"""
Data models for log analysis system.

Defines structured representations of log entries and related data.
"""

import re
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum


class HttpMethod(Enum):
    """HTTP request methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class LogLevel(Enum):
    """Log entry severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class LogEntry:
    """
    Represents a single log entry from web server logs.
    
    Supports Common Log Format and Extended Log Format parsing.
    """
    ip_address: str
    timestamp: datetime
    method: HttpMethod
    path: str
    protocol: str
    status_code: int
    response_size: int
    referrer: Optional[str] = None
    user_agent: Optional[str] = None
    response_time: Optional[float] = None
    
    def __post_init__(self):
        """Validate data after initialization."""
        self._validate()
    
    def _validate(self):
        """Validate log entry data."""
        if not self.ip_address:
            raise ValueError("IP address is required")
        
        if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', self.ip_address):
            raise ValueError(f"Invalid IP address format: {self.ip_address}")
        
        if self.status_code < 100 or self.status_code > 599:
            raise ValueError(f"Invalid HTTP status code: {self.status_code}")
        
        if self.response_size < 0:
            raise ValueError("Response size cannot be negative")
    
    @property
    def is_error(self) -> bool:
        """Check if this entry represents an error response."""
        return self.status_code >= 400
    
    @property
    def is_server_error(self) -> bool:
        """Check if this entry represents a server error."""
        return self.status_code >= 500
    
    @property
    def is_client_error(self) -> bool:
        """Check if this entry represents a client error."""
        return 400 <= self.status_code < 500
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert log entry to dictionary for serialization."""
        return {
            'ip_address': self.ip_address,
            'timestamp': self.timestamp.isoformat(),
            'method': self.method.value,
            'path': self.path,
            'protocol': self.protocol,
            'status_code': self.status_code,
            'response_size': self.response_size,
            'referrer': self.referrer,
            'user_agent': self.user_agent,
            'response_time': self.response_time,
            'is_error': self.is_error,
            'is_server_error': self.is_server_error,
            'is_client_error': self.is_client_error
        }


@dataclass
class AnalyticsReport:
    """
    Container for analytics results and metrics.
    """
    total_requests: int
    unique_ips: int
    error_rate: float
    avg_response_size: float
    top_endpoints: Dict[str, int]
    top_ips: Dict[str, int]
    status_code_distribution: Dict[int, int]
    hourly_traffic: Dict[str, int]
    error_log: list[LogEntry]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary for serialization."""
        return {
            'total_requests': self.total_requests,
            'unique_ips': self.unique_ips,
            'error_rate': round(self.error_rate, 4),
            'avg_response_size': round(self.avg_response_size, 2),
            'top_endpoints': self.top_endpoints,
            'top_ips': self.top_ips,
            'status_code_distribution': self.status_code_distribution,
            'hourly_traffic': self.hourly_traffic,
            'error_count': len(self.error_log)
        }


class ValidationError(Exception):
    """Raised when log entry validation fails."""
    pass


class ParseError(Exception):
    """Raised when log parsing fails."""
    pass
