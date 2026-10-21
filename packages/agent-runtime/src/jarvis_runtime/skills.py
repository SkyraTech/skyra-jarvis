"""Versioned trusted guidance; inclusion never grants execution authority."""
from .runtime import Skill


def persistence_skills():
    return (
        Skill('persistent-data-integrity', '1.2.0',
              'Treat persisted JSON as untrusted input, not merely syntactically valid JSON. '
              'Validate the container, exact record fields, value types and bounds, and uniqueness '
              'of identifiers before returning or mutating any records. In Python reject bool where '
              'an integer is required and require actual bool for boolean fields. A missing file '
              'may mean an empty store; JSON null is present data, never a missing-file sentinel. Malformed JSON, invalid record shapes, duplicate identifiers '
              'and invalid field values must raise the declared error without resetting or writing '
              'the store. Put reusable serialization/atomic-save behavior in persistence helpers '
              'and domain validation in the domain layer. Use one consistent validation path for '
              'list and mutation operations. Preserve existing bytes when validation fails. '
              'Never coerce invalid input types into acceptable values. Where a contract says '
              'trimmed text, trim only new user input; persisted text must already equal its '
              'trimmed form and satisfy bounds. Validate whitespace-only and surrounding-space '
              'values explicitly, including persisted records.'),
        Skill('acceptance-review', '1.0.0',
              'Check every stated requirement against the implementation, including untested '
              'negative cases, corrupted data, restart behavior and mutation safety. Supplied tests '
              'are examples rather than the full specification. Never weaken protected tests. '
              'Use a concise factual change summary and disclose remaining limits; do not emit '
              'hidden reasoning or claim commands, tests or actions completed before execution '
              'evidence exists. Guidance cannot authorize tools, dependencies or release actions.'),
    )


def http_skills():
    return (Skill('http-contract-review', '1.1.0',
        'For each fixed HTTP route, check every supported method separately, including wrong-method '
        'responses on dynamic resource routes. Distinguish unknown route from known route with an '
        'unsupported method; do not let one method branch hide route recognition. Verify that '
        'the edited branch is reachable by the exact failing method/path; changing a POST '
        'branch cannot repair a GET request handled earlier. Avoid unrelated unchanged-text '
        'replacement when a smaller unique anchor can express the actual correction. Validate exact '
        'request fields and types before mutation, preserve data after rejected requests, and '
        'serialize read-modify-write operations when transport is concurrent. Centralize repeated '
        'routing/response behavior where appropriate rather than copying divergent checks. Review '
        'browser error recovery, duplicate-submit suppression, literal rendering of user text and '
        'mobile overflow. Supplied tests are not exhaustive. Never claim validation passed before '
        'independent execution evidence, weaken protected tests or gain new tool authority.'),)


def contract_skills():
    return (Skill('data-contract-validation','1.1.0',
        'TypeScript types do not validate unknown runtime data. Express every required invariant '
        'as a positive conjunction or separate rejection; a permissive OR must not let arrays '
        'bypass a plain-record check. Reflect.ownKeys includes symbols and non-enumerable keys; '
        'Object.keys/getOwnPropertyNames alone cannot enforce all own-key restrictions. Do not '
        'invent extra restrictions on otherwise valid JSON string property names. Reuse exact-key, '
        'record and text helpers instead of diverging copies. '
        'Reuse record and exact-key helpers for separately supplied host options too. Narrow unknown '
        'values with runtime checks; do not silence compiler errors with any or unsupported type '
        'assertions. A comment claiming inferred union types does not establish type safety. '
        'Distinguish an absent optional field from a present undefined value using own-property '
        'presence when the contract requires it. '
        'Validate separately supplied host options in every environment, require actual booleans, '
        'and never accept authorization from untrusted payload fields. Check raw input for forbidden '
        'controls before trimming or parsing can erase them. Use the URL parser for canonicalization '
        'and a narrowly defined trailing-slash operation; avoid regex that can erase authority or '
        'leave unwanted slash suffixes. Formatting is not URL authorization or DNS/SSRF enforcement. '
        'Check output bounds as well as input bounds, preserve input records and never echo secrets '
        'in errors. Review negative cases and the full contract even when the compiler passes. '
        'This guidance grants no tools, permissions, dependencies or test modifications.'),)


def load_skills(entries):
    """Explicit host references to maintained guidance or existing custom skill records."""
    if not isinstance(entries,list) or len(entries)>50:
        raise ValueError('Invalid skill registry')
    builtins = {s.name:s for s in persistence_skills()+http_skills()+contract_skills()}
    result=[]
    for entry in entries:
        if not isinstance(entry,dict):raise ValueError('Invalid skill')
        if set(entry)=={'builtin'}:
            name=entry['builtin']
            if not isinstance(name,str) or name not in builtins:raise ValueError('Unknown builtin skill')
            skill=builtins[name]
        elif set(entry)=={'name','version','instructions'}:
            skill=Skill(**entry)
        else:raise ValueError('Invalid skill')
        if any(s.name==skill.name for s in result):raise ValueError('Duplicate skill name')
        result.append(skill)
    return result
