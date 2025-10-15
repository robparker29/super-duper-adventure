# Log Analysis System - Testing Ground

A Python-based log analysis system for processing web server logs and generating insights. Built as a testing ground for practicing coding challenges and Python development.

## Overview

This system processes Apache/Nginx-style web server logs to extract meaningful analytics like:
- Request patterns and traffic analysis
- Error rate monitoring
- Popular endpoints and user agents
- Performance metrics and anomaly detection

## Architecture

```
├── python/               # Core analysis engine
│   ├── log_parser.py    # Main parsing logic
│   ├── analytics.py     # Data analysis and metrics
│   ├── models.py        # Data structures and validation
│   └── utils.py         # Helper functions
├── tests/               # Comprehensive test suites
│   ├── test_log_parser.py
│   ├── test_analytics.py
│   └── test_system.py
├── data/               # Sample log files
├── analyze.py          # CLI analysis tool
└── example.py          # Usage examples
```

## Quick Start

### Prerequisites
- Python 3.8+
- pip (for optional testing dependencies)

### Setup
```bash
# Verify installation (all tests should pass)
python -X utf8 tests/test_system.py

# Try the example
python example.py

# Analyze sample data
python analyze.py data/sample.log

# Install Python testing dependencies (optional)
pip install -r requirements.txt

# Run comprehensive tests (if pytest installed)
python -m pytest tests/
```

### Basic Usage

**Python Analysis Engine:**
```python
from python.log_parser import LogParser
from python.analytics import LogAnalytics

parser = LogParser()
logs = parser.parse_file('data/sample.log')
analytics = LogAnalytics(logs)
report = analytics.generate_report()
print(f"Total requests: {report.total_requests}")
print(f"Error rate: {report.error_rate}%")
```

**Command-line Analysis:**
```bash
python analyze.py data/sample.log
python analyze.py data/sample.log --output report.json
```

## Core Functionality

### 1. Log Parsing (`python/log_parser.py`)
- Parses Common Log Format and Extended Log Format
- Handles malformed entries gracefully
- Memory-efficient streaming for large files
- Supports compressed .gz files

### 2. Analytics Engine (`python/analytics.py`)
- Traffic pattern analysis
- Error rate calculations
- Performance metrics (response times, payload sizes)
- Top endpoints, IPs, and user agents
- Trend analysis and anomaly detection

### 3. Data Models (`python/models.py`)
- Structured log entry representation
- Validation and type safety
- Clean data class design

### 4. Utilities (`python/utils.py`)
- File operations and export functions
- Data formatting helpers
- Configuration management
- Progress tracking for large operations

## Sample Log Format

```
127.0.0.1 - - [10/Oct/2023:13:55:36 +0000] "GET /api/users HTTP/1.1" 200 1234 "https://example.com" "Mozilla/5.0..."
192.168.1.100 - - [10/Oct/2023:13:56:15 +0000] "POST /login HTTP/1.1" 401 0 "-" "curl/7.68.0"
```

## Testing Strategy

This codebase focuses on comprehensive testing:
- **Unit Tests**: Individual function validation
- **Integration Tests**: End-to-end processing workflows
- **Edge Case Tests**: Malformed data, empty files, error conditions
- **System Tests**: Full verification of all components

Run all tests:
```bash
# Quick verification
python -X utf8 tests/test_system.py

# Comprehensive testing with pytest
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ --cov=python --cov-report=html
```

## Programming Challenges

Ready to test your skills? See `CHALLENGES.md` for progressive coding challenges that build on this codebase, from basic bug fixes to advanced optimizations.

## Project Purpose

This is a **testing ground** designed for:
- Interview preparation and practice
- Exploring Python log processing techniques
- Testing and debugging practice
- Code quality and refactoring exercises
- Learning analytics and data processing patterns

---

*Focus on clean code, comprehensive testing, and real-world error handling.*
