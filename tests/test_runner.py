#!/usr/bin/env python3
"""
Comprehensive test runner for simple-sqlalchemy

This script runs all tests with proper configuration and reporting.
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path


def check_dependencies():
    """Check if required test dependencies are available"""
    missing_deps = []
    
    try:
        import pytest
    except ImportError:
        missing_deps.append("pytest")
    
    try:
        import pytest_cov
    except ImportError:
        missing_deps.append("pytest-cov")
    
    try:
        import psutil
    except ImportError:
        missing_deps.append("psutil")
    
    # Check optional dependencies
    optional_deps = {}
    
    try:
        import string_schema
        optional_deps["string-schema"] = True
    except ImportError:
        optional_deps["string-schema"] = False
    
    if missing_deps:
        print(f"❌ Missing required dependencies: {', '.join(missing_deps)}")
        print("Install with: pip install -r tests/requirements.txt")
        return False, optional_deps
    
    print("✅ All required dependencies available")
    
    for dep, available in optional_deps.items():
        status = "✅" if available else "⚠️"
        print(f"{status} Optional dependency {dep}: {'available' if available else 'not available'}")
    
    return True, optional_deps


def run_tests(test_type="all", coverage=True, verbose=False, parallel=False, string_schema_only=False):
    """Run tests with specified configuration"""
    
    # Check dependencies
    deps_ok, optional_deps = check_dependencies()
    if not deps_ok:
        return False
    
    # Build pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add coverage if requested
    if coverage:
        cmd.extend([
            "--cov=simple_sqlalchemy",
            "--cov-report=html",
            "--cov-report=xml",
            "--cov-report=term-missing"
        ])
    
    # Add verbosity
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    # Add parallel execution
    if parallel:
        cmd.extend(["-n", "auto"])
    
    # Select test files based on type
    test_dir = Path(__file__).parent
    
    if string_schema_only:
        if not optional_deps.get("string-schema", False):
            print("❌ string-schema not available, cannot run string-schema tests")
            return False
        cmd.extend([
            str(test_dir / "test_string_schema.py"),
            str(test_dir / "test_string_schema_advanced.py")
        ])
    elif test_type == "core":
        cmd.extend([
            str(test_dir / "test_base.py"),
            str(test_dir / "test_client.py"),
            str(test_dir / "test_crud.py"),
            str(test_dir / "test_session.py")
        ])
    elif test_type == "helpers":
        cmd.extend([
            str(test_dir / "test_helpers.py")
        ])
    elif test_type == "integration":
        cmd.extend([
            str(test_dir / "test_integration.py")
        ])
    elif test_type == "string_schema":
        if not optional_deps.get("string-schema", False):
            print("⚠️ string-schema not available, skipping string-schema tests")
            return True
        cmd.extend([
            str(test_dir / "test_string_schema.py"),
            str(test_dir / "test_string_schema_advanced.py")
        ])
    elif test_type == "all":
        cmd.append(str(test_dir))
    else:
        print(f"❌ Unknown test type: {test_type}")
        return False
    
    # Add markers for string-schema tests
    if not optional_deps.get("string-schema", False) and test_type == "all":
        cmd.extend(["-m", "not string_schema"])
    
    print(f"🚀 Running tests: {' '.join(cmd)}")
    print("=" * 60)
    
    # Run tests
    try:
        result = subprocess.run(cmd, cwd=test_dir.parent)
        return result.returncode == 0
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False


def run_performance_tests():
    """Run performance-specific tests"""
    print("🏃 Running performance tests...")
    
    cmd = [
        "python", "-m", "pytest",
        "-v",
        "-k", "performance",
        str(Path(__file__).parent)
    ]
    
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running performance tests: {e}")
        return False


def run_memory_tests():
    """Run memory usage tests"""
    print("🧠 Running memory tests...")
    
    cmd = [
        "python", "-m", "pytest",
        "-v",
        "-k", "memory",
        str(Path(__file__).parent)
    ]
    
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running memory tests: {e}")
        return False


def generate_test_report():
    """Generate a comprehensive test report"""
    print("📊 Generating test report...")
    
    # Run tests with detailed output
    cmd = [
        "python", "-m", "pytest",
        "--cov=simple_sqlalchemy",
        "--cov-report=html:htmlcov",
        "--cov-report=xml:coverage.xml",
        "--cov-report=term-missing",
        "--junit-xml=test-results.xml",
        "-v",
        str(Path(__file__).parent)
    ]
    
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
        
        if result.returncode == 0:
            print("✅ Test report generated successfully")
            print("📁 HTML coverage report: htmlcov/index.html")
            print("📁 XML coverage report: coverage.xml")
            print("📁 JUnit XML report: test-results.xml")
        else:
            print("❌ Test report generation failed")
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error generating test report: {e}")
        return False


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="Simple-SQLAlchemy Test Runner")
    
    parser.add_argument(
        "--type", 
        choices=["all", "core", "helpers", "integration", "string_schema"],
        default="all",
        help="Type of tests to run"
    )
    
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Disable coverage reporting"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--parallel", "-p",
        action="store_true",
        help="Run tests in parallel"
    )
    
    parser.add_argument(
        "--performance",
        action="store_true",
        help="Run performance tests only"
    )
    
    parser.add_argument(
        "--memory",
        action="store_true",
        help="Run memory tests only"
    )
    
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate comprehensive test report"
    )
    
    parser.add_argument(
        "--string-schema-only",
        action="store_true",
        help="Run only string-schema tests"
    )
    
    args = parser.parse_args()
    
    print("🧪 Simple-SQLAlchemy Test Runner")
    print("=" * 40)
    
    success = True
    
    if args.performance:
        success = run_performance_tests()
    elif args.memory:
        success = run_memory_tests()
    elif args.report:
        success = generate_test_report()
    else:
        success = run_tests(
            test_type=args.type,
            coverage=not args.no_coverage,
            verbose=args.verbose,
            parallel=args.parallel,
            string_schema_only=args.string_schema_only
        )
    
    if success:
        print("\n✅ All tests completed successfully!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
