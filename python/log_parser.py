"""
Log parsing module for web server logs.

Handles Common Log Format (CLF) and Extended Log Format parsing
with robust error handling and memory-efficient processing.
"""

import re
import gzip
from datetime import datetime
from typing import Iterator, List, Optional, TextIO
from pathlib import Path

from models import LogEntry, HttpMethod, ParseError


class LogParser:
    """
    Parses web server log files in Common Log Format and Extended formats.
    
    Supports:
    - Common Log Format (CLF)
    - Combined Log Format (with referrer and user agent)
    - Compressed files (.gz)
    - Large file streaming
    - Graceful error handling for malformed entries
    """
    
    # Common Log Format pattern
    CLF_PATTERN = re.compile(
        r'^(\S+) \S+ \S+ \[([^\]]+)\] "(\S+) (\S+) (\S+)" (\d+) (\d+|-)$'
    )
    
    # Combined Log Format pattern (includes referrer and user agent)
    COMBINED_PATTERN = re.compile(
        r'^(\S+) \S+ \S+ \[([^\]]+)\] "(\S+) (\S+) (\S+)" (\d+) (\d+|-) "([^"]*)" "([^"]*)"$'
    )
    
    # Extended format with response time
    EXTENDED_PATTERN = re.compile(
        r'^(\S+) \S+ \S+ \[([^\]]+)\] "(\S+) (\S+) (\S+)" (\d+) (\d+|-) "([^"]*)" "([^"]*)" (\d+)$'
    )
    
    def __init__(self, strict_mode: bool = False):
        """
        Initialize parser.
        
        Args:
            strict_mode: If True, raise exceptions on parse errors.
                        If False, skip malformed lines and continue.
        """
        self.strict_mode = strict_mode
        self.parsed_count = 0
        self.error_count = 0
        self.errors: List[str] = []
    
    def parse_file(self, file_path: str) -> List[LogEntry]:
        """
        Parse entire log file into memory.
        
        Args:
            file_path: Path to log file
            
        Returns:
            List of parsed log entries
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ParseError: If strict_mode is True and parsing fails
        """
        entries = []
        for entry in self.parse_file_streaming(file_path):
            entries.append(entry)
        return entries
    
    def parse_file_streaming(self, file_path: str) -> Iterator[LogEntry]:
        """
        Parse log file as a generator for memory efficiency.
        
        Args:
            file_path: Path to log file
            
        Yields:
            LogEntry objects
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Log file not found: {file_path}")
        
        # Reset counters
        self.parsed_count = 0
        self.error_count = 0
        self.errors.clear()
        
        # Handle compressed files
        if file_path.endswith('.gz'):
            with gzip.open(file_path, 'rt') as file:
                yield from self._parse_stream(file)
        else:
            with open(file_path, 'r') as file:
                yield from self._parse_stream(file)
    
    def _parse_stream(self, file: TextIO) -> Iterator[LogEntry]:
        """Parse log entries from file stream."""
        for line_num, line in enumerate(file, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue  # Skip empty lines and comments
            
            try:
                entry = self.parse_line(line)
                if entry:
                    self.parsed_count += 1
                    yield entry
            except ParseError as e:
                self.error_count += 1
                error_msg = f"Line {line_num}: {str(e)}"
                self.errors.append(error_msg)
                
                if self.strict_mode:
                    raise ParseError(error_msg)
                # In non-strict mode, continue parsing
    
    def parse_line(self, line: str) -> Optional[LogEntry]:
        """
        Parse a single log line.
        
        Args:
            line: Raw log line string
            
        Returns:
            LogEntry object or None if parsing fails
            
        Raises:
            ParseError: If line cannot be parsed
        """
        # Try extended format first (most specific)
        match = self.EXTENDED_PATTERN.match(line)
        if match:
            return self._create_entry_from_match(match, include_response_time=True)
        
        # Try combined format
        match = self.COMBINED_PATTERN.match(line)
        if match:
            return self._create_entry_from_match(match)
        
        # Try basic CLF format
        match = self.CLF_PATTERN.match(line)
        if match:
            return self._create_entry_from_clf_match(match)
        
        raise ParseError(f"Unable to parse log line: {line[:100]}...")
    
    def _create_entry_from_match(self, match, include_response_time: bool = False) -> LogEntry:
        """Create LogEntry from regex match (combined/extended format)."""
        ip_address = match.group(1)
        timestamp_str = match.group(2)
        method_str = match.group(3)
        path = match.group(4)
        protocol = match.group(5)
        status_code = int(match.group(6))
        response_size = self._parse_size(match.group(7))
        referrer = self._parse_optional_field(match.group(8))
        user_agent = self._parse_optional_field(match.group(9))
        
        response_time = None
        if include_response_time and len(match.groups()) >= 10:
            response_time = float(match.group(10)) / 1000.0  # Convert microseconds to seconds
        
        timestamp = self._parse_timestamp(timestamp_str)
        method = HttpMethod(method_str)
        
        return LogEntry(
            ip_address=ip_address,
            timestamp=timestamp,
            method=method,
            path=path,
            protocol=protocol,
            status_code=status_code,
            response_size=response_size,
            referrer=referrer,
            user_agent=user_agent,
            response_time=response_time
        )
    
    def _create_entry_from_clf_match(self, match) -> LogEntry:
        """Create LogEntry from regex match (CLF format)."""
        ip_address = match.group(1)
        timestamp_str = match.group(2)
        method_str = match.group(3)
        path = match.group(4)
        protocol = match.group(5)
        status_code = int(match.group(6))
        response_size = self._parse_size(match.group(7))
        
        timestamp = self._parse_timestamp(timestamp_str)
        method = HttpMethod(method_str)
        
        return LogEntry(
            ip_address=ip_address,
            timestamp=timestamp,
            method=method,
            path=path,
            protocol=protocol,
            status_code=status_code,
            response_size=response_size
        )
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse Apache timestamp format."""
        try:
            # Format: 10/Oct/2023:13:55:36 +0000
            return datetime.strptime(timestamp_str, '%d/%b/%Y:%H:%M:%S %z')
        except ValueError:
            # Fallback without timezone
            try:
                return datetime.strptime(timestamp_str[:20], '%d/%b/%Y:%H:%M:%S')
            except ValueError:
                raise ParseError(f"Invalid timestamp format: {timestamp_str}")
    
    def _parse_size(self, size_str: str) -> int:
        """Parse response size, handling '-' for zero."""
        if size_str == '-':
            return 0
        try:
            return int(size_str)
        except ValueError:
            raise ParseError(f"Invalid response size: {size_str}")
    
    def _parse_optional_field(self, field: str) -> Optional[str]:
        """Parse optional fields like referrer and user agent."""
        if field == '-' or field == '':
            return None
        return field
    
    def get_parsing_stats(self) -> dict:
        """Get statistics about the last parsing operation."""
        return {
            'parsed_count': self.parsed_count,
            'error_count': self.error_count,
            'success_rate': (self.parsed_count / (self.parsed_count + self.error_count)) 
                           if (self.parsed_count + self.error_count) > 0 else 0,
            'errors': self.errors[:10]  # Return first 10 errors
        }
