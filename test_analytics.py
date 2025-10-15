"""
Test suite for analytics module.

Tests analytics calculations, report generation, and trend analysis.
"""

import pytest
from datetime import datetime, timezone
from collections import Counter

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'python'))

from python.analytics import LogAnalytics, TrendAnalyzer
from python.models import LogEntry, HttpMethod, AnalyticsReport


class TestLogAnalytics:
    """Test cases for LogAnalytics class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.sample_entries = [
            LogEntry(
                ip_address="127.0.0.1",
                timestamp=datetime(2023, 10, 10, 13, 55, 36, tzinfo=timezone.utc),
                method=HttpMethod.GET,
                path="/api/users",
                protocol="HTTP/1.1",
                status_code=200,
                response_size=1234,
                referrer="https://example.com",
                user_agent="Mozilla/5.0"
            ),
            LogEntry(
                ip_address="192.168.1.100",
                timestamp=datetime(2023, 10, 10, 13, 56, 15, tzinfo=timezone.utc),
                method=HttpMethod.POST,
                path="/login",
                protocol="HTTP/1.1",
                status_code=401,
                response_size=0,
                referrer=None,
                user_agent="curl/7.68.0"
            ),
            LogEntry(
                ip_address="127.0.0.1",
                timestamp=datetime(2023, 10, 10, 13, 57, 22, tzinfo=timezone.utc),
                method=HttpMethod.GET,
                path="/dashboard",
                protocol="HTTP/1.1",
                status_code=200,
                response_size=5678,
                referrer="https://app.example.com",
                user_agent="Mozilla/5.0"
            ),
            LogEntry(
                ip_address="203.0.113.15",
                timestamp=datetime(2023, 10, 10, 13, 58, 1, tzinfo=timezone.utc),
                method=HttpMethod.GET,
                path="/api/data",
                protocol="HTTP/1.1",
                status_code=404,
                response_size=156,
                referrer=None,
                user_agent="Python-requests/2.28.1"
            ),
            LogEntry(
                ip_address="127.0.0.1",
                timestamp=datetime(2023, 10, 10, 13, 58, 45, tzinfo=timezone.utc),
                method=HttpMethod.GET,
                path="/health",
                protocol="HTTP/1.1",
                status_code=200,
                response_size=23,
                referrer=None,
                user_agent="Go-http-client/1.1"
            )
        ]
    
    def test_empty_log_entries(self):
        """Test analytics with empty log entries."""
        analytics = LogAnalytics([])
        report = analytics.generate_report()
        
        assert report.total_requests == 0
        assert report.unique_ips == 0
        assert report.error_rate == 0.0
        assert report.avg_response_size == 0.0
        assert report.top_endpoints == {}
        assert report.top_ips == {}
    
    def test_basic_metrics(self):
        """Test basic analytics metrics calculation."""
        analytics = LogAnalytics(self.sample_entries)
        
        assert analytics.total_requests == 5
        assert analytics.get_unique_ip_count() == 3
        assert analytics.calculate_error_rate() == 40.0  # 2 errors out of 5
        assert analytics.calculate_avg_response_size() == (1234 + 0 + 5678 + 156 + 23) / 5
    
    def test_error_rate_calculation(self):
        """Test error rate calculations."""
        analytics = LogAnalytics(self.sample_entries)
        
        # Overall error rate (401 and 404)
        assert analytics.calculate_error_rate() == 40.0
        
        # Server error rate (500+)
        assert analytics.calculate_server_error_rate() == 0.0
        
        # Add a server error
        server_error_entry = LogEntry(
            ip_address="10.0.0.1",
            timestamp=datetime(2023, 10, 10, 14, 0, 0, tzinfo=timezone.utc),
            method=HttpMethod.GET,
            path="/error",
            protocol="HTTP/1.1",
            status_code=500,
            response_size=100
        )
        
        analytics_with_server_error = LogAnalytics(self.sample_entries + [server_error_entry])
        assert analytics_with_server_error.calculate_server_error_rate() == 1/6 * 100  # 1 out of 6
    
    def test_top_endpoints(self):
        """Test top endpoints calculation."""
        analytics = LogAnalytics(self.sample_entries)
        top_endpoints = analytics.get_top_endpoints(3)
        
        # /api/users, /dashboard, /health should each appear once
        assert top_endpoints["/api/users"] == 1
        assert top_endpoints["/dashboard"] == 1
        assert top_endpoints["/health"] == 1
    
    def test_top_ips(self):
        """Test top IPs calculation."""
        analytics = LogAnalytics(self.sample_entries)
        top_ips = analytics.get_top_ips(3)
        
        # 127.0.0.1 appears 3 times
        assert top_ips["127.0.0.1"] == 3
        assert top_ips["192.168.1.100"] == 1
        assert top_ips["203.0.113.15"] == 1
    
    def test_status_code_distribution(self):
        """Test status code distribution."""
        analytics = LogAnalytics(self.sample_entries)
        status_distribution = analytics.get_status_code_distribution()
        
        assert status_distribution[200] == 3
        assert status_distribution[401] == 1
        assert status_distribution[404] == 1
    
    def test_hourly_traffic_pattern(self):
        """Test hourly traffic pattern analysis."""
        analytics = LogAnalytics(self.sample_entries)
        hourly_traffic = analytics.get_hourly_traffic_pattern()
        
        # All our sample entries are in hour 13 (1 PM)
        assert hourly_traffic["13:00"] == 5
        
        # Should have entries for all 24 hours
        assert len(hourly_traffic) == 24
        assert hourly_traffic["00:00"] == 0
        assert hourly_traffic["23:00"] == 0
    
    def test_daily_traffic_pattern(self):
        """Test daily traffic pattern analysis."""
        analytics = LogAnalytics(self.sample_entries)
        daily_traffic = analytics.get_daily_traffic_pattern()
        
        # All entries are on 2023-10-10
        assert daily_traffic["2023-10-10"] == 5
    
    def test_error_entries(self):
        """Test getting error entries."""
        analytics = LogAnalytics(self.sample_entries)
        error_entries = analytics.get_error_entries()
        
        assert len(error_entries) == 2
        assert error_entries[0].status_code == 401
        assert error_entries[1].status_code == 404
    
    def test_slow_requests(self):
        """Test slow request detection."""
        # Add response time data
        entries_with_timing = []
        for entry in self.sample_entries:
            entry.response_time = 0.5  # Fast request
            entries_with_timing.append(entry)
        
        # Add one slow request
        slow_entry = LogEntry(
            ip_address="10.0.0.1",
            timestamp=datetime(2023, 10, 10, 14, 0, 0, tzinfo=timezone.utc),
            method=HttpMethod.GET,
            path="/slow",
            protocol="HTTP/1.1",
            status_code=200,
            response_size=100,
            response_time=2.5
        )
        entries_with_timing.append(slow_entry)
        
        analytics = LogAnalytics(entries_with_timing)
        slow_requests = analytics.get_slow_requests(threshold_seconds=1.0)
        
        assert len(slow_requests) == 1
        assert slow_requests[0].path == "/slow"
    
    def test_large_responses(self):
        """Test large response detection."""
        analytics = LogAnalytics(self.sample_entries)
        large_responses = analytics.get_large_responses(threshold_bytes=1000)
        
        # Should find entries with response_size > 1000
        assert len(large_responses) == 2  # 1234 and 5678 bytes
        assert large_responses[0].response_size == 1234
        assert large_responses[1].response_size == 5678
    
    def test_user_agent_analysis(self):
        """Test user agent analysis."""
        analytics = LogAnalytics(self.sample_entries)
        user_agents = analytics.analyze_user_agents(5)
        
        assert user_agents["Mozilla/5.0"] == 2
        assert user_agents["curl/7.68.0"] == 1
        assert user_agents["Python-requests/2.28.1"] == 1
        assert user_agents["Go-http-client/1.1"] == 1
    
    def test_referrer_analysis(self):
        """Test referrer analysis."""
        analytics = LogAnalytics(self.sample_entries)
        referrers = analytics.analyze_referrers(5)
        
        assert referrers["https://example.com"] == 1
        assert referrers["https://app.example.com"] == 1
    
    def test_suspicious_activity_detection(self):
        """Test suspicious activity detection."""
        # Create entries with suspicious patterns
        suspicious_entries = []
        
        # High volume from single IP
        for i in range(200):
            entry = LogEntry(
                ip_address="192.168.1.200",
                timestamp=datetime(2023, 10, 10, 14, 0, i, tzinfo=timezone.utc),
                method=HttpMethod.GET,
                path=f"/test{i}",
                protocol="HTTP/1.1",
                status_code=200,
                response_size=100
            )
            suspicious_entries.append(entry)
        
        # High error rate from single IP
        for i in range(20):
            entry = LogEntry(
                ip_address="192.168.1.201",
                timestamp=datetime(2023, 10, 10, 14, 0, i, tzinfo=timezone.utc),
                method=HttpMethod.GET,
                path=f"/error{i}",
                protocol="HTTP/1.1",
                status_code=404,
                response_size=0
            )
            suspicious_entries.append(entry)
        
        # Bot traffic
        bot_entry = LogEntry(
            ip_address="192.168.1.202",
            timestamp=datetime(2023, 10, 10, 14, 0, 0, tzinfo=timezone.utc),
            method=HttpMethod.GET,
            path="/robots.txt",
            protocol="HTTP/1.1",
            status_code=200,
            response_size=100,
            user_agent="Googlebot/2.1"
        )
        suspicious_entries.append(bot_entry)
        
        analytics = LogAnalytics(suspicious_entries)
        suspicious = analytics.detect_suspicious_activity()
        
        # Should detect high volume IP
        assert "192.168.1.200" in suspicious['high_volume_ips']
        
        # Should detect high error rate IP
        assert "192.168.1.201" in suspicious['high_error_ips']
        
        # Should detect bot
        assert "192.168.1.202" in suspicious['potential_bots']
    
    def test_performance_metrics(self):
        """Test performance metrics calculation."""
        # Add response time data
        entries_with_timing = []
        response_times = [0.1, 0.2, 0.5, 1.0, 2.0]
        
        for i, entry in enumerate(self.sample_entries):
            entry.response_time = response_times[i]
            entries_with_timing.append(entry)
        
        analytics = LogAnalytics(entries_with_timing)
        metrics = analytics.calculate_performance_metrics()
        
        assert metrics['avg_response_time'] == sum(response_times) / len(response_times)
        assert metrics['median_response_time'] == 0.5
        assert metrics['max_response_time'] == 2.0
        assert metrics['min_response_time'] == 0.1
        assert metrics['p95_response_time'] == 2.0  # 95th percentile
    
    def test_performance_metrics_no_timing_data(self):
        """Test performance metrics with no timing data."""
        analytics = LogAnalytics(self.sample_entries)
        metrics = analytics.calculate_performance_metrics()
        
        assert 'message' in metrics
        assert metrics['message'] == 'No response time data available'
    
    def test_generate_complete_report(self):
        """Test generating complete analytics report."""
        analytics = LogAnalytics(self.sample_entries)
        report = analytics.generate_report(top_n=3)
        
        assert isinstance(report, AnalyticsReport)
        assert report.total_requests == 5
        assert report.unique_ips == 3
        assert report.error_rate == 40.0
        assert len(report.top_endpoints) <= 3
        assert len(report.top_ips) <= 3
        assert len(report.error_log) == 2


class TestTrendAnalyzer:
    """Test cases for TrendAnalyzer class."""
    
    def setup_method(self):
        """Set up test fixtures with time-series data."""
        self.time_series_entries = []
        
        # Create entries over a 2-hour period
        base_time = datetime(2023, 10, 10, 13, 0, 0, tzinfo=timezone.utc)
        
        for hour in range(2):
            for minute in range(0, 60, 10):  # Every 10 minutes
                for i in range(5):  # 5 requests per 10-minute window
                    entry = LogEntry(
                        ip_address=f"192.168.1.{100 + i}",
                        timestamp=base_time.replace(hour=base_time.hour + hour, minute=minute, second=i),
                        method=HttpMethod.GET,
                        path=f"/test{i}",
                        protocol="HTTP/1.1",
                        status_code=200 if i < 4 else 500,  # 1 error per window
                        response_size=100 * (i + 1)
                    )
                    self.time_series_entries.append(entry)
    
    def test_traffic_trends_hourly(self):
        """Test traffic trend analysis with hourly windows."""
        analyzer = TrendAnalyzer(self.time_series_entries)
        trends = analyzer.analyze_traffic_trends(window_minutes=60)
        
        # Should have 2 hour-long windows
        assert len(trends) == 2
        
        for trend in trends:
            assert trend['request_count'] == 30  # 6 windows * 5 requests
            assert trend['error_count'] == 6  # 1 error per 10-minute window
            assert trend['error_rate'] == 20.0  # 6/30 * 100
            assert trend['unique_ips'] == 5
    
    def test_traffic_trends_small_windows(self):
        """Test traffic trend analysis with small windows."""
        analyzer = TrendAnalyzer(self.time_series_entries)
        trends = analyzer.analyze_traffic_trends(window_minutes=10)
        
        # Should have 12 ten-minute windows (6 per hour * 2 hours)
        assert len(trends) == 12
        
        for trend in trends:
            assert trend['request_count'] == 5
            assert trend['error_count'] == 1
            assert trend['error_rate'] == 20.0
            assert trend['unique_ips'] == 5
    
    def test_empty_trends(self):
        """Test trend analysis with empty data."""
        analyzer = TrendAnalyzer([])
        trends = analyzer.analyze_traffic_trends()
        
        assert trends == []
    
    def test_single_entry_trends(self):
        """Test trend analysis with single entry."""
        single_entry = [self.time_series_entries[0]]
        analyzer = TrendAnalyzer(single_entry)
        trends = analyzer.analyze_traffic_trends(window_minutes=60)
        
        assert len(trends) == 1
        assert trends[0]['request_count'] == 1
        assert trends[0]['error_count'] == 0
        assert trends[0]['unique_ips'] == 1


class TestAnalyticsEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_analytics_with_none_values(self):
        """Test analytics with entries containing None values."""
        entries_with_none = [
            LogEntry(
                ip_address="127.0.0.1",
                timestamp=datetime(2023, 10, 10, 13, 55, 36, tzinfo=timezone.utc),
                method=HttpMethod.GET,
                path="/test",
                protocol="HTTP/1.1",
                status_code=200,
                response_size=1234,
                referrer=None,
                user_agent=None,
                response_time=None
            )
        ]
        
        analytics = LogAnalytics(entries_with_none)
        report = analytics.generate_report()
        
        # Should handle None values gracefully
        assert report.total_requests == 1
        assert report.avg_response_size == 1234.0
    
    def test_extreme_values(self):
        """Test analytics with extreme values."""
        extreme_entry = LogEntry(
            ip_address="255.255.255.255",
            timestamp=datetime(2023, 10, 10, 13, 55, 36, tzinfo=timezone.utc),
            method=HttpMethod.GET,
            path="/test",
            protocol="HTTP/1.1",
            status_code=599,
            response_size=999999999,
            response_time=999.999
        )
        
        analytics = LogAnalytics([extreme_entry])
        report = analytics.generate_report()
        
        assert report.total_requests == 1
        assert report.avg_response_size == 999999999
        
        performance = analytics.calculate_performance_metrics()
        assert performance['max_response_time'] == 999.999
    
    def test_duplicate_entries(self):
        """Test analytics with duplicate entries."""
        base_entry = LogEntry(
            ip_address="127.0.0.1",
            timestamp=datetime(2023, 10, 10, 13, 55, 36, tzinfo=timezone.utc),
            method=HttpMethod.GET,
            path="/test",
            protocol="HTTP/1.1",
            status_code=200,
            response_size=1234
        )
        
        duplicate_entries = [base_entry] * 10
        analytics = LogAnalytics(duplicate_entries)
        
        assert analytics.total_requests == 10
        assert analytics.get_unique_ip_count() == 1
        
        top_endpoints = analytics.get_top_endpoints(5)
        assert top_endpoints["/test"] == 10
