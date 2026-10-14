"""Repeatable trusted fixture: failing test -> repair -> retest -> review bundle."""

import argparse
from pathlib import Path
import json
import sys

REPO=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(REPO/'services/core/src'))
sys.path.insert(0,str(REPO/'workers/coding/src'))
from jarvis_core import Core
from skyra_coding import Workspace,FileWorker
from skyra_coding.native import NativeExecutor,NativeProfile
from skyra_coding.workflow import CodingWorkflow


def main():
    parser=argparse.ArgumentParser(description='Run generated trusted Windows repair fixture; no Git/model calls')
    parser.add_argument('--directory',type=Path,required=True,help='New directory for fixture, database and evidence')
    args=parser.parse_args();root=args.directory.resolve();root.mkdir(parents=True,exist_ok=False)
    source=root/'source';source.mkdir();(source/'tests').mkdir()
    (source/'app.py').write_text('def answer():\n    return 41\n',encoding='utf-8')
    (source/'tests/test_app.py').write_text('import sys,unittest\nfrom pathlib import Path\nsys.path.insert(0,str(Path(__file__).resolve().parents[1]))\nfrom app import answer\nclass AnswerTest(unittest.TestCase):\n    def test_answer(self):self.assertEqual(42,answer())\n',encoding='utf-8')
    workspace=Workspace.snapshot(source,root/'snapshot',['app.py','tests/test_app.py'])
    profile=NativeProfile('fixture-unit',(sys.executable,'-I','-B','-m','unittest','discover','-s','tests','-v'),('tests/test_app.py',),20)
    executor=NativeExecutor([profile],owner_enabled=True)
    core=Core(root/'core.sqlite3')
    try:
        project=core.create_project('fixture-owner','Generated repair demo')
        core.set_policy('fixture-owner',project,'full',['workspace:fixture'])
        worker=FileWorker({(project,'workspace:fixture'):workspace},root/'evidence',executor)
        workflow=CodingWorkflow(worker)
        run=workflow.create(core,'fixture-owner',project,'workspace:fixture','fixture-unit',[
            {'path':'app.py','expected_sha256':workspace.read('app.py')['sha256'],'old':'41','new':'42'}],request_id='fixture-demo')
        for _ in range(4):result=workflow.advance(core,'fixture-owner',run)
        summary={'state':result['state'],'source_preserved':(source/'app.py').read_text().endswith('return 41\n'),
                 'mode':'native_trusted','run_id':run,'steps':result['results']}
        (root/'review.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
        print(json.dumps(summary,indent=2))
        if result['state']!='ready_for_review':raise SystemExit(1)
    finally:core.close()


if __name__=='__main__':main()
