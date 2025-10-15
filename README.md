# Log Analysis System

A robust log analysis system for processing web server logs and generating insights. Built for coding interview practice with progressive challenges.

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
├── javascript/          # API and additional processing
│   ├── server.js        # Express API server
│   ├── processor.js     # Data transformation
│   └── validator.js     # Request validation
├── tests/               # Comprehensive test suites
├── data/               # Sample log files
└── docs/               # Additional documentation
```

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 14+
- npm or yarn

### Setup
```bash
# Verify installation (all tests should pass)
python test_system.py

# Try the example
python example.py

# Install Python testing dependencies (optional)
pip install pytest pytest-cov

# Install JavaScript dependencies  
cd javascript && npm install

# Run tests (if pytest installed)
python -m pytest tests/python/
npm test --prefix javascript/
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
```

**JavaScript API:**
```bash
node javascript/server.js
# POST /analyze with log file
# GET /reports/{report_id}
```

## Core Functionality (20-minute overview)

### 1. Log Parsing (`python/log_parser.py`)
- Parses Common Log Format and Extended Log Format
- Handles malformed entries gracefully
- Memory-efficient streaming for large files

### 2. Analytics Engine (`python/analytics.py`)
- Traffic pattern analysis
- Error rate calculations
- Performance metrics (response times, payload sizes)
- Top endpoints, IPs, and user agents

### 3. API Layer (`javascript/server.js`)
- RESTful endpoints for log submission
- Async processing with job queues
- Report generation and retrieval

### 4. Data Models (`python/models.py`)
- Structured log entry representation
- Validation and type safety
- Serialization for API communication

## Sample Log Format

```
127.0.0.1 - - [10/Oct/2023:13:55:36 +0000] "GET /api/users HTTP/1.1" 200 1234 "https://example.com" "Mozilla/5.0..."
192.168.1.100 - - [10/Oct/2023:13:56:15 +0000] "POST /login HTTP/1.1" 401 0 "-" "curl/7.68.0"
```

## Testing Strategy

- **Unit Tests**: Individual function validation
- **Integration Tests**: End-to-end processing workflows
- **Performance Tests**: Large file handling and memory usage
- **Edge Case Tests**: Malformed data, empty files, concurrent access

## Programming Challenges

Ready to test your skills? See `CHALLENGES.md` for progressive coding challenges that build on this codebase, from basic bug fixes to advanced optimizations.

---

*This project is designed for interview preparation and skill demonstration. Focus on clean code, comprehensive testing, and real-world error handling.*
