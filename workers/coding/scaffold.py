"""Owner-operated scaffold review/create command; no credentials or model calls."""

import argparse
import json
from pathlib import Path
import re
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[2]
for source in ('services/core/src', 'workers/coding/src'):
    sys.path.insert(0, str(ROOT / source))

from jarvis_core import Core
from skyra_coding.scaffold import checksum, materialize, preview


def main():
    parser = argparse.ArgumentParser(description='Review or create a specification-backed Python scaffold')
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--actor', required=True, help='Existing owner identity in the private Core database')
    parser.add_argument('--request', type=Path, required=True, help='Owner-authored JSON scaffold request')
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--review', type=Path, help='Write a new review JSON file; never overwrite')
    action.add_argument('--apply', action='store_true')
    parser.add_argument('--expected-plan-sha256', help='Exact reviewed plan checksum, required for --apply')
    args = parser.parse_args()
    if args.apply and not re.fullmatch('[a-f0-9]{64}', args.expected_plan_sha256 or ''):
        parser.error('--apply requires --expected-plan-sha256 from the reviewed JSON')
    if args.review and args.expected_plan_sha256:
        parser.error('--expected-plan-sha256 applies only to --apply')
    core = None
    try:
        if not args.database.is_file() or args.request.stat().st_size > 24000:
            raise ValueError('Use an existing Core database and request within 24KB')
        request = json.loads(args.request.read_text(encoding='utf-8'))
        required = {'specification', 'expected_sha256', 'contract', 'parent', 'name', 'python'}
        if not isinstance(request, dict) or not required <= set(request) or set(request) - required - {'template'}:
            raise ValueError('Invalid scaffold request fields')
        core = Core(args.database)
        if args.review:
            plan = preview(core, args.actor, **request)
            with args.review.open('x', encoding='utf-8', newline='\n') as stream:
                json.dump({'plan_sha256': checksum(plan), 'plan': plan}, stream, indent=2, allow_nan=False)
                stream.write('\n')
            print('Scaffold review saved. No project or execution permissions were created.')
        else:
            result = materialize(core, args.actor, **request, expected_plan_sha256=args.expected_plan_sha256)
            print(json.dumps(result, sort_keys=True))
    except (OSError, ValueError, TypeError, KeyError, RecursionError, sqlite3.Error):
        parser.exit(2, 'Scaffold unavailable. Check ownership, approval, request and reviewed checksum. Existing projects are not overwritten.\n')
    finally:
        if core is not None:
            core.close()


if __name__ == '__main__':
    main()
