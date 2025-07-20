#!/usr/bin/env python3
"""
Comprehensive test runner for simple-sqlalchemy with string-schema integration

This script runs all tests and provides a comprehensive report of the
string-schema integration functionality.
"""

import sys
import os
import subprocess
import time
from pathlib import Path


def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def print_section(title):
    """Print a formatted section header"""
    print(f"\n🔍 {title}")
    print("-" * 40)


def check_environment():
    """Check the test environment"""
    print_section("Environment Check")
    
    # Check Python version
    python_version = sys.version_info
    print(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    else:
        print("✅ Python version OK")
    
    # Check required packages
    required_packages = [
        ("sqlalchemy", "SQLAlchemy"),
        ("pytest", "pytest"),
        ("pytest_cov", "pytest-cov")
    ]
    
    optional_packages = [
        ("string_schema", "string-schema"),
        ("psutil", "psutil")
    ]
    
    missing_required = []
    missing_optional = []
    
    for package, name in required_packages:
        try:
            __import__(package)
            print(f"✅ {name} available")
        except ImportError:
            print(f"❌ {name} missing")
            missing_required.append(name)
    
    for package, name in optional_packages:
        try:
            __import__(package)
            print(f"✅ {name} available")
        except ImportError:
            print(f"⚠️ {name} missing (optional)")
            missing_optional.append(name)
    
    if missing_required:
        print(f"\n❌ Missing required packages: {', '.join(missing_required)}")
        print("Install with: pip install -r tests/requirements.txt")
        return False
    
    if missing_optional:
        print(f"\n⚠️ Missing optional packages: {', '.join(missing_optional)}")
        print("Some tests will be skipped")
    
    return True


def run_test_suite(test_name, test_args, description):
    """Run a specific test suite"""
    print_section(f"{test_name}: {description}")
    
    cmd = ["python", "-m", "pytest"] + test_args
    print(f"Running: {' '.join(cmd)}")
    
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True
        )
        end_time = time.time()
        
        duration = end_time - start_time
        
        if result.returncode == 0:
            print(f"✅ {test_name} passed ({duration:.2f}s)")
            return True, duration
        else:
            print(f"❌ {test_name} failed ({duration:.2f}s)")
            print("STDOUT:", result.stdout[-500:] if result.stdout else "None")
            print("STDERR:", result.stderr[-500:] if result.stderr else "None")
            return False, duration
            
    except Exception as e:
        print(f"❌ {test_name} error: {e}")
        return False, 0


def run_all_tests():
    """Run all test suites"""
    print_header("Simple-SQLAlchemy Test Suite")
    
    # Check environment
    if not check_environment():
        return False
    
    # Test suites to run
    test_suites = [
        (
            "Core Tests",
            ["-v", "tests/test_base.py", "tests/test_client.py", "tests/test_crud.py", "tests/test_session.py"],
            "Core functionality tests"
        ),
        (
            "Helper Tests", 
            ["-v", "tests/test_helpers.py"],
            "Helper classes and utilities"
        ),
        (
            "Integration Tests",
            ["-v", "tests/test_integration.py"],
            "Integration and end-to-end tests"
        ),
        (
            "String Schema Tests",
            ["-v", "tests/test_string_schema.py"],
            "String-schema integration tests"
        ),
        (
            "String Schema Advanced Tests",
            ["-v", "tests/test_string_schema_advanced.py"],
            "Advanced string-schema features and edge cases"
        ),
        (
            "News Integration Tests",
            ["-v", "tests/test_news_integration.py"],
            "News project integration patterns"
        )
    ]
    
    # Run each test suite
    results = []
    total_time = 0
    
    for test_name, test_args, description in test_suites:
        success, duration = run_test_suite(test_name, test_args, description)
        results.append((test_name, success, duration))
        total_time += duration
    
    # Generate summary report
    print_header("Test Results Summary")
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    print(f"Total test suites: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Total time: {total_time:.2f}s")
    
    print("\nDetailed Results:")
    for test_name, success, duration in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} {test_name} ({duration:.2f}s)")
    
    # Generate coverage report if all tests passed
    if passed == total:
        print_section("Generating Coverage Report")
        coverage_cmd = [
            "python", "-m", "pytest",
            "--cov=simple_sqlalchemy",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "tests/"
        ]
        
        try:
            result = subprocess.run(
                coverage_cmd,
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Coverage report generated")
                print("📁 HTML report: htmlcov/index.html")
                
                # Extract coverage percentage
                output_lines = result.stdout.split('\n')
                for line in output_lines:
                    if 'TOTAL' in line and '%' in line:
                        print(f"📊 {line.strip()}")
                        break
            else:
                print("❌ Coverage report generation failed")
                
        except Exception as e:
            print(f"❌ Coverage report error: {e}")
    
    return passed == total


def run_performance_benchmark():
    """Run performance benchmarks"""
    print_header("Performance Benchmarks")
    
    try:
        import string_schema
        
        print_section("String Schema Performance Test")
        
        # Run performance-specific tests
        perf_cmd = [
            "python", "-m", "pytest",
            "-v", "-k", "performance",
            "tests/"
        ]
        
        result = subprocess.run(
            perf_cmd,
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Performance tests passed")
            print("Performance results in test output above")
        else:
            print("❌ Performance tests failed")
            print(result.stdout[-1000:] if result.stdout else "No output")
            
    except ImportError:
        print("⚠️ string-schema not available, skipping performance tests")


def main():
    """Main function"""
    print("🧪 Simple-SQLAlchemy Comprehensive Test Runner")
    
    # Run all tests
    success = run_all_tests()
    
    if success:
        print_header("🎉 All Tests Passed!")
        
        # Run performance benchmarks
        run_performance_benchmark()
        
        print("\n✅ Test suite completed successfully!")
        print("\n📋 Next Steps:")
        print("  1. Review coverage report: htmlcov/index.html")
        print("  2. Check performance results above")
        print("  3. Ready for production use!")
        
        return 0
    else:
        print_header("❌ Some Tests Failed")
        print("\n🔧 Troubleshooting:")
        print("  1. Check error messages above")
        print("  2. Ensure all dependencies are installed")
        print("  3. Run individual test files for more details")
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
