import sqlite3
import time
from pathlib import Path

DB_FILE = Path(__file__).parent / "mentor.db"


def conn():
    c = sqlite3.connect(DB_FILE)
    c.row_factory = sqlite3.Row
    return c


def init():
    with conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS tasks(
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                title        TEXT NOT NULL,
                category     TEXT NOT NULL DEFAULT 'other',
                due_ts       INTEGER NOT NULL,          -- task er somoy (epoch seconds)
                status       TEXT NOT NULL DEFAULT 'pending',  -- pending | done | missed
                completed_ts INTEGER,
                reason       TEXT,                      -- kaj na hole kon karon
                notified     INTEGER NOT NULL DEFAULT 0,
                created_ts   INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages(
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                role    TEXT NOT NULL,                  -- user | assistant
                content TEXT NOT NULL,
                ts      INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS expenses(
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                amount     REAL NOT NULL,
                purpose    TEXT NOT NULL,               -- kon kaje khoroch
                category   TEXT NOT NULL DEFAULT 'other',
                ts         INTEGER NOT NULL,
                created_ts INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS budgets(
                month  TEXT PRIMARY KEY,                -- 'YYYY-MM'
                amount REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS meta(
                key   TEXT PRIMARY KEY,
                value TEXT
            );
            """
        )


def get_meta(key):
    with conn() as c:
        r = c.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return r["value"] if r else None


def set_meta(key, value):
    with conn() as c:
        c.execute(
            "INSERT INTO meta(key,value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )


# ---------- helpers used by main.py ----------
def _rows(cur):
    return [dict(r) for r in cur.fetchall()]


def add_task(title, due_ts, category="other"):
    now = int(time.time())
    with conn() as c:
        cur = c.execute(
            "INSERT INTO tasks(title,category,due_ts,created_ts) VALUES(?,?,?,?)",
            (title, category, int(due_ts), now),
        )
        return cur.lastrowid


def all_tasks():
    with conn() as c:
        return _rows(c.execute("SELECT * FROM tasks ORDER BY due_ts"))


def get_all_tasks(since_ts=None):
    """Tasks shown on the timeline (last 2 days + future)."""
    since_ts = since_ts if since_ts is not None else int(time.time()) - 2 * 86400
    with conn() as c:
        return _rows(c.execute("SELECT * FROM tasks WHERE due_ts>=? ORDER BY due_ts", (since_ts,)))


def set_task_status(task_id, status, reason=None):
    ts = int(time.time()) if status == "done" else None
    with conn() as c:
        c.execute(
            "UPDATE tasks SET status=?, completed_ts=?, reason=? WHERE id=?",
            (status, ts, reason, task_id),
        )


def pop_due_tasks(now):
    """Pending tasks whose time has come and were not notified yet (marks them notified)."""
    with conn() as c:
        rows = _rows(c.execute(
            "SELECT * FROM tasks WHERE status='pending' AND notified=0 AND due_ts<=?", (now,)))
        for r in rows:
            c.execute("UPDATE tasks SET notified=1 WHERE id=?", (r["id"],))
    return rows


def add_message(role, content, ts=None):
    with conn() as c:
        c.execute("INSERT INTO messages(role,content,ts) VALUES(?,?,?)",
                  (role, content, ts or int(time.time())))


def get_chat_history(limit=50):
    with conn() as c:
        rows = _rows(c.execute(
            "SELECT role,content,ts FROM messages ORDER BY id DESC LIMIT ?", (limit,)))
    return rows[::-1]


def add_expense(amount, purpose, category="other", ts=None):
    now = int(time.time())
    with conn() as c:
        cur = c.execute(
            "INSERT INTO expenses(amount,purpose,category,ts,created_ts) VALUES(?,?,?,?,?)",
            (float(amount), purpose, category, ts or now, now),
        )
        return cur.lastrowid


def list_expenses(limit=None):
    sql = "SELECT * FROM expenses ORDER BY ts DESC"
    if limit:
        sql += f" LIMIT {int(limit)}"
    with conn() as c:
        return _rows(c.execute(sql))


def set_budget(month, amount):
    with conn() as c:
        c.execute(
            "INSERT INTO budgets(month,amount) VALUES(?,?) "
            "ON CONFLICT(month) DO UPDATE SET amount=excluded.amount",
            (month, float(amount)),
        )


def get_budget(month):
    with conn() as c:
        r = c.execute("SELECT amount FROM budgets WHERE month=?", (month,)).fetchone()
    return r["amount"] if r else None
