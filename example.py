#!/usr/bin/env python3
"""
Example usage of the Log Analysis System.

Demonstrates basic usage patterns and API calls.
"""

import sys
from pathlib import Path

# Add the current directory to path so we can import from python/
sys.path.insert(0, str(Path(__file__).parent))

from log_parser import LogParser
from analytics import LogAnalytics, TrendAnalyzer
from utils import format_bytes, save_report_as_json


def main():
    print("Log Analysis System - Example Usage")
    print("=" * 50)
    
    # Sample log file path
    log_file = "data/sample.log"
    
    if not Path(log_file).exists():
        print(f"Sample log file not found: {log_file}")
        print("Please ensure you're running from the project root directory.")
        return
    
    # Example 1: Basic parsing and analytics
    print("\n1. Basic Log Analysis:")
    print("-" * 30)
    
    # Parse logs
    parser = LogParser(strict_mode=False)
    log_entries = parser.parse_file(log_file)
    
    print(f"Parsed {len(log_entries)} log entries")
    
    # Show parsing statistics
    stats = parser.get_parsing_stats()
    print(f"Success rate: {stats['success_rate']:.1%}")
    
    # Generate analytics
    analytics = LogAnalytics(log_entries)
    report = analytics.generate_report(top_n=5)
    
    print(f"Total requests: {report.total_requests}")
    print(f"Unique IPs: {report.unique_ips}")
    print(f"Error rate: {report.error_rate:.2f}%")
    
    # Example 2: Top endpoints
    print("\n2. Top Endpoints:")
    print("-" * 30)
    
    top_endpoints = analytics.get_top_endpoints(5)
    for endpoint, count in top_endpoints.items():
        percentage = (count / report.total_requests) * 100
        print(f"  {endpoint:<20} {count:>3} ({percentage:.1f}%)")
    
    # Example 3: Error analysis
    print("\n3. Error Analysis:")
    print("-" * 30)
    
    error_entries = analytics.get_error_entries()
    print(f"Found {len(error_entries)} error responses:")
    
    for entry in error_entries[:3]:  # Show first 3 errors
        print(f"  {entry.timestamp.strftime('%H:%M:%S')} - "
              f"{entry.ip_address} - {entry.status_code} - {entry.path}")
    
    # Example 4: Traffic patterns
    print("\n4. Hourly Traffic Pattern:")
    print("-" * 30)
    
    hourly_traffic = analytics.get_hourly_traffic_pattern()
    for hour, count in sorted(hourly_traffic.items()):
        if count > 0:  # Only show hours with traffic
            print(f"  {hour}: {count} requests")
    
    # Example 5: Performance metrics (if available)
    print("\n5. Performance Metrics:")
    print("-" * 30)
    
    performance = analytics.calculate_performance_metrics()
    if 'message' in performance:
        print(f"  {performance['message']}")
    else:
        print(f"  Average response time: {performance['avg_response_time']:.3f}s")
        print(f"  95th percentile: {performance['p95_response_time']:.3f}s")
    
    # Example 6: Suspicious activity detection
    print("\n6. Suspicious Activity:")
    print("-" * 30)
    
    suspicious = analytics.detect_suspicious_activity()
    
    if suspicious['high_volume_ips']:
        print("  High volume IPs:")
        for ip, count in suspicious['high_volume_ips'].items():
            print(f"    {ip}: {count} requests")
    else:
        print("  No high-volume IPs detected")
    
    if suspicious['potential_bots']:
        print("  Potential bots:")
        for ip, count in suspicious['potential_bots'].items():
            print(f"    {ip}: {count} bot-like requests")
    else:
        print("  No bot traffic detected")
    
    # Example 7: Trend analysis
    print("\n7. Trend Analysis:")
    print("-" * 30)
    
    trend_analyzer = TrendAnalyzer(log_entries)
    trends = trend_analyzer.analyze_traffic_trends(window_minutes=60)
    
    print(f"Generated {len(trends)} trend data points")
    if trends:
        latest_trend = trends[-1]
        print(f"Latest trend window:")
        print(f"  Request count: {latest_trend['request_count']}")
        print(f"  Error rate: {latest_trend['error_rate']:.1f}%")
        print(f"  Unique IPs: {latest_trend['unique_ips']}")
    
    # Example 8: Save report
    print("\n8. Saving Report:")
    print("-" * 30)
    
    output_file = "example_report.json"
    save_report_as_json(report, output_file)
    print(f"Report saved to {output_file}")
    
    # Show file size
    file_size = Path(output_file).stat().st_size
    print(f"Report file size: {format_bytes(file_size)}")
    
    print("\n" + "=" * 50)
    print("Example completed successfully!")
    print("\nNext steps:")
    print("1. Try modifying the sample log file with your own data")
    print("2. Experiment with different analytics parameters")
    print("3. Check out the programming challenges in CHALLENGES.md")
    print("4. Run the JavaScript API server with: node javascript/server.js")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nExample interrupted by user")
    except Exception as e:
        print(f"Error running example: {e}")
        sys.exit(1)
