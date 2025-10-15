"""
Utility functions for log analysis system.

Provides helper functions for file operations, data formatting,
and common tasks across the application.
"""

import os
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Union
from datetime import datetime

from .models import LogEntry, AnalyticsReport


def format_bytes(bytes_value: int) -> str:
    """
    Format bytes into human-readable string.
    
    Args:
        bytes_value: Number of bytes
        
    Returns:
        Formatted string (e.g., "1.5 KB", "2.3 MB")
    """
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = float(bytes_value)
    unit_index = 0
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.1f} {units[unit_index]}"


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string (e.g., "1.5s", "2m 30s")
    """
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.0f}s"


def validate_ip_address(ip: str) -> bool:
    """
    Validate IP address format.
    
    Args:
        ip: IP address string
        
    Returns:
        True if valid IPv4 address
    """
    try:
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        
        for part in parts:
            num = int(part)
            if not 0 <= num <= 255:
                return False
        
        return True
    except (ValueError, AttributeError):
        return False


def save_report_as_json(report: AnalyticsReport, file_path: str) -> None:
    """
    Save analytics report as JSON file.
    
    Args:
        report: AnalyticsReport object
        file_path: Output file path
    """
    report_dict = report.to_dict()
    
    with open(file_path, 'w') as f:
        json.dump(report_dict, f, indent=2, default=str)


def save_logs_as_csv(log_entries: List[LogEntry], file_path: str) -> None:
    """
    Save log entries as CSV file.
    
    Args:
        log_entries: List of LogEntry objects
        file_path: Output file path
    """
    if not log_entries:
        return
    
    fieldnames = [
        'ip_address', 'timestamp', 'method', 'path', 'protocol',
        'status_code', 'response_size', 'referrer', 'user_agent', 'response_time'
    ]
    
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for entry in log_entries:
            row = {
                'ip_address': entry.ip_address,
                'timestamp': entry.timestamp.isoformat(),
                'method': entry.method.value,
                'path': entry.path,
                'protocol': entry.protocol,
                'status_code': entry.status_code,
                'response_size': entry.response_size,
                'referrer': entry.referrer or '',
                'user_agent': entry.user_agent or '',
                'response_time': entry.response_time or ''
            }
            writer.writerow(row)


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from JSON file.
    
    Args:
        config_path: Path to config file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return get_default_config()
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file: {e}")


def get_default_config() -> Dict[str, Any]:
    """Get default configuration settings."""
    return {
        'parsing': {
            'strict_mode': False,
            'max_file_size_mb': 500,
            'chunk_size': 8192
        },
        'analytics': {
            'top_n_default': 10,
            'slow_request_threshold': 1.0,
            'large_response_threshold': 1048576,  # 1MB
            'suspicious_ip_threshold': 1000
        },
        'output': {
            'date_format': '%Y-%m-%d %H:%M:%S',
            'decimal_places': 2
        }
    }


def ensure_directory_exists(directory_path: str) -> None:
    """
    Ensure directory exists, create if necessary.
    
    Args:
        directory_path: Path to directory
    """
    Path(directory_path).mkdir(parents=True, exist_ok=True)


def get_file_info(file_path: str) -> Dict[str, Any]:
    """
    Get information about a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        Dictionary with file information
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    stat = path.stat()
    
    return {
        'name': path.name,
        'size_bytes': stat.st_size,
        'size_formatted': format_bytes(stat.st_size),
        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
        'is_compressed': file_path.endswith('.gz'),
        'extension': path.suffix
    }


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file system operations.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove dangerous characters
    dangerous_chars = '<>:"/\\|?*'
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    
    # Truncate if too long
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:200-len(ext)] + ext
    
    return filename


def merge_reports(reports: List[AnalyticsReport]) -> AnalyticsReport:
    """
    Merge multiple analytics reports into one.
    
    Args:
        reports: List of AnalyticsReport objects
        
    Returns:
        Merged AnalyticsReport
    """
    if not reports:
        raise ValueError("No reports to merge")
    
    if len(reports) == 1:
        return reports[0]
    
    # Aggregate metrics
    total_requests = sum(r.total_requests for r in reports)
    unique_ips = len(set().union(*(r.top_ips.keys() for r in reports)))
    
    # Calculate weighted error rate
    total_errors = sum(r.total_requests * (r.error_rate / 100) for r in reports)
    error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
    
    # Calculate weighted average response size
    total_size = sum(r.total_requests * r.avg_response_size for r in reports)
    avg_response_size = (total_size / total_requests) if total_requests > 0 else 0
    
    # Merge top endpoints
    all_endpoints = {}
    for report in reports:
        for endpoint, count in report.top_endpoints.items():
            all_endpoints[endpoint] = all_endpoints.get(endpoint, 0) + count
    
    top_endpoints = dict(sorted(all_endpoints.items(), 
                               key=lambda x: x[1], reverse=True)[:10])
    
    # Merge top IPs
    all_ips = {}
    for report in reports:
        for ip, count in report.top_ips.items():
            all_ips[ip] = all_ips.get(ip, 0) + count
    
    top_ips = dict(sorted(all_ips.items(), 
                         key=lambda x: x[1], reverse=True)[:10])
    
    # Merge status codes
    all_status_codes = {}
    for report in reports:
        for code, count in report.status_code_distribution.items():
            all_status_codes[code] = all_status_codes.get(code, 0) + count
    
    # Merge hourly traffic
    all_hourly = {}
    for report in reports:
        for hour, count in report.hourly_traffic.items():
            all_hourly[hour] = all_hourly.get(hour, 0) + count
    
    # Merge error logs
    all_errors = []
    for report in reports:
        all_errors.extend(report.error_log)
    
    return AnalyticsReport(
        total_requests=total_requests,
        unique_ips=unique_ips,
        error_rate=error_rate,
        avg_response_size=avg_response_size,
        top_endpoints=top_endpoints,
        top_ips=top_ips,
        status_code_distribution=all_status_codes,
        hourly_traffic=all_hourly,
        error_log=all_errors
    )


class ProgressTracker:
    """Simple progress tracking for long-running operations."""
    
    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = datetime.now()
    
    def update(self, increment: int = 1) -> None:
        """Update progress counter."""
        self.current += increment
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current progress information."""
        elapsed = datetime.now() - self.start_time
        percent = (self.current / self.total * 100) if self.total > 0 else 0
        
        return {
            'current': self.current,
            'total': self.total,
            'percent': round(percent, 1),
            'elapsed_seconds': elapsed.total_seconds(),
            'description': self.description
        }
    
    def __str__(self) -> str:
        """String representation of progress."""
        progress_info = self.get_progress()
        return f"{self.description}: {progress_info['current']}/{progress_info['total']} ({progress_info['percent']}%)"
