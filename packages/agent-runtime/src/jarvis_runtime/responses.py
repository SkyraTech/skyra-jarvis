"""Shared strict response boundaries for structured agent requests."""
import json


class IncompleteResponse(ValueError):
    """A completed provider response without an acceptable final answer; never raw text."""
    def __init__(self, *, output_limited=False, usage=None):
        super().__init__('Incomplete model response')
        self.failure = 'provider_output_limit' if output_limited else 'provider_incomplete_response'
        try:
            self.usage = dict(validate_usage(usage)) if usage is not None else None
        except ValueError:
            self.usage = None


def failure_usage(exc):
    if not isinstance(exc, IncompleteResponse) or exc.usage is None: return None
    try: return validate_usage(exc.usage)
    except ValueError: return None

VALIDATION_CODES = {
    'Invalid response size': 'response_size',
    'Duplicate response key': 'duplicate_json_key',
    'Invalid JSON constant': 'nonfinite_json',
    'Response object required': 'response_object',
    'Invalid usage metadata': 'usage_metadata',
    'Invalid repair response': 'response_shape',
    'Invalid response shape': 'response_shape',
    'Invalid model patch': 'patch_shape',
    'Patch violates selected context': 'patch_context_mismatch',
    'Patch target absent from context': 'patch_unselected_path',
    'Patch target is protected': 'patch_protected_path',
    'Duplicate patch target': 'patch_duplicate_path',
    'Overlapping patch ranges': 'patch_overlap',
    'Patch text exceeds bounds': 'patch_text_bounds',
    'Combined patch text exceeds bounds': 'patch_combined_text_bounds',
    'Patch input hash differs': 'patch_hash_mismatch',
    'Patch old text is not unique': 'patch_old_text_mismatch',
    'Patch contains no change': 'patch_no_change',
    'Invalid new-file proposal': 'creation_shape',
    'Invalid response text': 'text_bounds',
    'Invalid response list': 'list_bounds',
    'Invalid plan': 'plan_shape',
    'Invalid plan phases': 'plan_phases',
    'Invalid plan phase': 'plan_phase',
}


def validation_code(exc):
    if isinstance(exc, json.JSONDecodeError): return 'invalid_json'
    return VALIDATION_CODES.get(str(exc), 'response_validation')


def validation_failure(core, project, subject, prefix):
    row = core.db.execute('SELECT kind FROM events WHERE project=? AND subject=? AND kind LIKE ? ORDER BY id DESC LIMIT 1',
                          (project, subject, prefix+'.validation_%')).fetchone()
    if row is None: return None
    code = row['kind'].removeprefix(prefix+'.validation_')
    return code if code in {*VALIDATION_CODES.values(), 'invalid_json', 'response_validation'} else None


def parse_object(text, maximum_bytes):
    if not isinstance(text, str) or len(text.encode()) > maximum_bytes:
        raise ValueError('Invalid response size')
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result: raise ValueError('Duplicate response key')
            result[key] = value
        return result
    def invalid(_):
        raise ValueError('Invalid JSON constant')
    result = json.loads(text, object_pairs_hook=pairs, parse_constant=invalid)
    if not isinstance(result, dict): raise ValueError('Response object required')
    return result


def validate_usage(usage):
    if (not isinstance(usage, dict) or set(usage) - {'input_tokens', 'output_tokens', 'total_tokens', 'reasoning_tokens'}
            or any(type(value) is not int or not 0 <= value <= 100000000 for value in usage.values())):
        raise ValueError('Invalid usage metadata')
    return usage


def failure_code(exc, fallback, *, provider_failure=False):
    if provider_failure:
        if isinstance(exc, (TimeoutError, ConnectionError)):
            return 'provider_timeout' if isinstance(exc, TimeoutError) else 'provider_connection_failed'
        try:
            import httpx
            if isinstance(exc, httpx.TimeoutException): return 'provider_timeout'
            if isinstance(exc, httpx.NetworkError): return 'provider_connection_failed'
        except ImportError:
            pass
        if isinstance(exc, IncompleteResponse):
            return exc.failure if exc.failure in {'provider_output_limit','provider_incomplete_response'} else fallback
        status = getattr(exc, 'status_code', getattr(exc, 'code', None))
        if type(status) is int and status in {400, 401, 403, 404, 408, 413, 429, 500, 502, 503, 504}:
            return 'provider_http_' + str(status)
    return fallback
