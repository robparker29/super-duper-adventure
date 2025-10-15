/**
 * Test suite for log processor module.
 * 
 * Tests Python integration, file processing, and error handling.
 */

const LogProcessor = require('../processor');
const fs = require('fs').promises;
const path = require('path');

describe('LogProcessor', () => {
  let processor;
  
  beforeEach(() => {
    processor = new LogProcessor();
  });

  describe('constructor', () => {
    test('should initialize with default values', () => {
      expect(processor.pythonPath).toBeDefined();
      expect(processor.scriptPath).toBeDefined();
    });

    test('should use environment variable for python path', () => {
      const originalPath = process.env.PYTHON_PATH;
      process.env.PYTHON_PATH = '/custom/python';
      
      const customProcessor = new LogProcessor();
      expect(customProcessor.pythonPath).toBe('/custom/python');
      
      // Restore original value
      if (originalPath) {
        process.env.PYTHON_PATH = originalPath;
      } else {
        delete process.env.PYTHON_PATH;
      }
    });
  });

  describe('generatePythonScript', () => {
    test('should generate valid Python script with default options', () => {
      const script = processor.generatePythonScript('/test/file.log', {});
      
      expect(script).toContain('import sys');
      expect(script).toContain('from log_parser import LogParser');
      expect(script).toContain('from analytics import LogAnalytics');
      expect(script).toContain("'/test/file.log'");
      expect(script).toContain('strict_mode=false');
      expect(script).toContain('top_n=10');
    });

    test('should generate script with custom options', () => {
      const options = {
        strictMode: true,
        topN: 20
      };
      
      const script = processor.generatePythonScript('/test/file.log', options);
      
      expect(script).toContain('strict_mode=true');
      expect(script).toContain('top_n=20');
    });

    test('should handle special characters in file path', () => {
      const specialPath = "/test/file with spaces & symbols.log";
      const script = processor.generatePythonScript(specialPath, {});
      
      expect(script).toContain(specialPath);
    });
  });

  describe('validateLogFile', () => {
    let tempFile;

    beforeEach(async () => {
      // Create a temporary file for testing
      tempFile = path.join(__dirname, 'temp_test.log');
      await fs.writeFile(tempFile, 'test log content\nline 2\nline 3');
    });

    afterEach(async () => {
      // Clean up temporary file
      try {
        await fs.unlink(tempFile);
      } catch (err) {
        // File might not exist, ignore error
      }
    });

    test('should validate existing file successfully', async () => {
      const result = await processor.validateLogFile(tempFile);
      
      expect(result.isValid).toBe(true);
      expect(result.fileSize).toBeGreaterThan(0);
      expect(result.sampleLines).toHaveLength(3);
      expect(result.estimatedLines).toBeGreaterThan(0);
    });

    test('should reject non-existent file', async () => {
      const result = await processor.validateLogFile('/non/existent/file.log');
      
      expect(result.isValid).toBe(false);
      expect(result.error).toBeDefined();
    });

    test('should reject file that is too large', async () => {
      // Mock a large file by creating a file with large stats
      const largeTempFile = path.join(__dirname, 'large_test.log');
      
      // Create file with content
      await fs.writeFile(largeTempFile, 'test');
      
      // Mock fs.stat to return large size
      const originalStat = fs.stat;
      fs.stat = jest.fn().mockResolvedValue({
        size: 200 * 1024 * 1024 // 200MB
      });

      try {
        const result = await processor.validateLogFile(largeTempFile);
        expect(result.isValid).toBe(false);
        expect(result.error).toContain('too large');
      } finally {
        // Restore original fs.stat
        fs.stat = originalStat;
        await fs.unlink(largeTempFile);
      }
    });

    test('should handle empty file', async () => {
      const emptyFile = path.join(__dirname, 'empty_test.log');
      await fs.writeFile(emptyFile, '');
      
      try {
        const result = await processor.validateLogFile(emptyFile);
        expect(result.isValid).toBe(false);
        expect(result.error).toContain('empty');
      } finally {
        await fs.unlink(emptyFile);
      }
    });
  });

  describe('estimateLineCount', () => {
    test('should estimate line count correctly', () => {
      const sample = 'line1\nline2\nline3\n';
      const fileSize = 1000;
      
      const estimate = processor.estimateLineCount(fileSize, sample);
      
      expect(estimate).toBeGreaterThan(0);
      expect(typeof estimate).toBe('number');
    });

    test('should handle single line sample', () => {
      const sample = 'single line';
      const fileSize = 100;
      
      const estimate = processor.estimateLineCount(fileSize, sample);
      
      expect(estimate).toBeGreaterThan(0);
    });
  });

  describe('getStats', () => {
    test('should return processor statistics', () => {
      const stats = processor.getStats();
      
      expect(stats.pythonPath).toBeDefined();
      expect(stats.scriptPath).toBeDefined();
      expect(stats.timestamp).toBeDefined();
      expect(new Date(stats.timestamp)).toBeInstanceOf(Date);
    });
  });

  describe('processLogFile', () => {
    test('should throw error for non-existent file', async () => {
      await expect(
        processor.processLogFile('/non/existent/file.log')
      ).rejects.toThrow('Failed to process log file');
    });

    // Note: Testing actual Python integration would require a real Python environment
    // In a real test suite, you might mock the spawn process or use test doubles
  });

  describe('callPythonAnalyzer', () => {
    test('should handle Python process timeout', async () => {
      // Mock spawn to simulate a hanging process
      const originalSpawn = require('child_process').spawn;
      const mockSpawn = jest.fn().mockImplementation(() => {
        const mockProcess = {
          stdout: { on: jest.fn() },
          stderr: { on: jest.fn() },
          on: jest.fn((event, callback) => {
            if (event === 'error') {
              // Don't call the callback to simulate hanging
            }
          }),
          kill: jest.fn()
        };
        return mockProcess;
      });

      require('child_process').spawn = mockSpawn;

      try {
        // This should timeout quickly in test environment
        await expect(
          processor.callPythonAnalyzer('/test/file.log', {})
        ).rejects.toThrow('timed out');
      } finally {
        // Restore original spawn
        require('child_process').spawn = originalSpawn;
      }
    }, 10000); // Increase timeout for this test

    test('should handle Python process failure', async () => {
      // Mock spawn to simulate process failure
      const originalSpawn = require('child_process').spawn;
      const mockSpawn = jest.fn().mockImplementation(() => {
        const mockProcess = {
          stdout: { on: jest.fn() },
          stderr: { 
            on: jest.fn((event, callback) => {
              if (event === 'data') {
                callback('Python error occurred');
              }
            })
          },
          on: jest.fn((event, callback) => {
            if (event === 'close') {
              callback(1); // Exit code 1 (failure)
            }
          }),
          kill: jest.fn()
        };
        return mockProcess;
      });

      require('child_process').spawn = mockSpawn;

      try {
        await expect(
          processor.callPythonAnalyzer('/test/file.log', {})
        ).rejects.toThrow('Python process failed');
      } finally {
        // Restore original spawn
        require('child_process').spawn = originalSpawn;
      }
    });

    test('should handle invalid JSON response', async () => {
      // Mock spawn to return invalid JSON
      const originalSpawn = require('child_process').spawn;
      const mockSpawn = jest.fn().mockImplementation(() => {
        const mockProcess = {
          stdout: { 
            on: jest.fn((event, callback) => {
              if (event === 'data') {
                callback('invalid json response');
              }
            })
          },
          stderr: { on: jest.fn() },
          on: jest.fn((event, callback) => {
            if (event === 'close') {
              callback(0); // Success exit code
            }
          }),
          kill: jest.fn()
        };
        return mockProcess;
      });

      require('child_process').spawn = mockSpawn;

      try {
        await expect(
          processor.callPythonAnalyzer('/test/file.log', {})
        ).rejects.toThrow('Failed to parse Python output');
      } finally {
        // Restore original spawn
        require('child_process').spawn = originalSpawn;
      }
    });

    test('should handle successful Python execution', async () => {
      // Mock spawn to return valid JSON
      const mockResult = {
        report: { total_requests: 100 },
        parsing_stats: { parsed_count: 95, error_count: 5 }
      };

      const originalSpawn = require('child_process').spawn;
      const mockSpawn = jest.fn().mockImplementation(() => {
        const mockProcess = {
          stdout: { 
            on: jest.fn((event, callback) => {
              if (event === 'data') {
                callback(JSON.stringify(mockResult));
              }
            })
          },
          stderr: { on: jest.fn() },
          on: jest.fn((event, callback) => {
            if (event === 'close') {
              callback(0); // Success exit code
            }
          }),
          kill: jest.fn()
        };
        return mockProcess;
      });

      require('child_process').spawn = mockSpawn;

      try {
        const result = await processor.callPythonAnalyzer('/test/file.log', {});
        expect(result).toEqual(mockResult);
      } finally {
        // Restore original spawn
        require('child_process').spawn = originalSpawn;
      }
    });
  });

  describe('edge cases', () => {
    test('should handle empty options object', () => {
      const script = processor.generatePythonScript('/test/file.log', {});
      expect(script).toContain('strict_mode=false');
      expect(script).toContain('top_n=10');
    });

    test('should handle undefined options', () => {
      const script = processor.generatePythonScript('/test/file.log', undefined);
      expect(script).toContain('strict_mode=false');
      expect(script).toContain('top_n=10');
    });

    test('should handle partial options', () => {
      const options = { strictMode: true };
      const script = processor.generatePythonScript('/test/file.log', options);
      
      expect(script).toContain('strict_mode=true');
      expect(script).toContain('top_n=10'); // Should use default
    });
  });
});

describe('LogProcessor Integration', () => {
  test('should handle file processing workflow', async () => {
    const processor = new LogProcessor();
    
    // Create a temporary log file
    const tempFile = path.join(__dirname, 'integration_test.log');
    const logContent = `127.0.0.1 - - [10/Oct/2023:13:55:36 +0000] "GET /test HTTP/1.1" 200 1234
192.168.1.100 - - [10/Oct/2023:13:56:15 +0000] "POST /login HTTP/1.1" 401 0`;
    
    await fs.writeFile(tempFile, logContent);
    
    try {
      // Validate file
      const validation = await processor.validateLogFile(tempFile);
      expect(validation.isValid).toBe(true);
      expect(validation.sampleLines).toHaveLength(2);
      
      // Check estimated line count
      expect(validation.estimatedLines).toBeCloseTo(2, 0);
      
    } finally {
      // Clean up
      await fs.unlink(tempFile);
    }
  });
});
