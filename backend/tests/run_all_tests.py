"""
Run All Tests
Executes all test scripts in the tests folder
"""

import sys
import os
import subprocess

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def run_test(test_file, test_name):
    """Run a single test file"""
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}Running: {test_name}{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"{Colors.RED}Error running test: {e}{Colors.END}")
        return False

def main():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}AI Fitness Chat Assistant - Test Suite{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    
    tests = [
        (os.path.join(tests_dir, "test_auth.py"), "Authentication Tests"),
        (os.path.join(tests_dir, "test_complete_flow.py"), "Complete Flow Test"),
    ]
    
    results = []
    
    for test_file, test_name in tests:
        if os.path.exists(test_file):
            passed = run_test(test_file, test_name)
            results.append((test_name, passed))
        else:
            print(f"{Colors.YELLOW}Skipping {test_name}: File not found{Colors.END}")
            results.append((test_name, False))
    
    # Print final summary
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}Final Test Summary{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = f"{Colors.GREEN}✓ PASSED{Colors.END}" if passed else f"{Colors.RED}✗ FAILED{Colors.END}"
        print(f"{status} - {test_name}")
    
    print(f"\n{Colors.BOLD}Total: {passed_count}/{total_count} test suites passed{Colors.END}")
    
    if passed_count == total_count:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ All test suites passed!{Colors.END}")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ Some test suites failed{Colors.END}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
