#!/usr/bin/env python3
"""
Test runner for VectorService tests.

This script provides an easy way to run different types of tests:
- Unit tests (mocked externals)
- Integration tests (real DB, mocked APIs)
- Manual tests (real APIs - requires API keys)

Usage:
    python tests/test_runner.py [test_type] [options]

Examples:
    python tests/test_runner.py unit
    python tests/test_runner.py integration
    python tests/test_runner.py manual
    python tests/test_runner.py all
    python tests/test_runner.py unit --verbose
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class VectorTestRunner:
    """Test runner for VectorService tests."""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.project_root = self.test_dir.parent
    
    def check_dependencies(self):
        """Check if required test dependencies are installed."""
        required_packages = [
            "pytest",
            "pytest-asyncio", 
            "sqlalchemy",
            "aiosqlite"
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            print("❌ Missing required test dependencies:")
            for package in missing_packages:
                print(f"   • {package}")
            print("\nInstall with: pip install " + " ".join(missing_packages))
            return False
        
        return True
    
    def run_unit_tests(self, verbose=False):
        """Run unit tests with mocked external services."""
        print("🧪 Running VectorService Unit Tests")
        print("=" * 40)
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir / "test_vector_service.py"),
            "-v" if verbose else "-q",
            "--tb=short"
        ]
        
        if verbose:
            cmd.extend(["--capture=no"])
        
        return subprocess.run(cmd, cwd=self.project_root).returncode == 0
    
    def run_integration_tests(self, verbose=False):
        """Run integration tests with real database."""
        print("🔗 Running VectorService Integration Tests")
        print("=" * 40)
        
        cmd = [
            sys.executable, "-m", "pytest", 
            str(self.test_dir / "test_vector_integration.py"),
            "-v" if verbose else "-q",
            "--tb=short"
        ]
        
        if verbose:
            cmd.extend(["--capture=no"])
        
        return subprocess.run(cmd, cwd=self.project_root).returncode == 0
    
    def run_manual_tests(self):
        """Run manual tests with real APIs."""
        print("🌐 Running VectorService Manual Tests (Real APIs)")
        print("=" * 40)
        
        # Check for API keys
        required_env_vars = [
            "OPENAI_API_KEY",
            "PINECONE_API_KEY",
            "PINECONE_ENVIRONMENT"
        ]
        
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        
        if missing_vars:
            print("⚠️ Manual tests require API keys. Missing variables:")
            for var in missing_vars:
                print(f"   • {var}")
            print("\nSet these environment variables to run manual tests.")
            print("Manual tests will test against real OpenAI and Pinecone APIs.")
            return False
        
        # Run manual tests
        cmd = [sys.executable, str(self.test_dir / "test_vector_manual.py")]
        return subprocess.run(cmd, cwd=self.project_root).returncode == 0
    
    def run_all_tests(self, verbose=False):
        """Run all available tests."""
        print("🚀 Running All VectorService Tests")
        print("=" * 40)
        
        results = []
        
        # Unit tests
        print("\n" + "=" * 20 + " UNIT TESTS " + "=" * 20)
        unit_result = self.run_unit_tests(verbose)
        results.append(("Unit Tests", unit_result))
        
        # Integration tests
        print("\n" + "=" * 18 + " INTEGRATION TESTS " + "=" * 18) 
        integration_result = self.run_integration_tests(verbose)
        results.append(("Integration Tests", integration_result))
        
        # Manual tests (only if API keys available)
        if all(os.getenv(var) for var in ["OPENAI_API_KEY", "PINECONE_API_KEY", "PINECONE_ENVIRONMENT"]):
            print("\n" + "=" * 19 + " MANUAL TESTS " + "=" * 19)
            manual_result = self.run_manual_tests()
            results.append(("Manual Tests", manual_result))
        else:
            print("\n⚠️ Skipping manual tests - API keys not configured")
        
        # Print summary
        print("\n" + "=" * 50)
        print("📋 Test Summary:")
        
        passed = 0
        total = len(results)
        
        for test_type, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_type}: {status}")
            if result:
                passed += 1
        
        print(f"\n🎯 Overall: {passed}/{total} test suites passed")
        
        return passed == total
    
    def lint_code(self):
        """Run code linting on the vector service."""
        print("🔍 Running Code Linting")
        print("=" * 30)
        
        # Check if flake8 is available
        try:
            import flake8
        except ImportError:
            print("⚠️ flake8 not installed. Install with: pip install flake8")
            return True  # Don't fail if linting tool not available
        
        cmd = [
            sys.executable, "-m", "flake8",
            str(self.project_root / "src" / "db" / "services" / "vector_service.py"),
            "--max-line-length=120",
            "--ignore=E203,W503"  # Ignore some black-compatible warnings
        ]
        
        result = subprocess.run(cmd, cwd=self.project_root)
        return result.returncode == 0
    
    def create_test_requirements(self):
        """Create a requirements file for testing."""
        test_requirements = [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.20.0",
            "sqlalchemy[asyncio]>=2.0.0",
            "aiosqlite>=0.17.0",
            "flake8>=5.0.0",  # For linting
        ]
        
        requirements_file = self.test_dir / "requirements.txt"
        
        with open(requirements_file, "w") as f:
            for req in test_requirements:
                f.write(req + "\n")
        
        print(f"📝 Created test requirements file: {requirements_file}")
        print("Install with: pip install -r tests/requirements.txt")


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(
        description="Test runner for VectorService",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python tests/test_runner.py unit              # Run unit tests
    python tests/test_runner.py integration       # Run integration tests  
    python tests/test_runner.py manual            # Run manual tests (requires API keys)
    python tests/test_runner.py all               # Run all available tests
    python tests/test_runner.py unit --verbose    # Run unit tests with verbose output
    python tests/test_runner.py lint              # Run code linting
    python tests/test_runner.py requirements      # Create test requirements file
        """
    )
    
    parser.add_argument(
        "test_type",
        choices=["unit", "integration", "manual", "all", "lint", "requirements"],
        help="Type of tests to run"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Run tests with verbose output"
    )
    
    args = parser.parse_args()
    
    runner = VectorTestRunner()
    
    # Handle special commands
    if args.test_type == "requirements":
        runner.create_test_requirements()
        return
    
    if args.test_type == "lint":
        success = runner.lint_code()
        sys.exit(0 if success else 1)
    
    # Check dependencies for regular tests
    if not runner.check_dependencies():
        print("\n💡 Tip: Create test requirements file with:")
        print("    python tests/test_runner.py requirements")
        sys.exit(1)
    
    # Run tests
    if args.test_type == "unit":
        success = runner.run_unit_tests(args.verbose)
    elif args.test_type == "integration":
        success = runner.run_integration_tests(args.verbose)
    elif args.test_type == "manual":
        success = runner.run_manual_tests()
    elif args.test_type == "all":
        success = runner.run_all_tests(args.verbose)
    else:
        print(f"Unknown test type: {args.test_type}")
        sys.exit(1)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 