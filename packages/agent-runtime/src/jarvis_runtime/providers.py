"""Explicit Gemini/Groq connections. One attempt; no tools, key rotation or fallback."""

import os
import re
import json
from .responses import IncompleteResponse


class OnlineProvider:
    def __init__(self, provider, model, api_key, *, timeout=45, max_output_tokens=4096, thinking_level=None):
        if (provider not in {'gemini', 'groq'} or not isinstance(model, str)
                or not re.fullmatch(r'[A-Za-z0-9._/-]{1,128}', model)
                or not isinstance(api_key, str) or not api_key.strip()
                or type(timeout) is not int or not 1 <= timeout <= 120
                or type(max_output_tokens) is not int
                or not 256 <= max_output_tokens <= (32768 if provider == 'gemini' else 8192)):
            raise ValueError('Invalid provider configuration')
        if thinking_level is not None and (not isinstance(thinking_level,str) or provider != 'gemini'
                or model != 'gemini-3.5-flash-lite'
                or thinking_level not in {'minimal','low','medium','high'}):
            raise ValueError('Unsupported explicit thinking configuration')
        self.provider, self.model, self._key = provider, model, api_key
        self.timeout, self.max_output_tokens = timeout, max_output_tokens
        self.thinking_level = thinking_level

    def complete(self, system, context, schema):
        if self.provider == 'gemini':
            from google import genai
            from google.genai import types
            options = {} if self.thinking_level is None else {
                'thinking_config': types.ThinkingConfig(thinking_level=self.thinking_level,include_thoughts=False)}
            with genai.Client(api_key=self._key, vertexai=False,
                    http_options=types.HttpOptions(timeout=self.timeout * 1000,
                        retry_options=types.HttpRetryOptions(attempts=1))) as client:
                response = client.models.generate_content(model=self.model, contents=context,
                    config=types.GenerateContentConfig(system_instruction=system,
                        response_mime_type='application/json', response_json_schema=schema,
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                        max_output_tokens=self.max_output_tokens, **options))
                candidates = response.candidates or []
                usage = response.usage_metadata
                counts = {k: v for k, v in {
                    'input_tokens': getattr(usage, 'prompt_token_count', None),
                    'output_tokens': getattr(usage, 'candidates_token_count', None),
                    'total_tokens': getattr(usage, 'total_token_count', None),
                    **({'reasoning_tokens':getattr(usage,'thoughts_token_count',None)} if self.thinking_level else {})
                    }.items() if v is not None}
                reason = str(candidates[0].finish_reason).split('.')[-1] if len(candidates)==1 else None
                if reason != 'STOP':
                    raise IncompleteResponse(output_limited=reason=='MAX_TOKENS',usage=counts)
                return response.text, counts
        from groq import Groq
        # JSON object mode does not transmit a schema as Gemini does. Include the
        # actual host-owned shape so the model is not asked to follow an absent schema.
        output_system = system + '\nRequired output JSON Schema:\n' + json.dumps(
            schema, separators=(',', ':'), allow_nan=False)
        with Groq(api_key=self._key, timeout=self.timeout, max_retries=0) as client:
            response = client.chat.completions.create(model=self.model,
                messages=[{'role': 'system', 'content': output_system}, {'role': 'user', 'content': context}],
                # JSON mode supports existing Llama models as well as newer schema models.
                # The runtime always validates the exact schema and patch semantics locally.
                response_format={'type': 'json_object'}, max_completion_tokens=self.max_output_tokens,
                temperature=0,
                stream=False)
            usage = response.usage
            counts = {k: v for k, v in {
                'input_tokens': getattr(usage, 'prompt_tokens', None),
                'output_tokens': getattr(usage, 'completion_tokens', None),
                'total_tokens': getattr(usage, 'total_tokens', None)}.items() if v is not None}
            reason = response.choices[0].finish_reason if len(response.choices)==1 else None
            if reason != 'stop':
                raise IncompleteResponse(output_limited=reason=='length',usage=counts)
            return response.choices[0].message.content, counts


def load_providers(entries):
    """Resolve only explicitly named environment keys; never auto-load repository secrets."""
    if not isinstance(entries, list) or not 1 <= len(entries) <= 8:
        raise ValueError('Explicit provider entries required')
    result = {}
    for entry in entries:
        if (not isinstance(entry, dict) or set(entry)-{'thinking_level'} != {
                'name', 'provider', 'model', 'api_key_env', 'timeout', 'max_output_tokens'}
                or not isinstance(entry['name'], str) or not re.fullmatch(r'[a-z][a-z0-9_-]{0,63}', entry['name'])
                or entry['name'] in result or not isinstance(entry['api_key_env'], str)
                or not re.fullmatch(r'[A-Z][A-Z0-9_]{0,127}', entry['api_key_env'])):
            raise ValueError('Invalid provider registration')
        result[entry['name']] = OnlineProvider(entry['provider'], entry['model'],
            os.environ.get(entry['api_key_env'], ''), timeout=entry['timeout'],
            max_output_tokens=entry['max_output_tokens'], thinking_level=entry.get('thinking_level'))
    return result


def generation_settings(provider):
    level = getattr(provider,'thinking_level',None)
    return {'thinking_level':level} if level is not None else None
