/**
 * Request validation module for API endpoints.
 * 
 * Provides validation for incoming requests to ensure data integrity
 * and security.
 */

const Joi = require('joi');

class RequestValidator {
  constructor() {
    this.schemas = this.defineSchemas();
  }

  /**
   * Define validation schemas
   */
  defineSchemas() {
    return {
      analysisRequest: Joi.object({
        strictMode: Joi.boolean().default(false),
        topN: Joi.number().integer().min(1).max(100).default(10),
        includePerformanceMetrics: Joi.boolean().default(true),
        includeSuspiciousActivity: Joi.boolean().default(true),
        slowRequestThreshold: Joi.number().min(0).max(60).default(1.0),
        largeResponseThreshold: Joi.number().integer().min(0).default(1048576)
      }),

      jobQuery: Joi.object({
        status: Joi.string().valid('queued', 'processing', 'completed', 'failed'),
        limit: Joi.number().integer().min(1).max(100).default(20),
        offset: Joi.number().integer().min(0).default(0)
      })
    };
  }

  /**
   * Validate analysis request parameters
   * @param {object} data - Request data to validate
   * @returns {object} Validation result
   */
  validateAnalysisRequest(data) {
    const { error, value } = this.schemas.analysisRequest.validate(data, {
      stripUnknown: true,
      abortEarly: false
    });

    if (error) {
      return {
        isValid: false,
        errors: error.details.map(detail => ({
          field: detail.path.join('.'),
          message: detail.message,
          value: detail.context.value
        }))
      };
    }

    return {
      isValid: true,
      data: value
    };
  }

  /**
   * Validate job query parameters
   * @param {object} data - Query parameters to validate
   * @returns {object} Validation result
   */
  validateJobQuery(data) {
    const { error, value } = this.schemas.jobQuery.validate(data, {
      stripUnknown: true,
      abortEarly: false
    });

    if (error) {
      return {
        isValid: false,
        errors: error.details.map(detail => ({
          field: detail.path.join('.'),
          message: detail.message
        }))
      };
    }

    return {
      isValid: true,
      data: value
    };
  }

  /**
   * Validate file upload
   * @param {object} file - Uploaded file object
   * @returns {object} Validation result
   */
  validateFileUpload(file) {
    const errors = [];

    if (!file) {
      errors.push({
        field: 'file',
        message: 'No file uploaded'
      });
      return { isValid: false, errors };
    }

    // Check file extension
    const allowedExtensions = ['.log', '.txt', '.gz'];
    const fileExtension = file.originalname.toLowerCase().split('.').pop();
    
    if (!allowedExtensions.includes(`.${fileExtension}`)) {
      errors.push({
        field: 'file.extension',
        message: `Invalid file extension. Allowed: ${allowedExtensions.join(', ')}`
      });
    }

    // Check file size (max 100MB)
    const maxSize = 100 * 1024 * 1024;
    if (file.size > maxSize) {
      errors.push({
        field: 'file.size',
        message: `File too large. Maximum size: ${this.formatBytes(maxSize)}`
      });
    }

    // Check filename
    if (file.originalname.length > 255) {
      errors.push({
        field: 'file.name',
        message: 'Filename too long (max 255 characters)'
      });
    }

    // Check for dangerous characters in filename
    const dangerousChars = /[<>:"/\\|?*\x00-\x1f]/;
    if (dangerousChars.test(file.originalname)) {
      errors.push({
        field: 'file.name',
        message: 'Filename contains invalid characters'
      });
    }

    return {
      isValid: errors.length === 0,
      errors: errors
    };
  }

  /**
   * Validate UUID format
   * @param {string} uuid - UUID string to validate
   * @returns {boolean} True if valid UUID
   */
  validateUUID(uuid) {
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    return uuidRegex.test(uuid);
  }

  /**
   * Validate IP address format
   * @param {string} ip - IP address to validate
   * @returns {boolean} True if valid IP address
   */
  validateIPAddress(ip) {
    const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
    return ipRegex.test(ip);
  }

  /**
   * Sanitize input string
   * @param {string} input - Input string to sanitize
   * @returns {string} Sanitized string
   */
  sanitizeString(input) {
    if (typeof input !== 'string') {
      return '';
    }

    return input
      .trim()
      .replace(/[<>]/g, '') // Remove potential HTML tags
      .substring(0, 1000); // Limit length
  }

  /**
   * Validate date range
   * @param {string} startDate - Start date ISO string
   * @param {string} endDate - End date ISO string
   * @returns {object} Validation result
   */
  validateDateRange(startDate, endDate) {
    const errors = [];

    try {
      const start = new Date(startDate);
      const end = new Date(endDate);

      if (isNaN(start.getTime())) {
        errors.push({
          field: 'startDate',
          message: 'Invalid start date format'
        });
      }

      if (isNaN(end.getTime())) {
        errors.push({
          field: 'endDate',
          message: 'Invalid end date format'
        });
      }

      if (errors.length === 0 && start >= end) {
        errors.push({
          field: 'dateRange',
          message: 'Start date must be before end date'
        });
      }

      // Check if date range is reasonable (not more than 1 year)
      if (errors.length === 0) {
        const oneYear = 365 * 24 * 60 * 60 * 1000;
        if (end - start > oneYear) {
          errors.push({
            field: 'dateRange',
            message: 'Date range cannot exceed 1 year'
          });
        }
      }

    } catch (error) {
      errors.push({
        field: 'dateRange',
        message: 'Invalid date format'
      });
    }

    return {
      isValid: errors.length === 0,
      errors: errors
    };
  }

  /**
   * Format bytes to human readable string
   * @param {number} bytes - Number of bytes
   * @returns {string} Formatted string
   */
  formatBytes(bytes) {
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }

    return `${size.toFixed(1)} ${units[unitIndex]}`;
  }

  /**
   * Create error response object
   * @param {string} message - Error message
   * @param {Array} details - Error details array
   * @returns {object} Error response object
   */
  createErrorResponse(message, details = []) {
    return {
      error: message,
      details: details,
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Validate request rate limiting data
   * @param {object} req - Express request object
   * @returns {object} Rate limit info
   */
  validateRateLimit(req) {
    const clientIP = req.ip || req.connection.remoteAddress;
    const userAgent = req.get('User-Agent') || 'unknown';
    
    return {
      clientIP: this.sanitizeString(clientIP),
      userAgent: this.sanitizeString(userAgent),
      timestamp: new Date().toISOString()
    };
  }
}

module.exports = RequestValidator;
