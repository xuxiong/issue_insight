#!/usr/bin/env python3
"""
Setup script for GitHub Project Activity Analyzer.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="issue-analyzer",
    version="1.0.0",
    author="Development Team",
    author_email="dev@example.com",
    description="A command-line tool for analyzing GitHub repository issues and activity",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/issue-finder",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "issue-analyzer=cli.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)