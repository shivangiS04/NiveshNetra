class ParseError(Exception):
    """Raised when a PDF cannot be parsed as a CAMS statement."""


class XIRRError(Exception):
    """Raised when XIRR computation fails to converge."""
