"""
Log Analysis System

A robust system for parsing and analyzing web server logs.
"""

from log_parser import LogParser
from analytics import LogAnalytics, TrendAnalyzer
from models import LogEntry, AnalyticsReport, HttpMethod
from utils import format_bytes, format_duration, save_report_as_json

__version__ = "1.0.0"
__author__ = "Log Analysis Team"

__all__ = [
    'LogParser',
    'LogAnalytics', 
    'TrendAnalyzer',
    'LogEntry',
    'AnalyticsReport',
    'HttpMethod',
    'format_bytes',
    'format_duration',
    'save_report_as_json'
]
