"""Explicit one-call conversation/planning probe using generated context only."""
import argparse
import json
import os
from pathlib import Path
import sys
import time

REPO = Path(__file__).resolve().parents[2]
for source in ('services/core/src', 'workers/coding/src', 'packages/agent-runtime/src'):
    sys.path.insert(0, str(REPO / source))
from jarvis_core import Core
from jarvis_runtime.conversation import ConversationRuntime
from jarvis_runtime.providers import OnlineProvider


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--provider', choices=('gemini', 'groq'), required=True)
    parser.add_argument('--model', required=True)
    parser.add_argument('--mode', choices=('chat', 'plan'), required=True)
    parser.add_argument('--api-key-env', required=True)
    parser.add_argument('--env-file', type=Path)
    parser.add_argument('--allow-live-call', action='store_true', required=True)
    args = parser.parse_args()
    key = os.environ.get(args.api_key_env, '')
    if args.env_file:
        from dotenv import dotenv_values
        key = key or dotenv_values(args.env_file).get(args.api_key_env, '')
    if not key:
        parser.error('Selected key is unavailable; value withheld')
    provider = OnlineProvider(args.provider, args.model, key, timeout=45, max_output_tokens=2048)
    root = args.directory.resolve()
    root.mkdir(parents=True, exist_ok=False)
    core = Core(root / 'core.sqlite3')
    try:
        project = core.create_project('probe-owner', 'Generated conversation probe')
        conversation = core.create_conversation('probe-owner', project)
        runtime = ConversationRuntime({args.provider: provider})
        content = ('In two sentences, explain why a website needs acceptance criteria.' if args.mode == 'chat' else
                   'Create a concise draft plan for a fictional three-page company website: home, services, contact. Include keyboard accessibility and automated tests. Use two phases, with one or two tasks and acceptance criteria each. No integrations or deployment actions.')
        turn = runtime.create(core, 'probe-owner', conversation, args.provider, args.mode, content, 'one-call-probe')
        started = time.monotonic()
        result = runtime.generate(core, 'probe-owner', turn)
        summary = {'provider': args.provider, 'model': args.model, 'mode': args.mode,
                   'state': result['state'], 'error': result['error'], 'usage': result['usage'],
                   'seconds': round(time.monotonic()-started,3), 'turn': turn,
                   'plan_validated': bool(result['response'] and result['response'].get('plan')),
                   'task_count': core.db.execute('SELECT COUNT(*) FROM tasks').fetchone()[0],
                   'live_calls_authorized': 1, 'generated_context_only': True}
        (root / 'review.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
        print(json.dumps(summary, indent=2))
        if result['state'] != 'completed': raise SystemExit(1)
    finally: core.close()

if __name__ == '__main__': main()
