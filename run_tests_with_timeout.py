#!/usr/bin/env python3
"""
测试执行脚本 - 带超时控制的测试运行器

功能特性：
- 找到所有测试文件（tests/**/*.py，排除 __init__.py 和 conftest.py）
- 为每个测试文件单独执行 uv run pytest --timeout=30
- 捕获每个测试文件的执行结果
- 记录执行时间和详细输出
- 使用 rich 库提供美观的终端输出
"""

import glob
import subprocess
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

    def set_result(self, result: TestResult, execution_time: float = 0.0,
                   stdout: str = "", stderr: str = ""):
        """设置测试结果"""
        self.result = result
        self.execution_time = execution_time
        self.stdout = stdout
        self.stderr = stderr


class TestRunner:
    """测试执行器"""

    def __init__(self):
        self.console = Console()
        self.timeout_seconds = 30
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
                timeout=self.timeout_seconds  # 严格限制在30秒内
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

            table.add_row(
                str(result.file_path),
                f"[{status_color}]{result.result.value}[/{status_color}]",
                f"{result.execution_time:.2f}s"
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


def main():
    """主函数"""
    runner = TestRunner()
    runner.run_all_tests()


if __name__ == "__main__":
    main()
