"""
Jarvis Failover & Benchmark Settings
====================================
Timeout thresholds, payload settings, and error status codes for classification.
"""

# Latency scanning settings
BENCHMARK_TIMEOUT_SECONDS = 15.0
PING_PROMPT = "ping"
MAX_MODELS_PER_KEY = 3

# Rate limit / Quota / Exhausted errors (HTTP status codes or substrings in error messages)
RATE_LIMIT_STATUS_CODES = {429}
RATE_LIMIT_ERROR_SUBSTRINGS = {
    "quota",
    "rate limit",
    "rate_limit",
    "exhausted",
    "too many requests",
    "limit exceeded",
    "resource_exhausted",
    "insufficient_quota",
    "billing",
    "balance",
    "credit"
}

# Transient / Model engine errors (HTTP status codes or substrings in error messages)
TRANSIENT_STATUS_CODES = {500, 502, 503, 504}
TRANSIENT_ERROR_SUBSTRINGS = {
    "overloaded",
    "timeout",
    "connection",
    "internal server error",
    "service unavailable",
    "unavailable",
    "try again",
    "temporary",
    "server error"
}
