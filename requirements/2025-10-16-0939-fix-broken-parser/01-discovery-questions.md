# Discovery Questions - Phase 2

## Context Found
After analyzing the codebase, I've identified:
- The `_parse_timestamp` method at [log_parser.py:212-222](python/log_parser.py#L212-L222) uses `datetime.strptime` with `%z` directive
- Current implementation expects format: `dd/Mon/YYYY:HH:MM:SS +ZZZZ`
- Existing tests at [test_log_parser.py:236-247](tests/test_log_parser.py#L236-L247) only test `+0000` timezone
- The issue: negative timezone offsets like `-0500` should work with `%z`, so the bug might be elsewhere

## Q1: Should the parser handle timezone-naive timestamps (no timezone at all)?
**Default if unknown:** Yes (better to support logs from various sources with fallback handling)

Your hypothesis suggests the "-" symbol is causing issues, but Python's `%z` directive should handle both `+` and `-` timezone offsets. The current fallback mechanism (lines 218-220) strips timezone info entirely but doesn't handle negative offsets specifically.

## Q2: Should the parser preserve timezone information in the parsed datetime objects?
**Default if unknown:** Yes (timezone-aware datetime objects prevent ambiguity and are best practice)

Currently the parser uses `%z` which creates timezone-aware datetime objects. If we need to support multiple formats, we should maintain this behavior for consistency.

## Q3: Will log files contain mixed timezone formats within the same file?
**Default if unknown:** Yes (real-world logs often contain mixed formats from different sources or time periods)

This affects whether we need to try multiple parsing strategies per timestamp or can detect the format once per file.

## Q4: Should the parser support additional timestamp formats beyond Apache Common Log Format?
**Default if unknown:** No (based on docstrings and patterns, parser is specifically designed for Apache/CLF formats)

The parser explicitly targets Common Log Format, Combined Log Format, and Extended formats. Expanding beyond this scope would require additional requirements.

## Q5: Is performance a critical concern when parsing timestamps (e.g., processing millions of log entries)?
**Default if unknown:** Yes (given the streaming implementation and memory-efficiency focus in the docstrings)

The codebase shows clear performance awareness (streaming parsers at line 76, memory-efficient processing). Any fix should avoid significant performance degradation like excessive try/except blocks.
