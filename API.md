# API Documentation

The Log Analysis System provides a RESTful API for uploading and analyzing log files. This document describes all available endpoints and their usage.

## Base URL
```
http://localhost:3000
```

## Authentication
Currently, the API does not require authentication. In production, you should implement proper authentication and authorization.

## Rate Limiting
- **Rate Limit**: 100 requests per 15 minutes per IP
- **File Upload Limit**: 100MB per file
- **Rate Limit Headers**: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

---

## Endpoints

### Health Check

#### `GET /health`
Check if the API server is running and healthy.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2023-10-10T14:30:00.000Z",
  "version": "1.0.0"
}
```

---

### Log Analysis

#### `POST /api/analyze`
Upload and analyze a log file.

**Request:**
- **Content-Type**: `multipart/form-data`
- **File Field**: `logfile` (required)
- **Parameters** (optional, in request body):

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `strictMode` | boolean | `false` | Fail on parsing errors |
| `topN` | integer | `10` | Number of top items in rankings |
| `includePerformanceMetrics` | boolean | `true` | Include response time analysis |
| `includeSuspiciousActivity` | boolean | `true` | Include security analysis |
| `slowRequestThreshold` | number | `1.0` | Threshold for slow requests (seconds) |
| `largeResponseThreshold` | integer | `1048576` | Threshold for large responses (bytes) |

**Example Request:**
```bash
curl -X POST http://localhost:3000/api/analyze \
  -F "logfile=@access.log" \
  -F "strictMode=false" \
  -F "topN=20"
```

**Response:**
```json
{
  "jobId": "123e4567-e89b-12d3-a456-426614174000",
  "status": "accepted",
  "message": "Log file queued for processing"
}
```

**Status Codes:**
- `202`: Request accepted, processing started
- `400`: Invalid request (bad file, invalid parameters)
- `413`: File too large
- `429`: Rate limit exceeded
- `500`: Internal server error

---

### Job Management

#### `GET /api/jobs/{jobId}`
Get the status of a processing job.

**Path Parameters:**
- `jobId`: UUID of the job

**Response:**
```json
{
  "jobId": "123e4567-e89b-12d3-a456-426614174000",
  "status": "processing",
  "progress": 75,
  "filename": "access.log",
  "createdAt": "2023-10-10T14:30:00.000Z",
  "completedAt": null,
  "error": null
}
```

**Job Status Values:**
- `queued`: Job is waiting to be processed
- `processing`: Job is currently being analyzed
- `completed`: Job finished successfully
- `failed`: Job failed with an error

#### `GET /api/jobs`
List all jobs (for debugging/monitoring).

**Query Parameters:**
- `limit`: Number of jobs to return (1-100, default: 20)
- `offset`: Number of jobs to skip (default: 0)

**Response:**
```json
{
  "jobs": [
    {
      "jobId": "123e4567-e89b-12d3-a456-426614174000",
      "status": "completed",
      "filename": "access.log",
      "createdAt": "2023-10-10T14:30:00.000Z",
      "progress": 100
    }
  ],
  "total": 1
}
```

#### `DELETE /api/jobs/{jobId}`
Delete a job and its associated data.

**Response:**
```json
{
  "message": "Job deleted successfully"
}
```

---

### Reports

#### `GET /api/reports/{jobId}`
Get the analysis report for a completed job.

**Path Parameters:**
- `jobId`: UUID of the completed job

**Response:**
```json
{
  "jobId": "123e4567-e89b-12d3-a456-426614174000",
  "filename": "access.log",
  "generatedAt": "2023-10-10T14:35:00.000Z",
  "report": {
    "total_requests": 1000,
    "unique_ips": 45,
    "error_rate": 12.5,
    "avg_response_size": 2048.5,
    "top_endpoints": {
      "/api/users": 234,
      "/login": 123,
      "/dashboard": 89
    },
    "top_ips": {
      "192.168.1.100": 456,
      "10.0.0.50": 234,
      "203.0.113.15": 123
    },
    "status_code_distribution": {
      "200": 750,
      "404": 125,
      "500": 25,
      "401": 100
    },
    "hourly_traffic": {
      "00:00": 0,
      "01:00": 5,
      "13:00": 234,
      "14:00": 456
    },
    "error_count": 250
  },
  "parsing_stats": {
    "parsed_count": 995,
    "error_count": 5,
    "success_rate": 0.995
  },
  "performance_metrics": {
    "avg_response_time": 0.245,
    "median_response_time": 0.180,
    "p95_response_time": 0.890,
    "p99_response_time": 1.234,
    "max_response_time": 5.678,
    "min_response_time": 0.001
  },
  "suspicious_activity": {
    "high_volume_ips": {
      "192.168.1.200": 2500
    },
    "high_error_ips": {
      "203.0.113.50": {
        "error_count": 45,
        "total_requests": 50,
        "error_rate": 90.0
      }
    },
    "potential_bots": {
      "198.51.100.42": 234
    }
  },
  "file_info": {
    "total_entries": 1000,
    "processed_successfully": 995,
    "processing_errors": 5
  }
}
```

---

## Error Responses

All error responses follow this format:

```json
{
  "error": "Error message",
  "message": "Detailed description",
  "timestamp": "2023-10-10T14:30:00.000Z"
}
```

### Common Error Codes

| Status | Error | Description |
|--------|-------|-------------|
| 400 | Invalid file type | Only .log, .txt, and .gz files are allowed |
| 400 | File too large | File exceeds 100MB limit |
| 400 | Invalid parameters | Request validation failed |
| 404 | Job not found | Job ID does not exist |
| 404 | Report not found | Report not available (job not completed) |
| 429 | Rate limit exceeded | Too many requests from this IP |
| 500 | Internal server error | Server-side processing error |

---

## Usage Examples

### Complete Workflow Example

```bash
# 1. Upload log file for analysis
RESPONSE=$(curl -s -X POST http://localhost:3000/api/analyze \
  -F "logfile=@access.log" \
  -F "topN=15" \
  -F "strictMode=false")

JOB_ID=$(echo $RESPONSE | jq -r '.jobId')
echo "Job ID: $JOB_ID"

# 2. Check job status (poll until complete)
while true; do
  STATUS=$(curl -s http://localhost:3000/api/jobs/$JOB_ID | jq -r '.status')
  echo "Status: $STATUS"
  
  if [ "$STATUS" = "completed" ]; then
    break
  elif [ "$STATUS" = "failed" ]; then
    echo "Job failed!"
    exit 1
  fi
  
  sleep 2
done

# 3. Get the analysis report
curl -s http://localhost:3000/api/reports/$JOB_ID | jq '.' > report.json
echo "Report saved to report.json"

# 4. Clean up (optional)
curl -X DELETE http://localhost:3000/api/jobs/$JOB_ID
```

### JavaScript/Node.js Example

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

async function analyzeLogFile(filePath) {
  try {
    // Upload file
    const formData = new FormData();
    formData.append('logfile', fs.createReadStream(filePath));
    formData.append('topN', '20');
    
    const uploadResponse = await axios.post('http://localhost:3000/api/analyze', formData, {
      headers: formData.getHeaders()
    });
    
    const jobId = uploadResponse.data.jobId;
    console.log('Job ID:', jobId);
    
    // Poll for completion
    let status = 'queued';
    while (status !== 'completed' && status !== 'failed') {
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const statusResponse = await axios.get(`http://localhost:3000/api/jobs/${jobId}`);
      status = statusResponse.data.status;
      console.log('Status:', status, `(${statusResponse.data.progress}%)`);
    }
    
    if (status === 'failed') {
      throw new Error('Analysis failed');
    }
    
    // Get report
    const reportResponse = await axios.get(`http://localhost:3000/api/reports/${jobId}`);
    console.log('Analysis complete!');
    console.log('Total requests:', reportResponse.data.report.total_requests);
    console.log('Error rate:', reportResponse.data.report.error_rate + '%');
    
    return reportResponse.data;
    
  } catch (error) {
    console.error('Error:', error.message);
    throw error;
  }
}

// Usage
analyzeLogFile('./access.log')
  .then(report => console.log('Success:', report.report.total_requests, 'requests'))
  .catch(error => console.error('Failed:', error.message));
```

### Python Example

```python
import requests
import time
import json

def analyze_log_file(file_path):
    # Upload file
    with open(file_path, 'rb') as f:
        files = {'logfile': f}
        data = {'topN': 20, 'strictMode': False}
        
        response = requests.post('http://localhost:3000/api/analyze', 
                               files=files, data=data)
        response.raise_for_status()
        
        job_id = response.json()['jobId']
        print(f"Job ID: {job_id}")
    
    # Poll for completion
    while True:
        response = requests.get(f'http://localhost:3000/api/jobs/{job_id}')
        response.raise_for_status()
        
        job_data = response.json()
        status = job_data['status']
        progress = job_data['progress']
        
        print(f"Status: {status} ({progress}%)")
        
        if status == 'completed':
            break
        elif status == 'failed':
            raise Exception(f"Job failed: {job_data.get('error', 'Unknown error')}")
        
        time.sleep(2)
    
    # Get report
    response = requests.get(f'http://localhost:3000/api/reports/{job_id}')
    response.raise_for_status()
    
    report = response.json()
    print(f"Analysis complete!")
    print(f"Total requests: {report['report']['total_requests']}")
    print(f"Error rate: {report['report']['error_rate']}%")
    
    return report

# Usage
try:
    report = analyze_log_file('access.log')
    print("Success!")
except Exception as e:
    print(f"Error: {e}")
```

---

## Development and Testing

### Running the Server
```bash
cd javascript
npm install
npm start
```

### Running Tests
```bash
# JavaScript tests
cd javascript
npm test

# Python tests
cd python
python -m pytest tests/
```

### Environment Variables
- `PORT`: Server port (default: 3000)
- `PYTHON_PATH`: Path to Python executable (default: python3)
- `NODE_ENV`: Environment (development/production)

---

## Production Considerations

1. **Authentication**: Implement proper API authentication
2. **File Storage**: Use cloud storage instead of local filesystem
3. **Database**: Replace in-memory job storage with Redis/PostgreSQL
4. **Monitoring**: Add comprehensive logging and metrics
5. **Security**: Implement file scanning and additional validation
6. **Scaling**: Use message queues for background processing
7. **CORS**: Configure CORS policies for web applications
