"""Temporary-test downgrade support; never used by runtime migrations."""
from pathlib import Path
import tempfile


def remove_post_v8_schema(core):
    database=Path(core.db.execute('PRAGMA database_list').fetchone()['file']).resolve()
    if not database.is_relative_to(Path(tempfile.gettempdir()).resolve()):
        raise ValueError('Migration downgrade fixtures require a temporary test database')
    # An old version marker must not coexist with later-version tables/indexes.
    for table in ('chat_attachments','coding_chat_requests','coding_chat_metadata','coding_source_activations',
                  'coding_source_preparations','coding_workspace_requests','coding_workspaces',
                  'coding_delegated_tasks','coding_connections','coding_job_links'):
        core.db.execute('DROP TABLE '+table)
    core.db.execute('DROP INDEX messages_conversation_page')
