"""
Test suite for log parser module.

Tests parsing functionality, error handling, and edge cases.
"""

import pytest
import tempfile
import os
from datetime import datetime
from unittest.mock import patch, mock_open

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from log_parser import LogParser
from models import LogEntry, HttpMethod, ParseError


class TestLogParser:
    """Test cases for LogParser class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = LogParser()
    
    def test_parse_clf_format(self):
        """Test parsing Common Log Format."""
        line = '127.0.0.1 - - [10/Oct/2023:13:55:36 +0000] "GET /test HTTP/1.1" 200 1234'
        
        entry = self.parser.parse_line(line)
        
        assert entry.ip_address == '127.0.0.1'
        assert entry.method == HttpMethod.GET
        assert entry.path == '/test'
        assert entry.status_code == 200
        assert entry.response_size == 1234
        assert entry.referrer is None
        assert entry.user_agent is None
    
    def test_parse_combined_format(self):
        """Test parsing Combined Log Format."""
        line = ('127.0.0.1 - - [10/Oct/2023:13:55:36 +0000] "GET /test HTTP/1.1" 200 1234 '
                '"https://example.com" "Mozilla/5.0"')
        
        entry = self.parser.parse_line(line)
        
        assert entry.ip_address == '127.0.0.1'
        assert entry.method == HttpMethod.GET
        assert entry.path == '/test'
        assert entry.status_code == 200
        assert entry.response_size == 1234
        assert entry.referrer == 'https://example.com'
        assert entry.user_agent == 'Mozilla/5.0'
    
    def test_parse_extended_format(self):
        """Test parsing Extended Log Format with response time."""
        line = ('127.0.0.1 - - [10/Oct/2023:13:55:36 +0000] "GET /test HTTP/1.1" 200 1234 '
                '"https://example.com" "Mozilla/5.0" 150000')
        
        entry = self.parser.parse_line(line)
        
        assert entry.ip_address == '127.0.0.1'
        assert entry.response_time == 150.0  # Converted from microseconds
    
    def test_parse_zero_response_size(self):
        """Test parsing with zero response size (-)."""
        line = '127.0.0.1 - - [10/Oct/2023:13:55:36 +0000] "POST /login HTTP/1.1" 401 -'
        
        entry = self.parser.parse_line(line)
        
        assert entry.response_size == 0
    
    def test_parse_missing_referrer(self):
        """Test parsing with missing referrer (-)."""
        line = ('127.0.0.1 - - [10/Oct/2023:13:55:36 +0000] "GET /test HTTP/1.1" 200 1234 '
                '"-" "Mozilla/5.0"')
        
        entry = self.parser.parse_line(line)
        
        assert entry.referrer is None
    
    def test_parse_different_http_methods(self):
        """Test parsing different HTTP methods."""
        methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
        
        for method in methods:
            line = f'127.0.0.1 - - [10/Oct/2023:13:55:36 +0000] "{method} /test HTTP/1.1" 200 100'
            entry = self.parser.parse_line(line)
            assert entry.method == HttpMethod(method)
    
    def test_parse_invalid_format(self):
        """Test parsing invalid log format."""
        invalid_line = "This is not a valid log line"
        
        with pytest.raises(ParseError):
            self.parser.parse_line(invalid_line)
    
    def test_parse_invalid_timestamp(self):
        """Test parsing with invalid timestamp."""
        line = '127.0.0.1 - - [invalid-timestamp] "GET /test HTTP/1.1" 200 1234'
        
        with pytest.raises(ParseError):
            self.parser.parse_line(line)
    
    def test_parse_invalid_status_code(self):
        """Test parsing with invalid status code."""
        line = '127.0.0.1 - - [10/Oct/2023:13:55:36 +0000] "GET /test HTTP/1.1" abc 1234'
        
        with pytest.raises(ParseError):
            self.parser.parse_line(line)
    
    def test_parse_file_streaming(self):
        """Test streaming file parsing."""
        log_content = """127.0.0.1 - - [10/Oct/2023:13:55:36 +0000] "GET /test1 HTTP/1.1" 200 100
127.0.0.1 - - [10/Oct/2023:13:56:36 +0000] "GET /test2 HTTP/1.1" 404 200
127.0.0.1 - - [10/Oct/2023:13:57:36 +0000] "POST /test3 HTTP/1.1" 500 300"""

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write(log_content)
            f.flush()
            temp_file_name = f.name

        try:
            entries = list(self.parser.parse_file_streaming(temp_file_name))

            assert len(entries) == 3
            assert entries[0].path == '/test1'
            assert entries[1].path == '/test2'
            assert entries[2].path == '/test3'
        finally:
            os.unlink(temp_file_name)
    
    def test_parse_file_with_empty_lines(self):
        """Test parsing file with empty lines and comments."""
        log_content = """# This is a comment
127.0.0.1 - - [10/Oct/2023:13:55:36 +0000] "GET /test1 HTTP/1.1" 200 100

127.0.0.1 - - [10/Oct/2023:13:56:36 +0000] "GET /test2 HTTP/1.1" 404 200
# Another comment

127.0.0.1 - - [10/Oct/2023:13:57:36 +0000] "POST /test3 HTTP/1.1" 500 300"""

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write(log_content)
            f.flush()
            temp_file_name = f.name

        try:
            entries = list(self.parser.parse_file_streaming(temp_file_name))

            assert len(entries) == 3
            assert self.parser.parsed_count == 3
            assert self.parser.error_count == 0
        finally:
            os.unlink(temp_file_name)
    
    def test_parse_file_with_errors_non_strict(self):
        """Test parsing file with errors in non-strict mode."""
        log_content = """127.0.0.1 - - [10/Oct/2023:13:55:36 +0000] "GET /test1 HTTP/1.1" 200 100
This is an invalid line
127.0.0.1 - - [10/Oct/2023:13:57:36 +0000] "POST /test3 HTTP/1.1" 500 300
Another invalid line"""

        parser = LogParser(strict_mode=False)

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write(log_content)
            f.flush()
            temp_file_name = f.name

        try:
            entries = list(parser.parse_file_streaming(temp_file_name))

            assert len(entries) == 2  # Only valid entries
            assert parser.parsed_count == 2
            assert parser.error_count == 2
            assert len(parser.errors) == 2
        finally:
            os.unlink(temp_file_name)

    def test_parse_file_with_errors_strict(self):
        """Test parsing file with errors in strict mode."""
        log_content = """127.0.0.1 - - [10/Oct/2023:13:55:36 +0000] "GET /test1 HTTP/1.1" 200 100
This is an invalid line
127.0.0.1 - - [10/Oct/2023:13:57:36 +0000] "POST /test3 HTTP/1.1" 500 300"""

        parser = LogParser(strict_mode=True)

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write(log_content)
            f.flush()
            temp_file_name = f.name

        try:
            with pytest.raises(ParseError):
                list(parser.parse_file_streaming(temp_file_name))
        finally:
            os.unlink(temp_file_name)
    
    def test_parse_nonexistent_file(self):
        """Test parsing nonexistent file."""
        with pytest.raises(FileNotFoundError):
            self.parser.parse_file('/nonexistent/file.log')
    
    def test_parse_compressed_file(self):
        """Test parsing compressed (.gz) file."""
        log_content = """127.0.0.1 - - [10/Oct/2023:13:55:36 +0000] "GET /test1 HTTP/1.1" 200 100
127.0.0.1 - - [10/Oct/2023:13:56:36 +0000] "GET /test2 HTTP/1.1" 404 200"""

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write(log_content)
            f.flush()
            temp_file_name = f.name

        try:
            # Simulate gzip file by mocking
            with patch('gzip.open', mock_open(read_data=log_content)):
                entries = list(self.parser.parse_file_streaming(temp_file_name + '.gz'))
                assert len(entries) == 2
        finally:
            os.unlink(temp_file_name)

    def test_parsing_stats(self):
        """Test parsing statistics."""
        log_content = """127.0.0.1 - - [10/Oct/2023:13:55:36 +0000] "GET /test1 HTTP/1.1" 200 100
Invalid line
127.0.0.1 - - [10/Oct/2023:13:57:36 +0000] "POST /test3 HTTP/1.1" 500 300"""

        parser = LogParser(strict_mode=False)

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write(log_content)
            f.flush()
            temp_file_name = f.name

        try:
            list(parser.parse_file_streaming(temp_file_name))
            stats = parser.get_parsing_stats()

            assert stats['parsed_count'] == 2
            assert stats['error_count'] == 1
            assert stats['success_rate'] > 0.5
            assert len(stats['errors']) == 1
        finally:
            os.unlink(temp_file_name)
    
    def test_timestamp_parsing_variations(self):
        """Test various timestamp formats."""
        # Standard format with timezone
        line1 = '127.0.0.1 - - [10/Oct/2023:13:55:36 +0000] "GET /test HTTP/1.1" 200 100'
        entry1 = self.parser.parse_line(line1)
        assert isinstance(entry1.timestamp, datetime)
        assert entry1.timestamp.tzinfo is not None, "Timezone-aware timestamp should have tzinfo"

        # Format without timezone (fallback) - now supported per requirements
        line2 = '127.0.0.1 - - [10/Oct/2023:13:55:36] "GET /test HTTP/1.1" 200 100'
        entry2 = self.parser.parse_line(line2)
        assert isinstance(entry2.timestamp, datetime)
        # Note: This will be timezone-naive (tzinfo is None) as no timezone was provided
        assert entry2.timestamp.tzinfo is None, "Timezone-naive timestamp should not have tzinfo"

    @pytest.mark.parametrize("timezone_offset,expected_offset_hours", [
        ("+0000", 0),      # UTC
        ("-0500", -5),    # US Eastern (EST)
        ("-0800", -8),    # US Pacific (PST)
        ("+0100", 1),     # Central European (CET)
        ("+0530", 5.5),   # Indian Standard Time
        ("+1000", 10),    # Australian Eastern
        ("-1200", -12),   # Baker Island (extreme minimum)
        ("+1400", 14),    # Line Islands (extreme maximum)
    ])
    def test_parse_various_timezones(self, timezone_offset, expected_offset_hours):
        """Test parsing various valid timezone formats.

        This test verifies that the parser correctly handles:
        - Positive timezone offsets (UTC+)
        - Negative timezone offsets (UTC-)
        - Half-hour offsets (e.g., +0530 for IST)
        - Extreme valid offsets (-1200 to +1400)
        """
        line = f'127.0.0.1 - - [10/Oct/2023:13:55:36 {timezone_offset}] "GET /test HTTP/1.1" 200 100'
        entry = self.parser.parse_line(line)

        # Verify entry was parsed successfully
        assert entry is not None
        assert entry.ip_address == '127.0.0.1'
        assert entry.path == '/test'

        # Verify timestamp is timezone-aware
        assert entry.timestamp.tzinfo is not None

        # Verify the timezone offset is correct
        offset_seconds = entry.timestamp.utcoffset().total_seconds()
        expected_offset_seconds = expected_offset_hours * 3600
        assert offset_seconds == expected_offset_seconds, \
            f"Expected offset {expected_offset_hours}h ({expected_offset_seconds}s), got {offset_seconds}s"

    @pytest.mark.parametrize("invalid_timezone", [
        "+2500",  # Exceeds maximum valid offset (+1400)
        "-9999",  # Far beyond minimum valid offset (-1200)
        "+1500",  # Beyond valid range (max is +1400)
        "-1300",  # Beyond valid range (min is -1200)
    ])
    def test_parse_invalid_timezones(self, invalid_timezone):
        """Test that invalid timezone offsets are rejected.

        Valid timezone range is UTC-12:00 to UTC+14:00.
        Timezones outside this range should raise ParseError.
        """
        line = f'127.0.0.1 - - [10/Oct/2023:13:55:36 {invalid_timezone}] "GET /test HTTP/1.1" 200 100'

        with pytest.raises(ParseError) as exc_info:
            self.parser.parse_line(line)

        # Verify error message contains useful information
        error_message = str(exc_info.value)
        assert "timezone" in error_message.lower() or "offset" in error_message.lower(), \
            "Error message should mention timezone or offset"

    def test_parse_file_with_mixed_timezones(self):
        """Test parsing file with different timezone formats in same file.

        Real-world log files may contain entries from different sources
        or time periods with varying timezone formats.
        """
        log_content = """127.0.0.1 - - [10/Oct/2023:13:55:36 +0000] "GET /test1 HTTP/1.1" 200 100
127.0.0.1 - - [10/Oct/2023:13:56:36 -0500] "GET /test2 HTTP/1.1" 200 200
127.0.0.1 - - [10/Oct/2023:13:57:36 +0530] "GET /test3 HTTP/1.1" 200 300
127.0.0.1 - - [10/Oct/2023:13:58:36 -0800] "GET /test4 HTTP/1.1" 200 400"""

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write(log_content)
            f.flush()
            temp_file_name = f.name

        try:
            entries = list(self.parser.parse_file_streaming(temp_file_name))

            assert len(entries) == 4, "Should parse all 4 entries with different timezones"

            # Verify each entry has correct path and timezone
            assert entries[0].path == '/test1'
            assert entries[0].timestamp.utcoffset().total_seconds() == 0  # +0000

            assert entries[1].path == '/test2'
            assert entries[1].timestamp.utcoffset().total_seconds() == -5 * 3600  # -0500

            assert entries[2].path == '/test3'
            assert entries[2].timestamp.utcoffset().total_seconds() == 5.5 * 3600  # +0530

            assert entries[3].path == '/test4'
            assert entries[3].timestamp.utcoffset().total_seconds() == -8 * 3600  # -0800

            # Verify all are timezone-aware
            for entry in entries:
                assert entry.timestamp.tzinfo is not None, \
                    "All timestamps should be timezone-aware"
        finally:
            os.unlink(temp_file_name)


class TestLogParserEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_extremely_long_line(self):
        """Test parsing extremely long log line."""
        parser = LogParser()
        long_path = '/test' + 'x' * 10000
        line = f'127.0.0.1 - - [10/Oct/2023:13:55:36 +0000] "GET {long_path} HTTP/1.1" 200 100'
        
        entry = parser.parse_line(line)
        assert entry.path == long_path
    
    def test_special_characters_in_path(self):
        """Test parsing path with special characters."""
        parser = LogParser()
        special_path = '/test%20with%20spaces?param=value&other=123'
        line = f'127.0.0.1 - - [10/Oct/2023:13:55:36 +0000] "GET {special_path} HTTP/1.1" 200 100'
        
        entry = parser.parse_line(line)
        assert entry.path == special_path
    
    def test_unicode_in_user_agent(self):
        """Test parsing user agent with unicode characters."""
        parser = LogParser()
        unicode_ua = 'Mozilla/5.0 (测试) Unicode-Browser/1.0'
        line = f'127.0.0.1 - - [10/Oct/2023:13:55:36 +0000] "GET /test HTTP/1.1" 200 100 "-" "{unicode_ua}"'
        
        entry = parser.parse_line(line)
        assert entry.user_agent == unicode_ua
    
    def test_large_response_size(self):
        """Test parsing very large response size."""
        parser = LogParser()
        large_size = 999999999999
        line = f'127.0.0.1 - - [10/Oct/2023:13:55:36 +0000] "GET /test HTTP/1.1" 200 {large_size}'
        
        entry = parser.parse_line(line)
        assert entry.response_size == large_size
    
    @pytest.mark.parametrize("status_code", [100, 200, 301, 404, 500, 599])
    def test_various_status_codes(self, status_code):
        """Test parsing various HTTP status codes."""
        parser = LogParser()
        line = f'127.0.0.1 - - [10/Oct/2023:13:55:36 +0000] "GET /test HTTP/1.1" {status_code} 100'
        
        entry = parser.parse_line(line)
        assert entry.status_code == status_code
