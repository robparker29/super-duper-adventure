/**
 * Log processor module that interfaces with Python analysis engine.
 * 
 * Handles communication between JavaScript API and Python log analysis components.
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs').promises;

class LogProcessor {
  constructor() {
    this.pythonPath = process.env.PYTHON_PATH || 'python3';
    this.scriptPath = path.join(__dirname, '..', 'python');
  }

  /**
   * Process log file using Python analysis engine
   * @param {string} filePath - Path to log file
   * @param {object} options - Processing options
   * @returns {Promise<object>} Analysis results
   */
  async processLogFile(filePath, options = {}) {
    try {
      // Validate file exists
      await fs.access(filePath);

      const result = await this.callPythonAnalyzer(filePath, options);
      
      // Clean up uploaded file after processing
      try {
        await fs.unlink(filePath);
      } catch (err) {
        console.warn('Could not clean up uploaded file:', err.message);
      }

      return result;

    } catch (error) {
      throw new Error(`Failed to process log file: ${error.message}`);
    }
  }

  /**
   * Call Python analysis script
   * @param {string} filePath - Path to log file
   * @param {object} options - Analysis options
   * @returns {Promise<object>} Analysis results
   */
  async callPythonAnalyzer(filePath, options) {
    return new Promise((resolve, reject) => {
      const args = [
        '-c',
        this.generatePythonScript(filePath, options)
      ];

      const pythonProcess = spawn(this.pythonPath, args, {
        cwd: this.scriptPath,
        stdio: ['pipe', 'pipe', 'pipe']
      });

      let stdout = '';
      let stderr = '';

      pythonProcess.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      pythonProcess.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      pythonProcess.on('close', (code) => {
        if (code !== 0) {
          reject(new Error(`Python process failed with code ${code}: ${stderr}`));
          return;
        }

        try {
          const result = JSON.parse(stdout);
          resolve(result);
        } catch (error) {
          reject(new Error(`Failed to parse Python output: ${error.message}`));
        }
      });

      pythonProcess.on('error', (error) => {
        reject(new Error(`Failed to start Python process: ${error.message}`));
      });

      // Set timeout
      setTimeout(() => {
        pythonProcess.kill();
        reject(new Error('Python process timed out'));
      }, 300000); // 5 minutes timeout
    });
  }

  /**
   * Generate Python script for analysis
   * @param {string} filePath - Path to log file
   * @param {object} options - Analysis options
   * @returns {string} Python script
   */
  generatePythonScript(filePath, options) {
    const strictMode = options.strictMode || false;
    const topN = options.topN || 10;

    return `
import sys
import json
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from log_parser import LogParser
from analytics import LogAnalytics
from utils import format_bytes

def main():
    try:
        # Parse log file
        parser = LogParser(strict_mode=${strictMode})
        log_entries = parser.parse_file('${filePath}')
        
        # Generate analytics
        analytics = LogAnalytics(log_entries)
        report = analytics.generate_report(top_n=${topN})
        
        # Get parsing stats
        parsing_stats = parser.get_parsing_stats()
        
        # Get performance metrics
        performance_metrics = analytics.calculate_performance_metrics()
        
        # Get suspicious activity
        suspicious_activity = analytics.detect_suspicious_activity()
        
        # Format response
        result = {
            'report': report.to_dict(),
            'parsing_stats': parsing_stats,
            'performance_metrics': performance_metrics,
            'suspicious_activity': suspicious_activity,
            'file_info': {
                'total_entries': len(log_entries),
                'processed_successfully': parsing_stats['parsed_count'],
                'processing_errors': parsing_stats['error_count']
            }
        }
        
        print(json.dumps(result, default=str))
        
    except Exception as e:
        error_result = {
            'error': str(e),
            'type': type(e).__name__
        }
        print(json.dumps(error_result))
        sys.exit(1)

if __name__ == '__main__':
    main()
`;
  }

  /**
   * Validate log file format
   * @param {string} filePath - Path to log file
   * @returns {Promise<object>} Validation results
   */
  async validateLogFile(filePath) {
    try {
      const stats = await fs.stat(filePath);
      
      // Check file size (max 100MB)
      const maxSize = 100 * 1024 * 1024;
      if (stats.size > maxSize) {
        throw new Error(`File too large: ${stats.size} bytes (max: ${maxSize} bytes)`);
      }

      // Check if file is readable
      await fs.access(filePath, fs.constants.R_OK);

      // Sample first few lines to check format
      const fileHandle = await fs.open(filePath, 'r');
      const buffer = Buffer.alloc(1024);
      const { bytesRead } = await fileHandle.read(buffer, 0, 1024, 0);
      await fileHandle.close();

      const sample = buffer.slice(0, bytesRead).toString();
      const lines = sample.split('\n').filter(line => line.trim());

      if (lines.length === 0) {
        throw new Error('File appears to be empty');
      }

      return {
        isValid: true,
        fileSize: stats.size,
        sampleLines: lines.slice(0, 3),
        estimatedLines: this.estimateLineCount(stats.size, sample)
      };

    } catch (error) {
      return {
        isValid: false,
        error: error.message
      };
    }
  }

  /**
   * Estimate number of lines in file
   * @param {number} fileSize - File size in bytes
   * @param {string} sample - Sample text from file
   * @returns {number} Estimated line count
   */
  estimateLineCount(fileSize, sample) {
    const lines = sample.split('\n');
    const avgLineLength = sample.length / lines.length;
    return Math.round(fileSize / avgLineLength);
  }

  /**
   * Get processing statistics
   * @returns {object} Current processing stats
   */
  getStats() {
    return {
      pythonPath: this.pythonPath,
      scriptPath: this.scriptPath,
      timestamp: new Date().toISOString()
    };
  }
}

module.exports = LogProcessor;
