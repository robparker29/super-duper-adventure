#!/usr/bin/env python3
"""
Quick verification test for the Log Analysis System.

Runs basic functionality tests to ensure everything is working correctly.
"""

import sys
import traceback
from pathlib import Path

# Add the python directory to path
sys.path.append(str(Path(__file__).parent / 'python'))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...", end=" ")
    try:
        from python.log_parser import LogParser
        from python.analytics import LogAnalytics, TrendAnalyzer
        from python.models import LogEntry, AnalyticsReport, HttpMethod
        from python.utils import format_bytes, format_duration
        print("✓ PASS")
        return True
    except Exception as e:
        print(f"✗ FAIL: {e}")
        return False

def test_basic_parsing():
    """Test basic log parsing functionality."""
    print("Testing log parsing...", end=" ")
    try:
        from python.log_parser import LogParser
        
        parser = LogParser()
        
        # Test parsing a single line
        test_line = '127.0.0.1 - - [10/Oct/2023:13:55:36 +0000] "GET /test HTTP/1.1" 200 1234'
        entry = parser.parse_line(test_line)
        
        assert entry.ip_address == '127.0.0.1'
        assert entry.status_code == 200
        assert entry.response_size == 1234
        assert entry.path == '/test'
        
        print("✓ PASS")
        return True
    except Exception as e:
        print(f"✗ FAIL: {e}")
        return False

def test_sample_file():
    """Test parsing the sample log file."""
    print("Testing sample file...", end=" ")
    try:
        from python.log_parser import LogParser
        from python.analytics import LogAnalytics
        
        sample_file = Path("data/sample.log")
        if not sample_file.exists():
            print("✗ SKIP: Sample file not found")
            return True
        
        parser = LogParser()
        entries = parser.parse_file(str(sample_file))
        
        assert len(entries) > 0, "No entries parsed"
        
        analytics = LogAnalytics(entries)
        report = analytics.generate_report()
        
        assert report.total_requests > 0, "No requests in report"
        assert report.unique_ips > 0, "No unique IPs found"
        
        print(f"✓ PASS ({len(entries)} entries)")
        return True
    except Exception as e:
        print(f"✗ FAIL: {e}")
        return False

def test_analytics():
    """Test analytics functionality."""
    print("Testing analytics...", end=" ")
    try:
        from python.models import LogEntry, HttpMethod
        from python.analytics import LogAnalytics
        from datetime import datetime, timezone
        
        # Create test data
        entries = [
            LogEntry(
                ip_address="127.0.0.1",
                timestamp=datetime(2023, 10, 10, 13, 55, 36, tzinfo=timezone.utc),
                method=HttpMethod.GET,
                path="/test",
                protocol="HTTP/1.1",
                status_code=200,
                response_size=1234
            ),
            LogEntry(
                ip_address="192.168.1.100",
                timestamp=datetime(2023, 10, 10, 13, 56, 15, tzinfo=timezone.utc),
                method=HttpMethod.POST,
                path="/login",
                protocol="HTTP/1.1",
                status_code=401,
                response_size=0
            )
        ]
        
        analytics = LogAnalytics(entries)
        report = analytics.generate_report()
        
        assert report.total_requests == 2
        assert report.unique_ips == 2
        assert report.error_rate == 50.0  # 1 error out of 2 requests
        
        print("✓ PASS")
        return True
    except Exception as e:
        print(f"✗ FAIL: {e}")
        return False

def test_utils():
    """Test utility functions."""
    print("Testing utilities...", end=" ")
    try:
        from python.utils import format_bytes, format_duration, validate_ip_address
        
        # Test format_bytes
        assert format_bytes(1024) == "1.0 KB"
        assert format_bytes(1048576) == "1.0 MB"
        
        # Test format_duration
        assert format_duration(0.5) == "500ms"
        assert format_duration(1.5) == "1.5s"
        assert format_duration(65) == "1m 5s"
        
        # Test IP validation
        assert validate_ip_address("127.0.0.1") == True
        assert validate_ip_address("invalid.ip") == False
        
        print("✓ PASS")
        return True
    except Exception as e:
        print(f"✗ FAIL: {e}")
        return False

def test_javascript_dependencies():
    """Test that JavaScript dependencies can be checked."""
    print("Testing JS dependencies...", end=" ")
    try:
        import subprocess
        import os
        
        js_dir = Path("javascript")
        if not js_dir.exists():
            print("✗ SKIP: JavaScript directory not found")
            return True
        
        # Check if package.json exists
        if not (js_dir / "package.json").exists():
            print("✗ SKIP: package.json not found")
            return True
        
        # Try to check if npm is available
        try:
            result = subprocess.run(['npm', '--version'], 
                                  capture_output=True, text=True, cwd=js_dir)
            if result.returncode == 0:
                print(f"✓ PASS (npm {result.stdout.strip()})")
            else:
                print("✗ SKIP: npm not available")
        except FileNotFoundError:
            print("✗ SKIP: npm not found")
        
        return True
    except Exception as e:
        print(f"✗ FAIL: {e}")
        return False

def main():
    """Run all tests."""
    print("Log Analysis System - Quick Verification Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_basic_parsing,
        test_analytics,
        test_utils,
        test_sample_file,
        test_javascript_dependencies
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ UNEXPECTED ERROR: {e}")
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The system is ready to use.")
        print("\nNext steps:")
        print("1. Run: ./example.py")
        print("2. Try: ./analyze.py data/sample.log")
        print("3. Start API: cd javascript && npm install && npm start")
        return 0
    else:
        print("❌ Some tests failed. Please check the installation.")
        print("\nCommon issues:")
        print("- Make sure you're in the project root directory")
        print("- Check that all Python files are present")
        print("- Verify the sample log file exists: data/sample.log")
        return 1

if __name__ == '__main__':
    sys.exit(main())
