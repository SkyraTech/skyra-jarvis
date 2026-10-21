"""Independent storage/source assertions for the synthetic native import flow."""
import json
from pathlib import Path
import sqlite3
import sys


def verify(directory):
    root = Path(directory).resolve(strict=True)
    db = sqlite3.connect((root / 'core.sqlite3').as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    try:
        row = db.execute('SELECT config FROM scaffold_registrations WHERE name=?',
                         ('native-existing-node',)).fetchone()
        assert row is not None, 'Existing registration missing'
        config = json.loads(row['config'])
        assert config['kind'] == 'existing-project' and config['host_source'] == 'existing-node'
        assert config['runtime']['kind'] == 'node-typescript-v1' and 'python_sha256' not in config
        assert config['source_directory'] == str(root / 'existing-node')
        document = root / 'existing-node/docs/01_PRODUCT_REQUIREMENTS.md'
        assert document.read_text(encoding='utf-8') == '# Existing owner requirements\nReturn 42; preserve this document.\n'
        assert 'Implementation pending' in (root / 'existing-node/src/main.ts').read_text(encoding='utf-8')
        assert not (root / 'existing-node/src/optional.ts').exists()
        job = db.execute("SELECT state,calls FROM build_jobs WHERE json_extract(config,'$.resource')=? ORDER BY rowid DESC LIMIT 1",
                         (config['workspace'],)).fetchone()
        assert job is not None and job['state'] == 'completed' and job['calls'] == 1
        admission = json.loads((root / 'scaffolds/native-existing-node/admission.json').read_text(encoding='utf-8'))
        assert admission['sha256'] == config['plan_sha256']
        assert admission['plan']['input_hashes']['src/optional.ts'] == 'absent'
    finally:
        db.close()


if __name__ == '__main__':
    verify(sys.argv[1])
