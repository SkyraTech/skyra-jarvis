"""Owner-operated, selected-file import. Never installs or executes project code."""
import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
for source in ('services/core/src', 'workers/coding/src'):
    sys.path.insert(0, str(ROOT / source))

from skyra_coding.admission import ProjectAdmission
from skyra_coding.scaffold import _parent
from skyra_coding.workspace import read_bytes, relative


def read_request(path):
    if not path.is_absolute():
        raise ValueError('Absolute configuration path required')
    content = read_bytes(_parent(path.parent), path.name)
    if len(content) > 32768:
        raise ValueError('Configuration exceeds 32KB')
    return json.loads(content)


def main():
    parser = argparse.ArgumentParser(description='Review and snapshot a host-approved existing project')
    parser.add_argument('--host-config', required=True, type=Path)
    parser.add_argument('--request', required=True, type=Path)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--review', type=Path, help='New absolute JSON output outside source and snapshot state')
    action.add_argument('--apply', action='store_true')
    parser.add_argument('--expected-sha256')
    args = parser.parse_args()
    if args.apply and not re.fullmatch('[a-f0-9]{64}', args.expected_sha256 or ''):
        parser.error('--apply requires the exact --expected-sha256 from the review')
    if args.review and args.expected_sha256:
        parser.error('--expected-sha256 applies only to --apply')
    try:
        host = read_request(args.host_config)
        request = read_request(args.request)
        if type(host) is not dict or set(host) != {'sources', 'snapshot_root'}:
            raise ValueError('Invalid host configuration')
        if type(request) is not dict or set(request) != {'source', 'name', 'files', 'create_paths'}:
            raise ValueError('Invalid admission request')
        admission = ProjectAdmission(host['sources'], host['snapshot_root'])
        if args.review:
            if not args.review.is_absolute() or args.review.suffix != '.json':
                raise ValueError('Absolute JSON output required')
            relative(args.review.name)
            output = _parent(args.review.parent) / args.review.name
            if any(output.is_relative_to(root) for root in [admission.root, *admission.sources.values()]):
                raise ValueError('Review output must be outside project and snapshot state')
            review = admission.preview(**request)
            with output.open('x', encoding='utf-8', newline='\n') as stream:
                json.dump(review, stream, indent=2, allow_nan=False)
                stream.write('\n')
            print('Admission review saved. Source unchanged; execution remains disabled.')
        else:
            result = admission.materialize(**request, expected_sha256=args.expected_sha256)
            print(json.dumps(result, sort_keys=True))
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        parser.exit(2, 'Admission unavailable. Check host-approved roots, selected files and exact review. Partial state requires reconciliation; source is never overwritten.\n')


if __name__ == '__main__':
    main()
