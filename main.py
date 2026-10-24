import os
import re
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import db
import fin
import llm
import ml

TZ = timezone(timedelta(hours=6))  # Bangladesh (no tzdata package needed)
BASE = Path(__file__).parent

db.init()
app = FastAPI(title="3D Mentor AI")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


@app.on_event("startup")
def warmup():
    def run():
        try:
            llm.generate_response("hi")
        except Exception as e:
            print("LLM warmup failed:", e)
    threading.Thread(target=run, daemon=True).start()


@app.get("/")
def read_root():
    return FileResponse(BASE / "static" / "index.html")


@app.get("/api/health")
def health_check():
    return {"ok": True, "provider": os.getenv("LLM_PROVIDER", "ollama"),
            "model": os.getenv("OLLAMA_MODEL", "qwen3.5:2b")}


# ---------------- helpers ----------------
def finance_summary(now=None):
    now = now or int(time.time())
    mk = fin.month_key(now, TZ)
    return fin.summary(db.list_expenses(), db.get_budget(mk), now, TZ)


def build_context(now):
    d = datetime.fromtimestamp(now, TZ)
    lines = [f"Now: {d.strftime('%A %d %b %Y, %I:%M %p')} (Bangladesh time)."]
    tasks = db.all_tasks()
    pending = [t for t in tasks if t["status"] == "pending"][:6]
    if pending:
        lines.append("Pending tasks: " + "; ".join(
            f"{t['title']} at {datetime.fromtimestamp(t['due_ts'], TZ).strftime('%d %b %I:%M %p')}"
            for t in pending))
    else:
        lines.append("No pending tasks.")
    ins = ml.insights(tasks, now, TZ)
    lines.append("Habits: " + ml.insights_text(ins))
    if ins["recent_reasons"]:
        lines.append("Recent reasons for missed tasks: " + "; ".join(ins["recent_reasons"]))
    lines.append("Finance: " + fin.summary_text(finance_summary(now)))
    return "\n".join(lines)


CAT_WORDS = {
    "food": ["khabar", "lunch", "dinner", "breakfast", "nasta", "food", "biryani", "cha", "tea", "খাবার"],
    "transport": ["bus", "rickshaw", "cng", "uber", "pathao", "fare", "bhara", "jatayat"],
    "study": ["boi", "book", "khata", "pen", "course", "print", "tuition", "poralekha"],
    "bills": ["bill", "internet", "wifi", "recharge", "rent", "electric", "gas"],
    "shopping": ["kapor", "jama", "shoes", "juta", "shopping", "kenakata"],
    "health": ["medicine", "osudh", "doctor", "hospital", "shasthyo"],
    "entertainment": ["movie", "game", "cinema", "netflix"],
}


def guess_expense_cat(text):
    t = text.lower()
    for cat, words in CAT_WORDS.items():
        if any(w in t for w in words):
            return cat
    return "other"


TASK_CATS = {
    "prayer": ["namaz", "namaj", "prayer", "fajr", "zuhr", "asr", "maghrib", "isha", "quran"],
    "study": ["study", "poro", "read", "assignment", "exam", "class", "lecture"],
    "coding": ["code", "coding", "project", "leetcode", "debug"],
    "health": ["gym", "walk", "exercise", "run", "sleep", "medicine"],
    "household": ["clean", "cook", "laundry", "bazar", "market"],
    "work": ["work", "meeting", "office", "client"],
}


def guess_task_cat(text):
    t = text.lower()
    for cat, words in TASK_CATS.items():
        if any(w in t for w in words):
            return cat
    return "other"


EXP_WORDS = r"(khoroch|kharcha|kharach|spent|spend|expense|kinlam|kenlam|খরচ)"


def try_budget(text):
    m = re.search(r"budget\D{0,12}(\d+(?:\.\d+)?)", text, re.I)
    if not m:
        return None
    amount = float(m.group(1))
    db.set_budget(fin.month_key(int(time.time()), TZ), amount)
    return f"Ei masher budget {round(amount)} Tk set kore dilam."


def try_expense(text):
    if not re.search(EXP_WORDS, text, re.I):
        return None
    n = re.search(r"(\d+(?:\.\d+)?)", text)
    if not n:
        return None
    amount = float(n.group(1))
    purpose = re.sub(EXP_WORDS, " ", text, flags=re.I)
    purpose = re.sub(r"\d+(?:\.\d+)?|\btk\b|\btaka\b|৳|\bon\b|\be\b|\bfor\b|\bkorlam\b", " ", purpose, flags=re.I)
    purpose = " ".join(purpose.split()) or "other"
    cat = guess_expense_cat(purpose)
    db.add_expense(amount, purpose, cat)
    s = finance_summary()
    msg = f"{round(amount)} Tk khoroch likhe rakhlam ({purpose}, {cat})."
    if s["budget"]:
        msg += f" Ei mashe baki {s['remaining']} Tk, ajker safe limit-e {s['today_left']} Tk baki."
    return msg


def parse_due(text, now):
    """Return (title, due_ts) or None. Understands '9pm', '9:30 pm', '21:00', 'kal/tomorrow'."""
    m = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", text, re.I)
    hour = minute = None
    if m:
        hour, minute = int(m.group(1)) % 12, int(m.group(2) or 0)
        if m.group(3).lower() == "pm":
            hour += 12
    else:
        m = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", text)
        if m:
            hour, minute = int(m.group(1)), int(m.group(2))
    if m is None:
        return None
    tomorrow = re.search(r"\b(tomorrow|kal)\b|কাল", text, re.I)
    base = datetime.fromtimestamp(now, TZ)
    due = base.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if tomorrow:
        due += timedelta(days=1)
    elif due.timestamp() <= now:
        due += timedelta(days=1)
    title = text.replace(m.group(0), " ")
    title = re.sub(r"\b(tomorrow|kal|at|e|-)\b|কাল", " ", title, flags=re.I)
    title = " ".join(title.split(" :-")).strip(" :-") or "Task"
    title = " ".join(title.split())
    return title, int(due.timestamp())


def try_task(text, now):
    m = re.match(r"^\s*(task|todo|reminder|kaj)\s*[:\-]?\s*(.+)$", text, re.I)
    if not m:
        return None
    parsed = parse_due(m.group(2), now)
    if not parsed:
        return "Kon somoy-e? Ekhane time likhun, jemon: task: Study 9pm"
    title, due_ts = parsed
    cat = guess_task_cat(title)
    db.add_task(title, due_ts, cat)
    when = datetime.fromtimestamp(due_ts, TZ).strftime("%d %b, %I:%M %p")
    msg = f"Task add holo: {title} ({when})."
    pct, _ = ml.predict_success(db.all_tasks(), due_ts, cat, now, TZ)
    if pct is not None:
        msg += f" Apnar history onujayi complete korar sombhabona prai {pct}%."
    return msg


def handle_commands(text, now):
    return try_budget(text) or try_task(text, now) or try_expense(text)


# ---------------- chat ----------------
class ChatRequest(BaseModel):
    message: str


@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    text = req.message.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Empty message")
    now = int(time.time())
    history = db.get_chat_history(limit=8)
    db.add_message("user", text, now)
    reply = handle_commands(text, now)
    if reply is None:
        try:
            reply = llm.generate_response(text, context=build_context(now), history=history)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    db.add_message("assistant", reply, int(time.time()))
    return {"reply": reply}


@app.post("/api/checkin")
def checkin():
    now = int(time.time())
    prompt = ("Do a short mentor check-in with me: mention my pending tasks, how my habits "
              "and spending look, and give one concrete suggestion for the next few hours.")
    try:
        reply = llm.generate_response(prompt, context=build_context(now))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    db.add_message("assistant", reply, int(time.time()))
    return {"reply": reply}


# ---------------- tasks ----------------
class TaskIn(BaseModel):
    title: str
    due_ts: int
    category: Optional[str] = None


class MissedIn(BaseModel):
    reason: Optional[str] = None


@app.get("/api/tasks")
def get_tasks():
    return db.get_all_tasks()


@app.post("/api/tasks")
def add_task(item: TaskIn):
    cat = item.category or guess_task_cat(item.title)
    tid = db.add_task(item.title.strip(), item.due_ts, cat)
    pct, _ = ml.predict_success(db.all_tasks(), item.due_ts, cat, int(time.time()), TZ)
    return {"id": tid, "predicted_success": pct}


@app.post("/api/tasks/{task_id}/done")
def task_done(task_id: int):
    db.set_task_status(task_id, "done")
    return {"ok": True}


@app.post("/api/tasks/{task_id}/missed")
def task_missed(task_id: int, body: MissedIn):
    db.set_task_status(task_id, "missed", (body.reason or "").strip() or None)
    return {"ok": True}


@app.get("/api/due")
def due_tasks():
    return db.pop_due_tasks(int(time.time()))


# ---------------- finance ----------------
class ExpenseIn(BaseModel):
    amount: float
    purpose: str
    category: Optional[str] = "other"


class BudgetIn(BaseModel):
    amount: float


@app.get("/api/finance")
def get_finance():
    s = finance_summary()
    return {"summary": s, "text": fin.summary_text(s), "expenses": db.list_expenses(limit=8)}


@app.post("/api/expenses")
def add_expense(item: ExpenseIn):
    if item.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    cat = item.category if item.category in fin.FIN_CATS else "other"
    db.add_expense(item.amount, item.purpose.strip(), cat)
    return {"ok": True}


@app.post("/api/budget")
def set_budget(item: BudgetIn):
    db.set_budget(fin.month_key(int(time.time()), TZ), item.amount)
    return {"ok": True}


# ---------------- insights / history ----------------
@app.get("/api/insights")
def get_insights():
    ins = ml.insights(db.all_tasks(), int(time.time()), TZ)
    ins["tip"] = ml.insights_text(ins)
    return ins


@app.get("/api/history")
def get_history():
    return db.get_chat_history(limit=50)
