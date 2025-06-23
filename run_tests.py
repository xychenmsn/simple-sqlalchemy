#!/usr/bin/env python3
"""
Test runner script for simple-sqlalchemy

This script provides convenient ways to run tests with different configurations.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and return the result"""
    if description:
        print(f"\n{description}")
        print("=" * len(description))
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Run simple-sqlalchemy tests")
    parser.add_argument(
        "--coverage", 
        action="store_true", 
        help="Run tests with coverage reporting"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Run tests in verbose mode"
    )
    parser.add_argument(
        "--parallel", "-n", 
        type=int, 
        help="Run tests in parallel with N workers"
    )
    parser.add_argument(
        "--fast", 
        action="store_true", 
        help="Run tests without slow tests"
    )
    parser.add_argument(
        "--integration", 
        action="store_true", 
        help="Run only integration tests"
    )
    parser.add_argument(
        "--unit", 
        action="store_true", 
        help="Run only unit tests (exclude integration)"
    )
    parser.add_argument(
        "test_path", 
        nargs="?", 
        help="Specific test file or directory to run"
    )
    
    args = parser.parse_args()
    
    # Build pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test path
    if args.test_path:
        cmd.append(args.test_path)
    else:
        cmd.append("tests/")
    
    # Add coverage
    if args.coverage:
        cmd.extend([
            "--cov=simple_sqlalchemy",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-report=xml:coverage.xml"
        ])
    
    # Add verbosity
    if args.verbose:
        cmd.append("-v")
    
    # Add parallel execution
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])
    
    # Add test filtering
    if args.fast:
        cmd.extend(["-m", "not slow"])
    elif args.integration:
        cmd.extend(["-m", "integration"])
    elif args.unit:
        cmd.extend(["-m", "not integration"])
    
    # Run tests
    success = run_command(cmd, "Running Tests")
    
    if args.coverage and success:
        print("\nCoverage report generated:")
        print("- Terminal: shown above")
        print("- HTML: htmlcov/index.html")
        print("- XML: coverage.xml")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
