#!/usr/bin/env python3
"""
Command-line interface for the Log Analysis System.

Provides easy access to log parsing and analytics functionality.
"""

import argparse
import json
import sys
from pathlib import Path

# Add the python directory to path
sys.path.append(str(Path(__file__).parent / 'python'))

from python.log_parser import LogParser
from python.analytics import LogAnalytics
from python.utils import save_report_as_json, format_bytes, format_duration
import time


def main():
    parser = argparse.ArgumentParser(
        description='Analyze web server logs and generate insights',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s data/sample.log                    # Basic analysis
  %(prog)s data/sample.log --output report.json  # Save to file
  %(prog)s data/sample.log --top 20 --strict     # Detailed analysis
  %(prog)s data/sample.log --format json          # JSON output
        """
    )
    
    parser.add_argument(
        'logfile',
        help='Path to log file to analyze'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output file path (default: print to stdout)'
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['json', 'text'],
        default='text',
        help='Output format (default: text)'
    )
    
    parser.add_argument(
        '--top', '-t',
        type=int,
        default=10,
        help='Number of top items to show (default: 10)'
    )
    
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Enable strict parsing mode (fail on errors)'
    )
    
    parser.add_argument(
        '--performance',
        action='store_true',
        help='Include performance metrics in output'
    )
    
    parser.add_argument(
        '--suspicious',
        action='store_true',
        help='Include suspicious activity analysis'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress progress output'
    )
    
    args = parser.parse_args()
    
    try:
        # Validate input file
        log_file = Path(args.logfile)
        if not log_file.exists():
            print(f"Error: Log file '{args.logfile}' not found", file=sys.stderr)
            sys.exit(1)
        
        if not args.quiet:
            print(f"Analyzing log file: {args.logfile}")
            print(f"File size: {format_bytes(log_file.stat().st_size)}")
        
        # Parse logs
        start_time = time.time()
        log_parser = LogParser(strict_mode=args.strict)
        
        if not args.quiet:
            print("Parsing log entries...")
        
        log_entries = log_parser.parse_file(args.logfile)
        parse_time = time.time() - start_time
        
        if not args.quiet:
            stats = log_parser.get_parsing_stats()
            print(f"Parsed {stats['parsed_count']} entries in {format_duration(parse_time)}")
            if stats['error_count'] > 0:
                print(f"Encountered {stats['error_count']} parsing errors")
        
        # Generate analytics
        if not args.quiet:
            print("Generating analytics...")
        
        analytics_start = time.time()
        analytics = LogAnalytics(log_entries)
        report = analytics.generate_report(top_n=args.top)
        analytics_time = time.time() - analytics_start
        
        if not args.quiet:
            print(f"Analytics completed in {format_duration(analytics_time)}")
        
        # Prepare output data
        output_data = {
            'report': report.to_dict(),
            'parsing_stats': log_parser.get_parsing_stats(),
            'processing_time': {
                'parsing_seconds': round(parse_time, 3),
                'analytics_seconds': round(analytics_time, 3),
                'total_seconds': round(parse_time + analytics_time, 3)
            }
        }
        
        # Add optional analysis
        if args.performance:
            output_data['performance_metrics'] = analytics.calculate_performance_metrics()
        
        if args.suspicious:
            output_data['suspicious_activity'] = analytics.detect_suspicious_activity()
        
        # Output results
        if args.format == 'json':
            if args.output:
                save_report_as_json(report, args.output)
                if not args.quiet:
                    print(f"Report saved to {args.output}")
            else:
                print(json.dumps(output_data, indent=2, default=str))
        else:
            # Text format output
            output_text = format_text_report(output_data, args)
            
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(output_text)
                if not args.quiet:
                    print(f"Report saved to {args.output}")
            else:
                print(output_text)
    
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def format_text_report(data, args):
    """Format analytics report as human-readable text."""
    report = data['report']
    parsing_stats = data['parsing_stats']
    processing_time = data['processing_time']
    
    lines = []
    lines.append("=" * 60)
    lines.append("LOG ANALYSIS REPORT")
    lines.append("=" * 60)
    
    # Summary statistics
    lines.append(f"\nSUMMARY:")
    lines.append(f"  Total Requests: {report['total_requests']:,}")
    lines.append(f"  Unique IPs: {report['unique_ips']:,}")
    lines.append(f"  Error Rate: {report['error_rate']:.2f}%")
    lines.append(f"  Avg Response Size: {format_bytes(int(report['avg_response_size']))}")
    
    # Processing stats
    lines.append(f"\nPROCESSING:")
    lines.append(f"  Parsing Time: {format_duration(processing_time['parsing_seconds'])}")
    lines.append(f"  Analytics Time: {format_duration(processing_time['analytics_seconds'])}")
    lines.append(f"  Success Rate: {parsing_stats['success_rate']:.1%}")
    
    # Top endpoints
    if report['top_endpoints']:
        lines.append(f"\nTOP ENDPOINTS:")
        for endpoint, count in report['top_endpoints'].items():
            percentage = (count / report['total_requests']) * 100
            lines.append(f"  {endpoint:<40} {count:>6} ({percentage:.1f}%)")
    
    # Top IPs
    if report['top_ips']:
        lines.append(f"\nTOP IP ADDRESSES:")
        for ip, count in report['top_ips'].items():
            percentage = (count / report['total_requests']) * 100
            lines.append(f"  {ip:<15} {count:>6} ({percentage:.1f}%)")
    
    # Status codes
    if report['status_code_distribution']:
        lines.append(f"\nSTATUS CODE DISTRIBUTION:")
        for status, count in sorted(report['status_code_distribution'].items()):
            percentage = (count / report['total_requests']) * 100
            lines.append(f"  {status} {count:>6} ({percentage:.1f}%)")
    
    # Hourly traffic (condensed view)
    if report['hourly_traffic']:
        lines.append(f"\nHOURLY TRAFFIC PATTERN:")
        traffic_items = sorted(report['hourly_traffic'].items())
        for i in range(0, len(traffic_items), 6):  # Show every 4 hours
            chunk = traffic_items[i:i+6]
            line = "  "
            for hour, count in chunk:
                line += f"{hour}: {count:>4} "
            lines.append(line.rstrip())
    
    # Performance metrics
    if args.performance and 'performance_metrics' in data:
        metrics = data['performance_metrics']
        if 'avg_response_time' in metrics:
            lines.append(f"\nPERFORMANCE METRICS:")
            lines.append(f"  Avg Response Time: {metrics['avg_response_time']:.3f}s")
            lines.append(f"  95th Percentile: {metrics.get('p95_response_time', 0):.3f}s")
            lines.append(f"  Max Response Time: {metrics.get('max_response_time', 0):.3f}s")
    
    # Suspicious activity
    if args.suspicious and 'suspicious_activity' in data:
        suspicious = data['suspicious_activity']
        if any(suspicious.values()):
            lines.append(f"\nSUSPICIOUS ACTIVITY:")
            
            if suspicious.get('high_volume_ips'):
                lines.append("  High Volume IPs:")
                for ip, count in list(suspicious['high_volume_ips'].items())[:5]:
                    lines.append(f"    {ip}: {count} requests")
            
            if suspicious.get('potential_bots'):
                lines.append("  Potential Bots:")
                for ip, count in list(suspicious['potential_bots'].items())[:5]:
                    lines.append(f"    {ip}: {count} bot-like requests")
    
    # Errors summary
    if report['error_count'] > 0:
        lines.append(f"\nERRORS:")
        lines.append(f"  Total Error Responses: {report['error_count']}")
        if parsing_stats['error_count'] > 0:
            lines.append(f"  Parsing Errors: {parsing_stats['error_count']}")
    
    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


if __name__ == '__main__':
    main()
