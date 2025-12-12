"""
Complete System Test Suite
Integrates backend and frontend tests, runs them in sequence
"""
import sys
import subprocess
from pathlib import Path

def run_backend_tests():
    """Run backend tests"""
    print("=" * 60)
    print("Step 1: Running Backend Tests")
    print("=" * 60)
    print()
    
    backend_test = Path(__file__).parent / "test_backend.py"
    if not backend_test.exists():
        print("❌ test_backend.py not found")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, str(backend_test)],
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print("\n✅ Backend tests passed!")
            return True
        else:
            print("\n❌ Backend tests failed!")
            print("\nStopping here. Please fix backend issues before testing frontend.")
            return False
    except Exception as e:
        print(f"❌ Failed to run backend tests: {e}")
        return False

def run_frontend_tests():
    """Run frontend tests"""
    print("\n" + "=" * 60)
    print("Step 2: Running Frontend Tests")
    print("=" * 60)
    print()
    
    frontend_test = Path(__file__).parent / "test_frontend.py"
    if not frontend_test.exists():
        print("❌ test_frontend.py not found")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, str(frontend_test)],
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print("\n✅ Frontend tests passed!")
            return True
        else:
            print("\n❌ Frontend tests failed!")
            return False
    except Exception as e:
        print(f"❌ Failed to run frontend tests: {e}")
        return False

def main():
    """Run complete system tests"""
    print("=" * 60)
    print("Complete System Test Suite")
    print("=" * 60)
    print()
    print("This will test both backend and frontend in sequence.")
    print("Backend tests must pass before frontend tests run.")
    print()
    
    # Step 1: Backend tests
    backend_passed = run_backend_tests()
    
    if not backend_passed:
        print("\n" + "=" * 60)
        print("System Test Failed - Backend Issues")
        print("=" * 60)
        print("\nPlease fix backend issues and run again.")
        print("Or run backend tests separately: scripts\\test_backend.bat")
        return 1
    
    # Step 2: Frontend tests (only if backend passed)
    frontend_passed = run_frontend_tests()
    
    # Summary
    print("\n" + "=" * 60)
    print("Complete System Test Summary")
    print("=" * 60)
    
    print(f"Backend Tests: {'✅ PASSED' if backend_passed else '❌ FAILED'}")
    print(f"Frontend Tests: {'✅ PASSED' if frontend_passed else '❌ FAILED'}")
    
    if backend_passed and frontend_passed:
        print("\n🎉 All system tests passed!")
        print("\nSystem is ready to use!")
        print("Next steps:")
        print("  1. Start backend: scripts\\start_backend_auto.bat")
        print("  2. Open frontend: frontend\\monitor.html")
        return 0
    else:
        print("\n⚠️  Some tests failed")
        if not backend_passed:
            print("  - Fix backend issues first")
        if not frontend_passed:
            print("  - Fix frontend issues")
        print("\nRun diagnose.bat for troubleshooting help.")
        return 1

if __name__ == "__main__":
    exit(main())

