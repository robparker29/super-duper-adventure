"""
Analytics engine for log analysis and reporting.

Provides comprehensive analysis of web server logs including:
- Traffic patterns and trends
- Error rate monitoring  
- Performance metrics
- Popular endpoints and user patterns
"""

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import statistics

from models import LogEntry, AnalyticsReport


class LogAnalytics:
    """
    Comprehensive analytics engine for web server logs.
    
    Generates insights and metrics from parsed log entries.
    """
    
    def __init__(self, log_entries: List[LogEntry]):
        """
        Initialize analytics with log entries.
        
        Args:
            log_entries: List of parsed log entries
        """
        self.log_entries = log_entries
        self.total_requests = len(log_entries)
    
    def generate_report(self, top_n: int = 10) -> AnalyticsReport:
        """
        Generate comprehensive analytics report.
        
        Args:
            top_n: Number of top items to include in rankings
            
        Returns:
            AnalyticsReport object with all metrics
        """
        if not self.log_entries:
            return self._empty_report()
        
        return AnalyticsReport(
            total_requests=self.total_requests,
            unique_ips=self.get_unique_ip_count(),
            error_rate=self.calculate_error_rate(),
            avg_response_size=self.calculate_avg_response_size(),
            top_endpoints=self.get_top_endpoints(top_n),
            top_ips=self.get_top_ips(top_n),
            status_code_distribution=self.get_status_code_distribution(),
            hourly_traffic=self.get_hourly_traffic_pattern(),
            error_log=self.get_error_entries()
        )
    
    def get_unique_ip_count(self) -> int:
        """Count unique IP addresses."""
        return len(set(entry.ip_address for entry in self.log_entries))
    
    def calculate_error_rate(self) -> float:
        """Calculate overall error rate (4xx and 5xx responses)."""
        if self.total_requests == 0:
            return 0.0
        
        error_count = sum(1 for entry in self.log_entries if entry.is_error)
        return (error_count / self.total_requests) * 100
    
    def calculate_server_error_rate(self) -> float:
        """Calculate server error rate (5xx responses only)."""
        if self.total_requests == 0:
            return 0.0
        
        server_error_count = sum(1 for entry in self.log_entries if entry.is_server_error)
        return (server_error_count / self.total_requests) * 100
    
    def calculate_avg_response_size(self) -> float:
        """Calculate average response size in bytes."""
        if not self.log_entries:
            return 0.0
        
        total_size = sum(entry.response_size for entry in self.log_entries)
        return total_size / len(self.log_entries)
    
    def get_top_endpoints(self, n: int = 10) -> Dict[str, int]:
        """
        Get most frequently requested endpoints.
        
        Args:
            n: Number of top endpoints to return
            
        Returns:
            Dictionary of endpoint -> request count
        """
        endpoint_counter = Counter(entry.path for entry in self.log_entries)
        return dict(endpoint_counter.most_common(n))
    
    def get_top_ips(self, n: int = 10) -> Dict[str, int]:
        """
        Get IP addresses with most requests.
        
        Args:
            n: Number of top IPs to return
            
        Returns:
            Dictionary of IP -> request count
        """
        ip_counter = Counter(entry.ip_address for entry in self.log_entries)
        return dict(ip_counter.most_common(n))
    
    def get_status_code_distribution(self) -> Dict[int, int]:
        """Get distribution of HTTP status codes."""
        status_counter = Counter(entry.status_code for entry in self.log_entries)
        return dict(status_counter)
    
    def get_hourly_traffic_pattern(self) -> Dict[str, int]:
        """
        Analyze traffic patterns by hour of day.
        
        Returns:
            Dictionary of hour -> request count
        """
        hourly_traffic = defaultdict(int)
        
        for entry in self.log_entries:
            hour_key = entry.timestamp.strftime('%H:00')
            hourly_traffic[hour_key] += 1
        
        # Ensure all 24 hours are represented
        for hour in range(24):
            hour_key = f"{hour:02d}:00"
            if hour_key not in hourly_traffic:
                hourly_traffic[hour_key] = 0
        
        return dict(sorted(hourly_traffic.items()))
    
    def get_daily_traffic_pattern(self) -> Dict[str, int]:
        """Analyze traffic patterns by day."""
        daily_traffic = defaultdict(int)
        
        for entry in self.log_entries:
            day_key = entry.timestamp.strftime('%Y-%m-%d')
            daily_traffic[day_key] += 1
        
        return dict(sorted(daily_traffic.items()))
    
    def get_error_entries(self) -> List[LogEntry]:
        """Get all log entries that represent errors."""
        return [entry for entry in self.log_entries if entry.is_error]
    
    def get_slow_requests(self, threshold_seconds: float = 1.0) -> List[LogEntry]:
        """
        Get requests that took longer than threshold.
        
        Args:
            threshold_seconds: Response time threshold in seconds
            
        Returns:
            List of slow log entries
        """
        return [
            entry for entry in self.log_entries 
            if entry.response_time and entry.response_time > threshold_seconds
        ]
    
    def get_large_responses(self, threshold_bytes: int = 1024 * 1024) -> List[LogEntry]:
        """
        Get responses larger than threshold.
        
        Args:
            threshold_bytes: Response size threshold in bytes
            
        Returns:
            List of large response entries
        """
        return [
            entry for entry in self.log_entries 
            if entry.response_size > threshold_bytes
        ]
    
    def analyze_user_agents(self, n: int = 10) -> Dict[str, int]:
        """Analyze most common user agents."""
        user_agent_counter = Counter(
            entry.user_agent for entry in self.log_entries 
            if entry.user_agent
        )
        return dict(user_agent_counter.most_common(n))
    
    def analyze_referrers(self, n: int = 10) -> Dict[str, int]:
        """Analyze most common referrers."""
        referrer_counter = Counter(
            entry.referrer for entry in self.log_entries 
            if entry.referrer
        )
        return dict(referrer_counter.most_common(n))
    
    def detect_suspicious_activity(self) -> Dict[str, Any]:
        """
        Detect potentially suspicious patterns in logs.
        
        Returns:
            Dictionary with suspicious activity indicators
        """
        suspicious = {}
        
        # IPs with unusually high request rates
        ip_counts = Counter(entry.ip_address for entry in self.log_entries)
        avg_requests_per_ip = statistics.mean(ip_counts.values()) if ip_counts else 0
        threshold = avg_requests_per_ip * 10  # 10x average
        
        suspicious['high_volume_ips'] = {
            ip: count for ip, count in ip_counts.items() 
            if count > threshold and count > 100
        }
        
        # High error rate IPs
        ip_errors = defaultdict(int)
        ip_totals = defaultdict(int)
        
        for entry in self.log_entries:
            ip_totals[entry.ip_address] += 1
            if entry.is_error:
                ip_errors[entry.ip_address] += 1
        
        suspicious['high_error_ips'] = {
            ip: {
                'error_count': error_count,
                'total_requests': ip_totals[ip],
                'error_rate': (error_count / ip_totals[ip]) * 100
            }
            for ip, error_count in ip_errors.items()
            if ip_totals[ip] > 10 and (error_count / ip_totals[ip]) > 0.5
        }
        
        # Potential bot traffic (based on user agent patterns)
        bot_indicators = ['bot', 'crawler', 'spider', 'scraper']
        potential_bots = Counter()
        
        for entry in self.log_entries:
            if entry.user_agent:
                user_agent_lower = entry.user_agent.lower()
                if any(indicator in user_agent_lower for indicator in bot_indicators):
                    potential_bots[entry.ip_address] += 1
        
        suspicious['potential_bots'] = dict(potential_bots.most_common(10))
        
        return suspicious
    
    def calculate_performance_metrics(self) -> Dict[str, float]:
        """Calculate performance-related metrics."""
        if not self.log_entries:
            return {}
        
        # Filter entries with response time data
        timed_entries = [e for e in self.log_entries if e.response_time is not None]
        
        if not timed_entries:
            return {'message': 'No response time data available'}
        
        response_times = [e.response_time for e in timed_entries]
        
        return {
            'avg_response_time': statistics.mean(response_times),
            'median_response_time': statistics.median(response_times),
            'p95_response_time': self._percentile(response_times, 95),
            'p99_response_time': self._percentile(response_times, 99),
            'max_response_time': max(response_times),
            'min_response_time': min(response_times)
        }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile value."""
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def _empty_report(self) -> AnalyticsReport:
        """Create empty report for no data."""
        return AnalyticsReport(
            total_requests=0,
            unique_ips=0,
            error_rate=0.0,
            avg_response_size=0.0,
            top_endpoints={},
            top_ips={},
            status_code_distribution={},
            hourly_traffic={},
            error_log=[]
        )


class TrendAnalyzer:
    """
    Analyzes trends and patterns over time periods.
    """
    
    def __init__(self, log_entries: List[LogEntry]):
        self.log_entries = sorted(log_entries, key=lambda x: x.timestamp)
    
    def analyze_traffic_trends(self, window_minutes: int = 60) -> List[Dict[str, Any]]:
        """
        Analyze traffic trends over time windows.
        
        Args:
            window_minutes: Size of time window in minutes
            
        Returns:
            List of trend data points
        """
        if not self.log_entries:
            return []
        
        trends = []
        start_time = self.log_entries[0].timestamp
        end_time = self.log_entries[-1].timestamp
        window_delta = timedelta(minutes=window_minutes)
        
        current_time = start_time
        while current_time < end_time:
            window_end = current_time + window_delta
            
            # Count requests in this window
            window_requests = [
                entry for entry in self.log_entries
                if current_time <= entry.timestamp < window_end
            ]
            
            if window_requests:
                error_count = sum(1 for entry in window_requests if entry.is_error)
                trends.append({
                    'timestamp': current_time.isoformat(),
                    'request_count': len(window_requests),
                    'error_count': error_count,
                    'error_rate': (error_count / len(window_requests)) * 100,
                    'unique_ips': len(set(entry.ip_address for entry in window_requests))
                })
            
            current_time = window_end
        
        return trends
