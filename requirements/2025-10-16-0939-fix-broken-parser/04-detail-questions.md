# Expert Detail Questions - Phase 4

## Context
After analyzing the codebase, I've discovered that Python's `%z` directive already handles negative timezones correctly. The implementation at [log_parser.py:216](python/log_parser.py#L216) successfully parses `-0500` format. This appears to be a test coverage gap rather than an implementation bug.

## Q1: Should we validate that timezone offsets are within valid ranges (-1200 to +1400)?
**Default if unknown:** Yes (prevents parsing invalid timezones like +2500 or -9999)

**Context**: Currently the parser accepts any timezone format that `strptime` can parse, including theoretically invalid offsets. Timezone offsets range from UTC-12:00 to UTC+14:00 in practice.

## Q2: Should the fallback mechanism (line 220) that strips timezone info be removed or enhanced?
**Default if unknown:** Enhanced (add explicit handling for timezone-naive formats while preserving the ability to parse them)

**Context**: The current fallback at [log_parser.py:220](python/log_parser.py#L220) silently strips timezone data and returns timezone-naive datetime. This could cause issues when mixing timezone-aware and naive datetimes.

## Q3: Should we add explicit documentation/comments explaining timezone handling in the `_parse_timestamp` method?
**Default if unknown:** Yes (improves code maintainability and helps future developers understand the implementation)

**Context**: The current docstring (line 213) only says "Parse Apache timestamp format" without explaining timezone handling, fallback behavior, or supported formats.

## Q4: Should test cases use `@pytest.mark.parametrize` to cover multiple timezone variations efficiently?
**Default if unknown:** Yes (matches existing pattern at test_log_parser.py:289 and provides better test coverage)

**Context**: Following the pattern from `test_various_status_codes` at [test_log_parser.py:289-296](tests/test_log_parser.py#L289-L296) would allow testing multiple timezone formats efficiently.

## Q5: Should we add performance benchmarks to verify no regression when adding new test coverage?
**Default if unknown:** No (this is a test addition, not an optimization task, and current performance is adequate)

**Context**: While the challenge mentions "consider performance impact", we're primarily adding test coverage. Benchmark infrastructure would be valuable but may be out of scope for this specific challenge.
