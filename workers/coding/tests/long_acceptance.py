"""Opt-in real elapsed-time native supervision acceptance; deterministic, no providers."""
import argparse
import json
from pathlib import Path
import sys
import threading
import time

REPO = Path(__file__).resolve().parents[3]
for source in ('services/core/src', 'workers/coding/src', 'packages/agent-runtime/src'):
    sys.path.insert(0, str(REPO / source))

from jarvis_core import Core
from jarvis_core.build_jobs import BuildJobs
from jarvis_runtime import RepairRuntime
from skyra_coding import FileWorker, Workspace
from skyra_coding.native import NativeExecutor, NativeProfile


class NoProviderCalls:
    provider = 'fixture'
    model = 'no-live-provider'
    timeout = 1
    max_output_tokens = 256

    def complete(self, *args):
        raise AssertionError('A passing repair baseline must never call a provider')


def main(seconds):
    if type(seconds) is not int or not 601 <= seconds <= 900:
        raise ValueError('Use 601..900 actual seconds to cross both original limits')
    root = REPO / '.runtime' / ('long-execution-' + str(time.time_ns()))
    source = root / 'source'
    source.mkdir(parents=True)
    (source / 'app.py').write_text('def answer():\n    return 42\n', encoding='utf-8')
    (source / 'acceptance.py').write_text(
        'import sys,time\nfrom pathlib import Path\n'
        'sys.path.insert(0,str(Path(__file__).resolve().parent))\n'
        'from app import answer\n'
        f'time.sleep({seconds})\nassert answer()==42\nprint("long acceptance passed")\n', encoding='utf-8')
    workspace = Workspace.snapshot(source, root / 'snapshot', ['app.py', 'acceptance.py'])
    database = root / 'core.sqlite3'
    core = Core(database)
    project = core.create_project('owner', 'Long supervision fixture')
    core.set_policy('owner', project, 'full', ['workspace:long-fixture'])
    profile = NativeProfile('reviewed-long-fixture', (sys.executable, '-I', '-B', 'acceptance.py'),
                            ('acceptance.py',), seconds + 30)
    worker = FileWorker({(project, 'workspace:long-fixture'): workspace}, root / 'evidence',
                        NativeExecutor([profile], owner_enabled=True))
    jobs = BuildJobs(RepairRuntime(worker, {'fixture': NoProviderCalls()}))
    job = jobs.create(core, 'owner', project, 'workspace:long-fixture', profile.name, 'fixture',
                      'Verify real elapsed-time long execution', list(workspace.selected), [],
                      1, 1, 2, seconds + 120, False, True, 'long-fixture')
    result, errors = [], []
    def execute():
        connection = Core(database)
        try: result.append(jobs.tick(connection, 'owner', project)['build_job'])
        except BaseException as exc: errors.append(type(exc).__name__)
        finally: connection.close()
    thread = threading.Thread(target=execute, daemon=True)
    started = time.monotonic()
    thread.start()
    observations = 0
    crossed = False
    print(json.dumps({'artifacts': str(root), 'seconds': seconds}), flush=True)
    try:
        while thread.is_alive():
            current = jobs.get(core, 'owner', job['id'])
            if current['state'] == 'running':
                assert current['lease_until'] > core.clock(), current
                duplicate = jobs.tick(core, 'owner', project)
                assert duplicate['build_job'] is None and duplicate['recovered'] == 0, duplicate
                observations += 1
                crossed = crossed or time.monotonic() - started > 600
            progress = {'state': current['state'], 'elapsed_seconds': round(time.monotonic()-started, 1),
                        'observations': observations, 'crossed_original_parent_lease': crossed}
            temporary = root / 'progress.tmp'
            temporary.write_text(json.dumps(progress), encoding='utf-8')
            try:
                temporary.replace(root / 'progress.json')
            except PermissionError:
                # Windows readers may temporarily deny replacement. This file is
                # advisory telemetry; SQLite and final evidence remain authoritative.
                pass
            thread.join(2)
        assert not errors, errors
        final = result[0]
        assert final['state'] == 'completed' and final['calls'] == 0, final
        task = core.task('owner', final['baseline_task'])
        report = worker.evidence(json.loads(task['evidence'])[0])['result']
        assert report['passed'] and report['cleanup_confirmed'] and report['duration_seconds'] >= seconds, report
        assert crossed and observations > 100
        assert core.db.execute('SELECT count(*) FROM execution_attempts').fetchone()[0] == 1
        proof = {'fixture': True, 'live_model_calls': 0, 'actual_duration_seconds': report['duration_seconds'],
                 'profile_timeout': profile.timeout, 'parent_lease_crossed': crossed,
                 'duplicate_dispatch_observations': observations, 'execution_attempts': 1,
                 'cleanup_confirmed': True, 'final_state': final['state'], 'artifacts': str(root)}
        (root / 'review.json').write_text(json.dumps(proof, indent=2), encoding='utf-8')
        print(json.dumps(proof, indent=2), flush=True)
    finally:
        if thread.is_alive():
            jobs.control(core, 'owner', job['id'], 'cancel')
            thread.join(15)
        core.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=int, default=610)
    main(parser.parse_args().seconds)
