/**
 * Test suite for request validator module.
 * 
 * Tests validation logic, error handling, and edge cases.
 */

const RequestValidator = require('../validator');

describe('RequestValidator', () => {
  let validator;
  
  beforeEach(() => {
    validator = new RequestValidator();
  });

  describe('constructor', () => {
    test('should initialize schemas correctly', () => {
      expect(validator.schemas).toBeDefined();
      expect(validator.schemas.analysisRequest).toBeDefined();
      expect(validator.schemas.jobQuery).toBeDefined();
    });
  });

  describe('validateAnalysisRequest', () => {
    test('should validate valid request with default values', () => {
      const result = validator.validateAnalysisRequest({});
      
      expect(result.isValid).toBe(true);
      expect(result.data.strictMode).toBe(false);
      expect(result.data.topN).toBe(10);
      expect(result.data.includePerformanceMetrics).toBe(true);
      expect(result.data.includeSuspiciousActivity).toBe(true);
      expect(result.data.slowRequestThreshold).toBe(1.0);
      expect(result.data.largeResponseThreshold).toBe(1048576);
    });

    test('should validate valid request with custom values', () => {
      const requestData = {
        strictMode: true,
        topN: 20,
        includePerformanceMetrics: false,
        includeSuspiciousActivity: false,
        slowRequestThreshold: 2.5,
        largeResponseThreshold: 2097152
      };
      
      const result = validator.validateAnalysisRequest(requestData);
      
      expect(result.isValid).toBe(true);
      expect(result.data).toEqual(requestData);
    });

    test('should reject invalid topN values', () => {
      const invalidCases = [
        { topN: 0 },
        { topN: -1 },
        { topN: 101 },
        { topN: 'invalid' }
      ];

      invalidCases.forEach(testCase => {
        const result = validator.validateAnalysisRequest(testCase);
        expect(result.isValid).toBe(false);
        expect(result.errors).toBeDefined();
        expect(result.errors.some(e => e.field === 'topN')).toBe(true);
      });
    });

    test('should reject invalid threshold values', () => {
      const invalidCases = [
        { slowRequestThreshold: -1 },
        { slowRequestThreshold: 61 },
        { largeResponseThreshold: -1 }
      ];

      invalidCases.forEach(testCase => {
        const result = validator.validateAnalysisRequest(testCase);
        expect(result.isValid).toBe(false);
        expect(result.errors).toBeDefined();
      });
    });

    test('should strip unknown properties', () => {
      const requestData = {
        strictMode: true,
        unknownProperty: 'should be removed',
        anotherUnknown: 123
      };
      
      const result = validator.validateAnalysisRequest(requestData);
      
      expect(result.isValid).toBe(true);
      expect(result.data.unknownProperty).toBeUndefined();
      expect(result.data.anotherUnknown).toBeUndefined();
      expect(result.data.strictMode).toBe(true);
    });

    test('should provide detailed error messages', () => {
      const invalidData = {
        strictMode: 'not a boolean',
        topN: 'not a number',
        slowRequestThreshold: 'not a number'
      };
      
      const result = validator.validateAnalysisRequest(invalidData);
      
      expect(result.isValid).toBe(false);
      expect(result.errors).toHaveLength(3);
      
      const errorFields = result.errors.map(e => e.field);
      expect(errorFields).toContain('strictMode');
      expect(errorFields).toContain('topN');
      expect(errorFields).toContain('slowRequestThreshold');
    });
  });

  describe('validateJobQuery', () => {
    test('should validate valid query with default values', () => {
      const result = validator.validateJobQuery({});
      
      expect(result.isValid).toBe(true);
      expect(result.data.limit).toBe(20);
      expect(result.data.offset).toBe(0);
    });

    test('should validate valid query with custom values', () => {
      const queryData = {
        status: 'completed',
        limit: 50,
        offset: 10
      };
      
      const result = validator.validateJobQuery(queryData);
      
      expect(result.isValid).toBe(true);
      expect(result.data).toEqual(queryData);
    });

    test('should reject invalid status values', () => {
      const invalidStatus = { status: 'invalid_status' };
      
      const result = validator.validateJobQuery(invalidStatus);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.some(e => e.field === 'status')).toBe(true);
    });

    test('should validate all valid status values', () => {
      const validStatuses = ['queued', 'processing', 'completed', 'failed'];
      
      validStatuses.forEach(status => {
        const result = validator.validateJobQuery({ status });
        expect(result.isValid).toBe(true);
        expect(result.data.status).toBe(status);
      });
    });

    test('should reject invalid limit and offset values', () => {
      const invalidCases = [
        { limit: 0 },
        { limit: 101 },
        { limit: -1 },
        { offset: -1 }
      ];

      invalidCases.forEach(testCase => {
        const result = validator.validateJobQuery(testCase);
        expect(result.isValid).toBe(false);
      });
    });
  });

  describe('validateFileUpload', () => {
    test('should reject missing file', () => {
      const result = validator.validateFileUpload(null);
      
      expect(result.isValid).toBe(false);
      expect(result.errors).toHaveLength(1);
      expect(result.errors[0].field).toBe('file');
    });

    test('should validate acceptable file extensions', () => {
      const validFiles = [
        { originalname: 'test.log', size: 1000 },
        { originalname: 'test.txt', size: 1000 },
        { originalname: 'test.gz', size: 1000 },
        { originalname: 'access.LOG', size: 1000 }, // Case insensitive
      ];

      validFiles.forEach(file => {
        const result = validator.validateFileUpload(file);
        expect(result.isValid).toBe(true);
      });
    });

    test('should reject invalid file extensions', () => {
      const invalidFiles = [
        { originalname: 'test.pdf', size: 1000 },
        { originalname: 'test.exe', size: 1000 },
        { originalname: 'test', size: 1000 }, // No extension
      ];

      invalidFiles.forEach(file => {
        const result = validator.validateFileUpload(file);
        expect(result.isValid).toBe(false);
        expect(result.errors.some(e => e.field === 'file.extension')).toBe(true);
      });
    });

    test('should reject files that are too large', () => {
      const largeFile = {
        originalname: 'large.log',
        size: 200 * 1024 * 1024 // 200MB
      };
      
      const result = validator.validateFileUpload(largeFile);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.some(e => e.field === 'file.size')).toBe(true);
    });

    test('should reject filenames that are too long', () => {
      const longFilename = 'a'.repeat(300) + '.log';
      const file = {
        originalname: longFilename,
        size: 1000
      };
      
      const result = validator.validateFileUpload(file);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.some(e => e.field === 'file.name')).toBe(true);
    });

    test('should reject filenames with dangerous characters', () => {
      const dangerousFilenames = [
        '<script>.log',
        'test>.log',
        'test?.log',
        'test*.log',
        'test|.log'
      ];

      dangerousFilenames.forEach(filename => {
        const file = { originalname: filename, size: 1000 };
        const result = validator.validateFileUpload(file);
        expect(result.isValid).toBe(false);
        expect(result.errors.some(e => e.field === 'file.name')).toBe(true);
      });
    });

    test('should handle multiple validation errors', () => {
      const badFile = {
        originalname: '<dangerous>.pdf', // Bad extension and dangerous chars
        size: 200 * 1024 * 1024 // Too large
      };
      
      const result = validator.validateFileUpload(badFile);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(1);
    });
  });

  describe('validateUUID', () => {
    test('should validate correct UUID formats', () => {
      const validUUIDs = [
        '123e4567-e89b-12d3-a456-426614174000',
        'A123E567-E89B-12D3-A456-426614174000', // Uppercase
        '550e8400-e29b-41d4-a716-446655440000'
      ];

      validUUIDs.forEach(uuid => {
        expect(validator.validateUUID(uuid)).toBe(true);
      });
    });

    test('should reject invalid UUID formats', () => {
      const invalidUUIDs = [
        '123e4567-e89b-12d3-a456-42661417400', // Too short
        '123e4567-e89b-12d3-a456-4266141740000', // Too long
        '123e4567-e89b-12d3-a456-42661417400g', // Invalid character
        '123e4567-e89b-12d3-a456', // Missing parts
        'not-a-uuid-at-all',
        ''
      ];

      invalidUUIDs.forEach(uuid => {
        expect(validator.validateUUID(uuid)).toBe(false);
      });
    });
  });

  describe('validateIPAddress', () => {
    test('should validate correct IP addresses', () => {
      const validIPs = [
        '127.0.0.1',
        '192.168.1.1',
        '10.0.0.1',
        '255.255.255.255',
        '0.0.0.0'
      ];

      validIPs.forEach(ip => {
        expect(validator.validateIPAddress(ip)).toBe(true);
      });
    });

    test('should reject invalid IP addresses', () => {
      const invalidIPs = [
        '256.1.1.1', // Out of range
        '192.168.1', // Incomplete
        '192.168.1.1.1', // Too many parts
        'not.an.ip.address',
        '192.168.-1.1', // Negative number
        '',
        'localhost'
      ];

      invalidIPs.forEach(ip => {
        expect(validator.validateIPAddress(ip)).toBe(false);
      });
    });
  });

  describe('sanitizeString', () => {
    test('should remove HTML tags and trim whitespace', () => {
      const input = '  <script>alert("xss")</script>  ';
      const result = validator.sanitizeString(input);
      
      expect(result).toBe('alert("xss")');
    });

    test('should limit string length', () => {
      const longString = 'a'.repeat(2000);
      const result = validator.sanitizeString(longString);
      
      expect(result.length).toBe(1000);
    });

    test('should handle non-string input', () => {
      expect(validator.sanitizeString(null)).toBe('');
      expect(validator.sanitizeString(undefined)).toBe('');
      expect(validator.sanitizeString(123)).toBe('');
      expect(validator.sanitizeString({})).toBe('');
    });

    test('should preserve valid content', () => {
      const input = 'Valid log content with numbers 123 and symbols @#$';
      const result = validator.sanitizeString(input);
      
      expect(result).toBe(input);
    });
  });

  describe('validateDateRange', () => {
    test('should validate correct date range', () => {
      const startDate = '2023-01-01T00:00:00Z';
      const endDate = '2023-01-02T00:00:00Z';
      
      const result = validator.validateDateRange(startDate, endDate);
      
      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    test('should reject invalid date formats', () => {
      const invalidDates = [
        ['invalid-date', '2023-01-02T00:00:00Z'],
        ['2023-01-01T00:00:00Z', 'invalid-date'],
        ['not-a-date', 'also-not-a-date']
      ];

      invalidDates.forEach(([start, end]) => {
        const result = validator.validateDateRange(start, end);
        expect(result.isValid).toBe(false);
      });
    });

    test('should reject start date after end date', () => {
      const startDate = '2023-01-02T00:00:00Z';
      const endDate = '2023-01-01T00:00:00Z';
      
      const result = validator.validateDateRange(startDate, endDate);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.some(e => e.field === 'dateRange')).toBe(true);
    });

    test('should reject date range longer than one year', () => {
      const startDate = '2023-01-01T00:00:00Z';
      const endDate = '2025-01-01T00:00:00Z'; // More than 1 year
      
      const result = validator.validateDateRange(startDate, endDate);
      
      expect(result.isValid).toBe(false);
      expect(result.errors.some(e => e.message.includes('1 year'))).toBe(true);
    });
  });

  describe('formatBytes', () => {
    test('should format bytes correctly', () => {
      expect(validator.formatBytes(0)).toBe('0.0 B');
      expect(validator.formatBytes(512)).toBe('512.0 B');
      expect(validator.formatBytes(1024)).toBe('1.0 KB');
      expect(validator.formatBytes(1536)).toBe('1.5 KB');
      expect(validator.formatBytes(1048576)).toBe('1.0 MB');
      expect(validator.formatBytes(1073741824)).toBe('1.0 GB');
    });

    test('should handle large numbers', () => {
      const result = validator.formatBytes(1099511627776); // 1 TB
      expect(result).toContain('TB');
    });
  });

  describe('createErrorResponse', () => {
    test('should create error response with message only', () => {
      const response = validator.createErrorResponse('Test error');
      
      expect(response.error).toBe('Test error');
      expect(response.details).toEqual([]);
      expect(response.timestamp).toBeDefined();
      expect(new Date(response.timestamp)).toBeInstanceOf(Date);
    });

    test('should create error response with details', () => {
      const details = [
        { field: 'test', message: 'Test detail' }
      ];
      const response = validator.createErrorResponse('Test error', details);
      
      expect(response.error).toBe('Test error');
      expect(response.details).toEqual(details);
    });
  });

  describe('validateRateLimit', () => {
    test('should extract and sanitize client information', () => {
      const mockReq = {
        ip: '192.168.1.100',
        get: jest.fn().mockReturnValue('Mozilla/5.0 Test Browser')
      };
      
      const result = validator.validateRateLimit(mockReq);
      
      expect(result.clientIP).toBe('192.168.1.100');
      expect(result.userAgent).toBe('Mozilla/5.0 Test Browser');
      expect(result.timestamp).toBeDefined();
    });

    test('should handle missing IP and user agent', () => {
      const mockReq = {
        connection: { remoteAddress: '10.0.0.1' },
        get: jest.fn().mockReturnValue(undefined)
      };
      
      const result = validator.validateRateLimit(mockReq);
      
      expect(result.clientIP).toBe('10.0.0.1');
      expect(result.userAgent).toBe('unknown');
    });

    test('should sanitize malicious input', () => {
      const mockReq = {
        ip: '<script>alert("xss")</script>',
        get: jest.fn().mockReturnValue('<iframe>evil</iframe>')
      };
      
      const result = validator.validateRateLimit(mockReq);
      
      expect(result.clientIP).not.toContain('<script>');
      expect(result.userAgent).not.toContain('<iframe>');
    });
  });

  describe('edge cases and error handling', () => {
    test('should handle null and undefined inputs gracefully', () => {
      expect(validator.validateAnalysisRequest(null).isValid).toBe(true);
      expect(validator.validateJobQuery(undefined).isValid).toBe(true);
      expect(validator.validateFileUpload(undefined).isValid).toBe(false);
    });

    test('should handle empty objects', () => {
      expect(validator.validateAnalysisRequest({}).isValid).toBe(true);
      expect(validator.validateJobQuery({}).isValid).toBe(true);
    });

    test('should handle extremely large numbers', () => {
      const result = validator.validateAnalysisRequest({
        topN: Number.MAX_SAFE_INTEGER
      });
      expect(result.isValid).toBe(false);
    });
  });
});
