# Initial Request

## Challenge 1.1: Fix the Broken Parser 🐛

**Date**: 2025-10-16 09:39
**Files**: `python/log_parser.py`

## Problem Statement

There's a bug in the log parser that causes it to fail on certain timestamp formats. Some logs use a different timezone format (`[10/Oct/2023:13:55:36 -0500]` instead of `[10/Oct/2023:13:55:36 +0000]`).

## Your Task

1. Create a test case that reproduces the bug
2. Fix the `_parse_timestamp` method to handle both timezone formats
3. Ensure all existing tests still pass

## Expected Outcome

Parser should handle both `+0000` and `-0500` timezone formats.

## User Hypothesis

The "-" symbol is causing `parse_timestamp` to fail on certain timezone formats.

## User Strategy

- Red/Green TDD - write comprehensive tests for the issue
- Include documentation/comments
- Consider performance impact of solutions
