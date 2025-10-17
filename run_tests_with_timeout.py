#!/usr/bin/env python3
"""
测试执行脚本 - 带超时控制的测试运行器

功能特性：
- 找到所有测试文件（tests/**/*.py，排除 __init__.py 和 conftest.py）
- 为每个测试文件单独执行 uv run pytest，支持命令行 --timeout 参数控制超时（默认10秒）
- 捕获每个测试文件的执行结果、失败比例和具体失败方法
- 记录执行时间和详细输出
- 使用 rich 库提供美观的终端输出
"""

import argparse
import glob
import re
import subprocess
import sys
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Tuple, Dict, Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns


class TestResult(Enum):
    """测试结果枚举"""
    PASSED = "✅ 通过"
    FAILED = "❌ 失败"
    TIMEOUT = "⏱️ 超时"
    ERROR = "🔥 错误"


class TestExecutionResult:
    """单个测试文件执行结果"""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.result: TestResult = TestResult.ERROR
        self.execution_time: float = 0.0
        self.stdout: str = ""
        self.stderr: str = ""
        self.error_message: str = ""
        self.total_tests: int = 0
        self.failed_tests: int = 0
        self.failure_rate: float = 0.0
        self.failed_methods: List[str] = []

    def set_result(self, result: TestResult, execution_time: float = 0.0,
                   stdout: str = "", stderr: str = ""):
        """设置测试结果"""
        self.result = result
        self.execution_time = execution_time
        self.stdout = stdout
        self.stderr = stderr

        # 解析pytest输出，提取失败信息
        self._parse_pytest_output(stdout, stderr)

    def _parse_pytest_output(self, stdout: str, stderr: str):
        """解析pytest输出，提取测试统计和失败方法信息"""
        # 合并stdout和stderr进行解析
        full_output = stdout + stderr

        # 匹配多种pytest统计信息格式
        self.total_tests = 0
        self.failed_tests = 0
        self.failed_methods = []

        # 首先尝试匹配总结行，如 "4 failed, 31 passed in 0.18s"
        summary_pattern = r'(\d+)\s*failed.*?(\d+)\s*passed.*?\d+\.\d+s'
        summary_match = re.search(summary_pattern, full_output, re.IGNORECASE)
        if summary_match:
            failed, passed = map(int, summary_match.groups())
            self.failed_tests = failed
            self.total_tests = failed + passed

        # 如果没找到总结行，尝试匹配 "collected X items"
        if self.total_tests == 0:
            collected_pattern = r'collected\s+(\d+)'
            collected_match = re.search(collected_pattern, full_output, re.IGNORECASE)
            if collected_match:
                self.total_tests = int(collected_match.group(1))

        # 如果还是没找到总测试数，尝试匹配只有失败的总结行，如 "11 failed in 0.20s"
        if self.total_tests == 0:
            failed_only_pattern = r'(\d+)\s*failed[^,]*in'
            failed_match = re.search(failed_only_pattern, full_output, re.IGNORECASE)
            if failed_match:
                self.failed_tests = int(failed_match.group(1))
                # 当匹配 "N failed in TIME" 且无passed时，意味着 N = 总测试数
                self.total_tests = self.failed_tests

        # 最后尝试处理特殊情况：找到失败测试数量但没找到总数
        if self.failed_tests > 0 and self.total_tests < self.failed_tests:
            self.total_tests = self.failed_tests

        # 计算失败比例
        if self.total_tests > 0:
            self.failure_rate = (self.failed_tests / self.total_tests * 100)
        else:
            # 如果没有收集到测试数量但有失败，根据测试结果设置
            if self.result == TestResult.PASSED:
                self.failure_rate = 0.0
                self.total_tests = 1  # 至少有1个测试
                self.failed_tests = 0
            elif self.result in [TestResult.FAILED, TestResult.TIMEOUT, TestResult.ERROR]:
                self.failure_rate = 100.0
                self.total_tests = 1  # 至少有1个测试
                self.failed_tests = 1

        # 匹配失败的测试方法
        # pytest输出格式如：
        # FAILED tests/unit/test_errors.py::TestAPIError::test_api_error_with_retry_info
        failed_method_pattern = r'^FAILED\s+(.*?)(?:\s|$)(?!.*\.\.\.)'
        failed_matches = re.findall(failed_method_pattern, full_output, re.MULTILINE)

        self.failed_methods = []
        for test_path in failed_matches:
            # 提取方法名，格式通常是 "tests/unit/test_errors.py::TestAPIError::test_api_error_with_retry_info"
            method_name = test_path.strip()
            if '::' in method_name:
                parts = method_name.split('::')
                if len(parts) >= 3:
                    # 保留类名和方法名: TestAPIError::test_api_error_with_retry_info
                    method_name = f"{parts[-2]}::{parts[-1]}"
                else:
                    # 只有文件和方法: test_file.py::function_name
                    method_name = parts[-1]
            else:
                # 如果没有::，可能是文件名
                method_name = Path(method_name).name

            # 清理方法名，避免包含多余的字符
            method_name = method_name.replace(' -', '').strip()
            if method_name and len(method_name) < 200 and method_name not in self.failed_methods:
                self.failed_methods.append(method_name)

        # 如果没有找到具体的FAILED行，尝试从输出中解析其他失败信息
        # 对于一些pytest输出格式，我们可能需要从其他地方提取方法信息
        if not self.failed_methods and self.failed_tests > 0:
            # 尝试匹配 = FAILURES = 部分的方法名
            failure_section_pattern = r'= FAILURES =\s*$'
            failure_start = re.search(failure_section_pattern, full_output, re.MULTILINE)
            if failure_start:
                # 从FAILURES部分开始查找方法名
                failure_part = full_output[failure_start.end():]
                method_pattern = r'_+(\w+)::_+(\w+)\s*\)?'
                method_matches = re.findall(method_pattern, failure_part)
                if method_matches:
                    for class_name, method_name in method_matches:
                        clean_method = f"{class_name}::{method_name}"
                        if clean_method not in self.failed_methods:
                            self.failed_methods.append(clean_method)

        # 如果没有找到具体的方法名，但有失败统计，添加通用的失败信息
        if not self.failed_methods and self.failed_tests > 0:
            self.failed_methods = [f"{self.failed_tests} 个测试失败"]


class TestRunner:
    """测试执行器"""

    def __init__(self, timeout_seconds: int = 10):
        self.console = Console()
        self.timeout_seconds = timeout_seconds
        self.test_pattern = "tests/**/*.py"
        self.exclude_patterns = ["**/test_*.py", "**/*_test.py"]

    def find_test_files(self) -> List[Path]:
        """找到所有测试文件"""
        # 使用 glob 找到所有测试文件
        test_files = glob.glob(self.test_pattern, recursive=True)

        # 转换为 Path 对象并去重
        test_paths = sorted(set(Path(f) for f in test_files))

        # 排除 __init__.py 和 conftest.py
        filtered_paths = []
        for path in test_paths:
            if path.name not in ["__init__.py", "conftest.py"]:
                filtered_paths.append(path)

        return filtered_paths

    def run_single_test(self, test_file: Path) -> TestExecutionResult:
        """运行单个测试文件"""
        result = TestExecutionResult(test_file)

        start_time = time.time()
        try:
            # 使用 subprocess.run 执行 uv run pytest，不能使用 --timeout 参数，避免冲突
            cmd = ["uv", "run", "pytest", str(test_file)]

            self.console.print(f"\n[blue]执行测试文件:[/blue] {test_file}")
            self.console.print(f"[dim]命令: {' '.join(cmd)} (超时: {self.timeout_seconds}s)[/dim]")

            # 执行命令，设置超时时间
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds  # 严格限制在默认10秒内（可配）
            )

            execution_time = time.time() - start_time

            # 分析返回码和输出
            if process.returncode == 0:
                result.set_result(TestResult.PASSED, execution_time,
                                process.stdout, process.stderr)
            else:
                # 检查 stderr 是否包含 pytest-timeout 相关的信息
                stderr_upper = process.stderr.upper()
                if ("TIMEOUT" in stderr_upper or "INTERRUPTED" in stderr_upper or
                    execution_time >= self.timeout_seconds):
                    result.set_result(TestResult.TIMEOUT, execution_time,
                                    process.stdout, process.stderr)
                else:
                    result.set_result(TestResult.FAILED, execution_time,
                                    process.stdout, process.stderr)

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            result.set_result(TestResult.TIMEOUT, execution_time)
            result.error_message = f"测试执行超过 {self.timeout_seconds} 秒"
        except FileNotFoundError:
            result.error_message = f"测试文件不存在: {test_file}"
        except Exception as e:
            result.error_message = f"执行测试时发生错误: {e}"

        return result

    def group_tests_by_directory(self, test_files: List[Path]) -> Dict[str, List[Path]]:
        """按目录分组测试文件"""
        groups = {
            "unit": [],
            "integration": [],
            "contract": []
        }

        for file_path in test_files:
            if "unit" in str(file_path):
                groups["unit"].append(file_path)
            elif "integration" in str(file_path):
                groups["integration"].append(file_path)
            elif "contract" in str(file_path):
                groups["contract"].append(file_path)

        return groups

    def display_results(self, results: List[TestExecutionResult]):
        """显示测试结果"""
        # 创建统计表
        table = Table(title="测试执行结果汇总")
        table.add_column("测试文件", style="cyan", no_wrap=True)
        table.add_column("状态", style="bold")
        table.add_column("执行时间", style="yellow", justify="right")
        table.add_column("失败比例", style="red", justify="right")

        # 统计数据
        total_tests = len(results)
        passed = sum(1 for r in results if r.result == TestResult.PASSED)
        failed = sum(1 for r in results if r.result == TestResult.FAILED)
        timeout = sum(1 for r in results if r.result == TestResult.TIMEOUT)
        success_rate = (passed / total_tests * 100) if total_tests > 0 else 0

        # 添加结果到表
        for result in results:
            status_color = {
                TestResult.PASSED: "green",
                TestResult.FAILED: "red",
                TestResult.TIMEOUT: "orange1",
                TestResult.ERROR: "red"
            }.get(result.result, "white")

            # 显示失败比例
            failure_rate_display = "N/A"
            if result.total_tests > 0:
                failure_rate_display = f"{result.failure_rate:.1f}%"
            elif result.result in [TestResult.FAILED, TestResult.TIMEOUT, TestResult.ERROR]:
                failure_rate_display = "100.0%"

            table.add_row(
                str(result.file_path),
                f"[{status_color}]{result.result.value}[/{status_color}]",
                f"{result.execution_time:.2f}s",
                failure_rate_display
            )

        self.console.print(table)

        # 显示统计信息
        stats_text = f"""
总测试文件数: {total_tests}
✅ 通过: {passed}
❌ 失败: {failed}
⏱️  超时: {timeout}
📊 通过率: {success_rate:.1f}%
        """.strip()

        # 根据结果显示总体结论
        if passed == total_tests:
            conclusion = "🎉 所有测试通过！"
            conclusion_color = "green"
        elif timeout > 0:
            conclusion = f"⚠️  存在超时问题 ({timeout} 个文件超时)"
            conclusion_color = "orange1"
        else:
            conclusion = f"❌ 部分测试失败 ({failed} 个文件失败)"
            conclusion_color = "red"

        self.console.print(Panel.fit(
            f"[bold {conclusion_color}]{conclusion}[/bold {conclusion_color}]\n\n{stats_text}",
            title="总体结论"
        ))

    def display_failed_methods_details(self, results: List[TestExecutionResult]):
        """显示失败方法的详细信息"""
        failed_results = [r for r in results if r.failed_methods]

        if not failed_results:
            return

        self.console.print(f"\n\n[red]🔍 失败方法详情:[/red]")

        for result in failed_results:
            self.console.print(f"\n[bold cyan]{result.file_path}[/bold cyan] - 失败了 {result.failed_tests}/{result.total_tests} 个测试 ({result.failure_rate:.1f}%)")

            for method in result.failed_methods:
                self.console.print(f"  ❌ {method}")

    def run_all_tests(self):
        """运行所有测试"""
        self.console.print(Panel.fit(
            "[bold blue]🚀 开始测试执行[/bold blue]\n\n"
            f"📁 测试模式: {self.test_pattern}\n"
            f"⏱️  超时设置: {self.timeout_seconds} 秒\n"
            f"🕐 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            title="测试执行配置"
        ))

        # 找到所有测试文件
        test_files = self.find_test_files()

        if not test_files:
            self.console.print("[red]❌ 未找到任何测试文件[/red]")
            return

        # 按目录分组显示
        grouped_tests = self.group_tests_by_directory(test_files)
        self.console.print("\n[blue]📋 发现的测试文件:[/blue]")

        for group_name, files in grouped_tests.items():
            if files:
                self.console.print(f"\n[bold cyan]{group_name.upper()}[/bold cyan]:")
                for file_path in files:
                    self.console.print(f"  • {file_path}")

        # 逐个执行测试
        results = []
        self.console.print(f"\n[blue]⚡ 开始逐个执行测试 ({len(test_files)} 个文件)...[/blue]")

        for test_file in test_files:
            result = self.run_single_test(test_file)
            results.append(result)

            # 显示简单结果
            status_color = {
                TestResult.PASSED: "green",
                TestResult.FAILED: "red",
                TestResult.TIMEOUT: "orange1",
                TestResult.ERROR: "red"
            }.get(result.result, "white")

            self.console.print(f"  {result.result.value} {result.file_path.name} "
                             f"({result.execution_time:.2f}s)")

        # 显示详细结果
        self.console.print("\n")
        self.display_results(results)
        self.display_failed_methods_details(results)


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="测试执行脚本 - 带超时控制的测试运行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python run_tests_with_timeout.py                 # 使用默认超时10秒
  python run_tests_with_timeout.py --timeout 30    # 设置30秒超时
  python run_tests_with_timeout.py --timeout 5     # 设置5秒超时
        """.strip()
    )

    parser.add_argument(
        '--timeout',
        type=int,
        default=5,
        metavar='SECONDS',
        help='单个测试文件执行的超时时间（秒），默认5秒'
    )

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_arguments()
    runner = TestRunner(timeout_seconds=args.timeout)
    runner.run_all_tests()


if __name__ == "__main__":
    main()
