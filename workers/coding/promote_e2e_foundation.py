"""Promote the independently reviewed agent-written E2E foundation, never regenerate it."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
for source in ('services/core/src', 'workers/coding/src', 'packages/agent-runtime/src'):
    sys.path.insert(0, str(REPO / source))
from skyra_coding.scaffold import _parent
from skyra_coding.workspace import checked, read_bytes, digest
from skyra_coding.delivery import Delivery

FOUNDATION = REPO / '.runtime/coding-evaluation-gemini-1792426287190213500'
PROJECT = REPO.parent / 'skyra-e2e-suite'
AUTHORED = {'src/guards.ts': '783f674872cd52c1a6b2187b2805740a542fd876d3e597f3eb08007693025644',
            'src/target.ts': '47499520083aefaff8205c389bf3c4550b833d53bd15f89991984732beeba891'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--expected-sha256')
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location('supervised_evaluation', REPO / 'packages/agent-runtime/evaluate.py')
    evaluation = importlib.util.module_from_spec(spec); spec.loader.exec_module(evaluation)
    inputs = evaluation.tested_inputs(FOUNDATION, 'c47bef257b51486784d5acc0aa3c63ec', task='e2e-targets-v1')
    independent = json.loads((FOUNDATION / 'independent-review.json').read_text(encoding='utf-8'))
    if independent['passed'] is not True or independent['input_hashes'] != inputs['input_hashes']:
        raise ValueError('Current independent acceptance required')
    for path, identity in AUTHORED.items():
        if inputs['input_hashes'][path] != identity:
            raise ValueError('Previously reviewed agent source changed')
    source = _parent(PROJECT)
    config = json.loads((FOUNDATION / 'evaluation.json').read_text(encoding='utf-8'))
    class NoCalls:
        provider = config['provider']; model = config['model']
        def complete(self, *args): raise AssertionError('Promotion never buys a model call')
    core, runtime, jobs, _ = evaluation.connect(FOUNDATION, NoCalls())
    try:
        worker = runtime.worker
        workspace = worker.workspaces[(config['project'], 'workspace:evaluation')]
        # Only supervisor-owned scaffolding is seeded. Agent source is written
        # exclusively by the existing reviewed, tested delivery mechanism.
        for path in config['protected_paths']:
            content = read_bytes(workspace.baseline, path)
            target = checked(source, path)
            if target.exists():
                if read_bytes(source, path) != content:
                    raise ValueError('Existing project scaffold differs; do not overwrite it')
            else:
                if args.apply:
                    raise ValueError('Review and seed protected scaffolding first')
                target.parent.mkdir(parents=True, exist_ok=True)
                with checked(source, path).open('xb') as stream: stream.write(content)
        resources = json.loads(core._owned('owner', config['project'])['resources'])
        target_resource = 'source:skyra-e2e'
        if target_resource not in resources:
            core.set_policy('owner', config['project'], 'full', [*resources, target_resource])
        worker.delivery = Delivery(worker, [{'project_id': config['project'], 'resource_id': target_resource,
            'workspace_resource': 'workspace:evaluation', 'directory': str(source)}])
        checkpoint = FOUNDATION / 'product-promotion.json'
        if not args.apply:
            review = worker.delivery.preview(core, 'owner', inputs['run'], target_resource)
            if {change['path'] for change in review['plan']['changes']} != set(AUTHORED):
                raise ValueError('Only the two reviewed agent files may be delivered')
            if checkpoint.exists() and json.loads(checkpoint.read_text(encoding='utf-8')) != review:
                raise ValueError('Prior product promotion intent differs')
            if not checkpoint.exists(): checkpoint.write_text(json.dumps(review, indent=2), encoding='utf-8')
            print(json.dumps({'state': 'review_required', 'sha256': review['sha256'],
                'project': str(source), 'agent_files': list(AUTHORED), 'model_calls': 0}))
        else:
            review = json.loads(checkpoint.read_text(encoding='utf-8'))
            if args.expected_sha256 != review['sha256']:
                raise ValueError('Exact product-promotion review required')
            task = worker.delivery.prepare(core, 'owner', inputs['run'], target_resource,
                review['sha256'], 'promote-e2e-validator-v1')
            if task['state'] == 'queued':
                lease = core.start('owner', task['id']); worker.perform(core, 'owner', task['id'], lease['lease_token'])
            result = worker.delivery.status(core, 'owner', task['id'])
            if result['state'] != 'succeeded': raise ValueError('Product delivery requires reconciliation')
            for path, identity in AUTHORED.items():
                if digest(read_bytes(source, path)) != identity: raise ValueError('Delivered source differs')
            print(json.dumps({'state': 'delivered', 'task': task['id'], 'evidence': result['evidence'],
                'project': str(source), 'model_calls': 0, 'completed_project': False}))
    finally:
        core.close()


if __name__ == '__main__':
    main()
