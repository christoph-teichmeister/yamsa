class ImportParseError(Exception):
    """Raised when a file cannot be parsed at all — as opposed to single rows being skipped."""
