/**
 * Express API server for log analysis system.
 * 
 * Provides RESTful endpoints for:
 * - Uploading and processing log files
 * - Retrieving analysis reports
 * - Managing processing jobs
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
const multer = require('multer');
const { v4: uuidv4 } = require('uuid');
const fs = require('fs').promises;
const path = require('path');

const LogProcessor = require('./processor');
const RequestValidator = require('./validator');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware setup
app.use(helmet());
app.use(compression());
app.use(cors());
app.use(express.json({ limit: '10mb' }));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP, please try again later.'
});
app.use('/api/', limiter);

// File upload configuration
const upload = multer({
  dest: '../data/uploads/',
  limits: {
    fileSize: 100 * 1024 * 1024 // 100MB limit
  },
  fileFilter: (req, file, cb) => {
    // Accept log files and compressed files
    const allowedExtensions = ['.log', '.txt', '.gz'];
    const fileExtension = path.extname(file.originalname).toLowerCase();
    
    if (allowedExtensions.includes(fileExtension)) {
      cb(null, true);
    } else {
      cb(new Error('Invalid file type. Only .log, .txt, and .gz files are allowed.'));
    }
  }
});

// In-memory job storage (in production, use Redis or database)
const jobs = new Map();
const reports = new Map();

const processor = new LogProcessor();
const validator = new RequestValidator();

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: '1.0.0'
  });
});

// Upload and analyze log file
app.post('/api/analyze', upload.single('logfile'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        error: 'No log file provided'
      });
    }

    // Validate request parameters
    const validationResult = validator.validateAnalysisRequest(req.body);
    if (!validationResult.isValid) {
      return res.status(400).json({
        error: 'Invalid request parameters',
        details: validationResult.errors
      });
    }

    const jobId = uuidv4();
    const job = {
      id: jobId,
      status: 'queued',
      filename: req.file.originalname,
      filepath: req.file.path,
      options: validationResult.data,
      createdAt: new Date().toISOString(),
      progress: 0
    };

    jobs.set(jobId, job);

    // Start processing asynchronously
    processLogFileAsync(jobId);

    res.status(202).json({
      jobId: jobId,
      status: 'accepted',
      message: 'Log file queued for processing'
    });

  } catch (error) {
    console.error('Error in /api/analyze:', error);
    res.status(500).json({
      error: 'Internal server error',
      message: error.message
    });
  }
});

// Get job status
app.get('/api/jobs/:jobId', (req, res) => {
  const jobId = req.params.jobId;
  const job = jobs.get(jobId);

  if (!job) {
    return res.status(404).json({
      error: 'Job not found'
    });
  }

  res.json({
    jobId: job.id,
    status: job.status,
    progress: job.progress,
    filename: job.filename,
    createdAt: job.createdAt,
    completedAt: job.completedAt,
    error: job.error
  });
});

// Get analysis report
app.get('/api/reports/:jobId', (req, res) => {
  const jobId = req.params.jobId;
  const job = jobs.get(jobId);

  if (!job) {
    return res.status(404).json({
      error: 'Job not found'
    });
  }

  if (job.status !== 'completed') {
    return res.status(400).json({
      error: 'Analysis not completed yet',
      status: job.status
    });
  }

  const report = reports.get(jobId);
  if (!report) {
    return res.status(404).json({
      error: 'Report not found'
    });
  }

  res.json(report);
});

// List all jobs for debugging
app.get('/api/jobs', (req, res) => {
  const jobList = Array.from(jobs.values()).map(job => ({
    jobId: job.id,
    status: job.status,
    filename: job.filename,
    createdAt: job.createdAt,
    progress: job.progress
  }));

  res.json({
    jobs: jobList,
    total: jobList.length
  });
});

// Delete job and associated data
app.delete('/api/jobs/:jobId', async (req, res) => {
  const jobId = req.params.jobId;
  const job = jobs.get(jobId);

  if (!job) {
    return res.status(404).json({
      error: 'Job not found'
    });
  }

  try {
    // Clean up uploaded file
    if (job.filepath) {
      try {
        await fs.unlink(job.filepath);
      } catch (err) {
        console.warn('Could not delete uploaded file:', err.message);
      }
    }

    // Remove from memory
    jobs.delete(jobId);
    reports.delete(jobId);

    res.json({
      message: 'Job deleted successfully'
    });

  } catch (error) {
    console.error('Error deleting job:', error);
    res.status(500).json({
      error: 'Error deleting job',
      message: error.message
    });
  }
});

// Error handling middleware
app.use((error, req, res, next) => {
  console.error('Unhandled error:', error);

  if (error instanceof multer.MulterError) {
    if (error.code === 'LIMIT_FILE_SIZE') {
      return res.status(400).json({
        error: 'File too large',
        message: 'File size must be less than 100MB'
      });
    }
  }

  res.status(500).json({
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'development' ? error.message : 'Something went wrong'
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    error: 'Not found',
    message: `Route ${req.method} ${req.originalUrl} not found`
  });
});

/**
 * Process log file asynchronously
 */
async function processLogFileAsync(jobId) {
  const job = jobs.get(jobId);
  if (!job) return;

  try {
    job.status = 'processing';
    job.progress = 10;

    // Call Python processor
    const result = await processor.processLogFile(job.filepath, job.options);
    
    job.progress = 90;

    // Store the report
    reports.set(jobId, {
      jobId: jobId,
      filename: job.filename,
      generatedAt: new Date().toISOString(),
      ...result
    });

    job.status = 'completed';
    job.progress = 100;
    job.completedAt = new Date().toISOString();

  } catch (error) {
    console.error(`Error processing job ${jobId}:`, error);
    job.status = 'failed';
    job.error = error.message;
  }
}

// Start server
if (require.main === module) {
  app.listen(PORT, () => {
    console.log(`Log Analysis API server running on port ${PORT}`);
    console.log(`Health check: http://localhost:${PORT}/health`);
  });
}

module.exports = app;
