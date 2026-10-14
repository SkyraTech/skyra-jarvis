"""SQLite project state and exact-action authorization, without model dependencies.

Callers supply identities from a trusted host, never from unverified model input.
Resource IDs are exact logical scopes; execution adapters must enforce OS boundaries.
"""

from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sqlite3
import time
import uuid


class Denied(PermissionError):
    pass


class Conflict(ValueError):
    pass


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def identifier():
    return uuid.uuid4().hex


class Core:
    def __init__(self, path, clock=time.time):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.clock = clock
        self.db = sqlite3.connect(path, isolation_level=None, timeout=5)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        with self.transaction():
            version = self.db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1):
                raise Conflict("Unsupported database version; migration required")
            if version == 0:
                for statement in SCHEMA:
                    self.db.execute(statement)
                self.db.execute("PRAGMA user_version=1")

    def close(self):
        self.db.close()

    @contextmanager
    def transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def _owned(self, actor, project):
        row = self.db.execute("SELECT * FROM projects WHERE id=?", (project,)).fetchone()
        if row is None or row["owner"] != actor:
            raise Denied("Project unavailable for this actor")
        return row

    def _task(self, actor, task):
        row = self.db.execute("SELECT * FROM tasks WHERE id=?", (task,)).fetchone()
        if row is None:
            raise Denied("Task unavailable")
        self._owned(actor, row["project"])
        return row

    def _event(self, project, kind, subject):
        self.db.execute("INSERT INTO events(project,kind,subject,at) VALUES(?,?,?,?)",
                        (project, kind, subject, self.clock()))

    def create_project(self, actor, name):
        if not actor or not name.strip():
            raise ValueError("Actor and project name required")
        project = identifier()
        with self.transaction():
            self.db.execute("INSERT INTO projects VALUES(?,?,?,'read_only',1,'[]')",
                            (project, actor, name))
            self._event(project, "project.created", project)
        return project

    def set_policy(self, actor, project, mode, resources):
        if mode not in {"read_only", "ask", "full"}:
            raise ValueError("Unknown permission mode")
        if not isinstance(resources, list) or not all(isinstance(x, str) and x for x in resources):
            raise ValueError("Explicit resource IDs required")
        with self.transaction():
            self._owned(actor, project)
            self.db.execute("UPDATE projects SET mode=?,resources=?,version=version+1 WHERE id=?",
                            (mode, encode(sorted(set(resources))), project))
            self._event(project, "policy.updated", project)

    def create_conversation(self, actor, project):
        conversation = identifier()
        with self.transaction():
            self._owned(actor, project)
            self.db.execute("INSERT INTO conversations VALUES(?,?)", (conversation, project))
            self._event(project, "conversation.created", conversation)
        return conversation

    def _conversation(self, actor, conversation):
        row = self.db.execute("SELECT project FROM conversations WHERE id=?", (conversation,)).fetchone()
        if row is None:
            raise Denied("Conversation unavailable")
        self._owned(actor, row[0])
        return row[0]

    def append_message(self, actor, conversation, role, content, request_id):
        if role not in {"user", "assistant", "tool"} or not request_id or not isinstance(content, str):
            raise ValueError("Invalid message")
        with self.transaction():
            project = self._conversation(actor, conversation)
            prior = self.db.execute("SELECT * FROM messages WHERE conversation=? AND request_id=?",
                                    (conversation, request_id)).fetchone()
            if prior:
                if prior["role"] != role or prior["content"] != content:
                    raise Conflict("Request ID reused with different message")
                return prior["id"]
            cursor = self.db.execute("INSERT INTO messages(conversation,role,content,request_id) VALUES(?,?,?,?)",
                                     (conversation, role, content, request_id))
            self._event(project, "message.appended", str(cursor.lastrowid))
            return cursor.lastrowid

    def messages(self, actor, conversation):
        self._conversation(actor, conversation)
        return [dict(r) for r in self.db.execute("SELECT * FROM messages WHERE conversation=? ORDER BY id", (conversation,))]

    def create_task(self, actor, project, action, resource, payload):
        if action not in {"read", "write", "execute"} or not isinstance(resource, str) or not resource:
            raise ValueError("Invalid action/resource")
        if not isinstance(payload, dict):
            raise ValueError("Task payload must be an object")
        serialized = encode(payload)
        digest = hashlib.sha256(encode([project, actor, action, resource, payload]).encode()).hexdigest()
        task = identifier()
        with self.transaction():
            self._owned(actor, project)
            self.db.execute("INSERT INTO tasks(id,project,action,resource,payload,digest,state) VALUES(?,?,?,?,?,?,'queued')",
                            (task, project, action, resource, serialized, digest))
            self._event(project, "task.created", task)
        return task

    def task(self, actor, task):
        return dict(self._task(actor, task))

    def start(self, actor, task, lease_seconds=60):
        if not 1 <= lease_seconds <= 300:
            raise ValueError("Lease must be 1..300 seconds")
        with self.transaction():
            t = self._task(actor, task)
            if t["state"] not in {"queued", "waiting_approval"}:
                raise Conflict("Task cannot start in its current state")
            p = self._owned(actor, t["project"])
            if t["resource"] not in json.loads(p["resources"]):
                raise Denied("Resource outside scope")
            if p["mode"] == "read_only" and t["action"] != "read":
                raise Denied("Read-only policy")
            if p["mode"] == "ask" and t["action"] != "read":
                approval = self.db.execute(
                    "SELECT * FROM approvals WHERE task=? AND version=? AND digest=? AND expires>? AND state IN ('pending','approved') ORDER BY rowid DESC LIMIT 1",
                    (task, p["version"], t["digest"], self.clock())).fetchone()
                if approval is None:
                    aid = identifier()
                    self.db.execute("INSERT INTO approvals VALUES(?,?,?,?,?,'pending')",
                                    (aid, task, p["version"], t["digest"], self.clock()+300))
                    self.db.execute("UPDATE tasks SET state='waiting_approval' WHERE id=?", (task,))
                    self._event(t["project"], "approval.requested", aid)
                    return {"state": "waiting_approval", "approval_id": aid}
                if approval["state"] == "pending":
                    return {"state": "waiting_approval", "approval_id": approval["id"]}
                self.db.execute("UPDATE approvals SET state='consumed' WHERE id=?", (approval["id"],))
            token = identifier()
            self.db.execute("UPDATE tasks SET state='running',lease_token=?,lease_until=?,policy_version=? WHERE id=?",
                            (token, self.clock()+lease_seconds, p["version"], task))
            self._event(t["project"], "task.started", task)
            return {"state": "running", "lease_token": token}

    def decide(self, actor, approval_id, approve):
        if type(approve) is not bool:
            raise ValueError("Decision must be boolean")
        with self.transaction():
            a = self.db.execute("SELECT * FROM approvals WHERE id=?", (approval_id,)).fetchone()
            if a is None:
                raise Denied("Approval unavailable")
            t = self._task(actor, a["task"])
            p = self._owned(actor, t["project"])
            if a["state"] != "pending" or a["expires"] <= self.clock() or a["version"] != p["version"] or a["digest"] != t["digest"] or t["state"] != "waiting_approval":
                raise Conflict("Approval is stale or already decided")
            self.db.execute("UPDATE approvals SET state=? WHERE id=?", ("approved" if approve else "rejected", approval_id))
            if not approve:
                self.db.execute("UPDATE tasks SET state='cancelled' WHERE id=?", (t["id"],))
            self._event(t["project"], "approval.approved" if approve else "approval.rejected", approval_id)

    def _lease(self, actor, task, token):
        t = self._task(actor, task)
        p = self._owned(actor, t["project"])
        if t["state"] != "running" or t["lease_token"] != token or t["lease_until"] <= self.clock():
            raise Conflict("Lease expired or ownership lost")
        if p["version"] != t["policy_version"]:
            raise Denied("Policy changed; reconcile task before continuing")
        return t

    def heartbeat(self, actor, task, token):
        with self.transaction():
            self._lease(actor, task, token)
            self.db.execute("UPDATE tasks SET lease_until=? WHERE id=?", (self.clock()+60, task))

    def complete(self, actor, task, token, evidence, success=True):
        if type(success) is not bool or not isinstance(evidence, list) or not evidence or not all(isinstance(x,str) and x.strip() for x in evidence):
            raise ValueError("Nonempty evidence references and boolean outcome required")
        with self.transaction():
            t = self._lease(actor, task, token)
            state = "succeeded" if success else "failed"
            self.db.execute("UPDATE tasks SET state=?,evidence=?,lease_token=NULL,lease_until=NULL WHERE id=?",
                            (state, encode(evidence), task))
            self._event(t["project"], "task."+state, task)

    def cancel(self, actor, task):
        with self.transaction():
            t = self._task(actor, task)
            if t["state"] in {"succeeded", "failed", "cancelled"}:
                raise Conflict("Task already terminal")
            # Running external effects need acknowledgement/reconciliation, not fake cancellation.
            state = "cancellation_requested" if t["state"] in {"running", "cancellation_requested"} else "cancelled"
            if t["state"] in {"interrupted", "cancellation_unconfirmed"}:
                raise Conflict("Reconcile uncertain effects before cancellation")
            self.db.execute("UPDATE tasks SET state=? WHERE id=?", (state, task))
            self._event(t["project"], "task."+state, task)

    def recover_expired(self, actor, project):
        with self.transaction():
            self._owned(actor, project)
            rows = self.db.execute("SELECT id,state FROM tasks WHERE project=? AND state IN ('running','cancellation_requested') AND lease_until<=?",
                                   (project, self.clock())).fetchall()
            for row in rows:
                state = "cancellation_unconfirmed" if row["state"] == "cancellation_requested" else "interrupted"
                self.db.execute("UPDATE tasks SET state=?,lease_token=NULL,lease_until=NULL WHERE id=?", (state, row[0]))
                self._event(project, "task."+state, row[0])
            return len(rows)

    def reconcile(self, actor, task, outcome, evidence):
        """Trusted host records externally verified outcome; never automatic retry."""
        if outcome not in {"retry", "succeeded", "failed", "cancelled"}:
            raise ValueError("Unknown reconciliation outcome")
        if not isinstance(evidence, list) or not evidence or not all(isinstance(x,str) and x.strip() for x in evidence):
            raise ValueError("Reconciliation evidence required")
        with self.transaction():
            t = self._task(actor, task)
            if t["state"] not in {"interrupted", "cancellation_unconfirmed"}:
                raise Conflict("Task is not awaiting reconciliation")
            if outcome == "retry" and t["state"] == "cancellation_unconfirmed":
                raise Conflict("Cancelled work cannot automatically restart")
            state = "queued" if outcome == "retry" else outcome
            self.db.execute("UPDATE tasks SET state=?,evidence=? WHERE id=?", (state, encode(evidence), task))
            self._event(t["project"], "task.reconciled."+state, task)

    def events(self, actor, project, after=0):
        self._owned(actor, project)
        return [dict(r) for r in self.db.execute("SELECT * FROM events WHERE project=? AND id>? ORDER BY id", (project, after))]


SCHEMA = [
    "CREATE TABLE projects(id TEXT PRIMARY KEY,owner TEXT NOT NULL,name TEXT NOT NULL,mode TEXT NOT NULL,version INTEGER NOT NULL,resources TEXT NOT NULL)",
    "CREATE TABLE conversations(id TEXT PRIMARY KEY,project TEXT NOT NULL REFERENCES projects(id))",
    "CREATE TABLE messages(id INTEGER PRIMARY KEY,conversation TEXT NOT NULL REFERENCES conversations(id),role TEXT NOT NULL,content TEXT NOT NULL,request_id TEXT NOT NULL,UNIQUE(conversation,request_id))",
    "CREATE TABLE tasks(id TEXT PRIMARY KEY,project TEXT NOT NULL REFERENCES projects(id),action TEXT NOT NULL,resource TEXT NOT NULL,payload TEXT NOT NULL,digest TEXT NOT NULL,state TEXT NOT NULL,lease_token TEXT,lease_until REAL,policy_version INTEGER,evidence TEXT)",
    "CREATE TABLE approvals(id TEXT PRIMARY KEY,task TEXT NOT NULL REFERENCES tasks(id),version INTEGER NOT NULL,digest TEXT NOT NULL,expires REAL NOT NULL,state TEXT NOT NULL)",
    "CREATE TABLE events(id INTEGER PRIMARY KEY AUTOINCREMENT,project TEXT NOT NULL REFERENCES projects(id),kind TEXT NOT NULL,subject TEXT NOT NULL,at REAL NOT NULL)",
    "CREATE INDEX events_project_cursor ON events(project,id)",
    "CREATE INDEX approvals_task ON approvals(task,version)",
    "CREATE INDEX tasks_recovery ON tasks(project,state,lease_until)",
]
