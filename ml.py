"""Habit analytics + success predictor."""
from collections import defaultdict
from datetime import datetime, timedelta

CATS = ["study", "coding", "prayer", "health", "household", "work", "other"]
SLOT_NAMES = ["morning", "afternoon", "evening", "night"]
STALE_SECONDS = 12 * 3600

def slot_of(hour: int) -> str:
    if 5 <= hour < 12: return "morning"
    if 12 <= hour < 17: return "afternoon"
    if 17 <= hour < 21: return "evening"
    return "night"

def _labelled(tasks, now):
    out = []
    for t in tasks:
        if t["status"] == "done": out.append((t, 1))
        elif t["status"] == "missed": out.append((t, 0))
        elif t["status"] == "pending" and t["due_ts"] < now - STALE_SECONDS: out.append((t, 0))
    return out

def _rate(done, n): return (done + 1) / (n + 2)

def insights(tasks, now, tz):
    lab = _labelled(tasks, now)
    n = len(lab)
    done = sum(y for _, y in lab)
    slots = {s: [0, 0] for s in SLOT_NAMES}
    cats = defaultdict(lambda: [0, 0])
    for t, y in lab:
        s = slot_of(datetime.fromtimestamp(t["due_ts"], tz).hour)
        slots[s][0] += 1; slots[s][1] += y
        cats[t["category"]][0] += 1; cats[t["category"]][1] += y

    by_slot = {s: {"n": v[0], "done": v[1], "rate": round(_rate(v[1], v[0]), 2)} for s, v in slots.items() if v[0] > 0}
    by_cat = {c: {"n": v[0], "done": v[1], "rate": round(_rate(v[1], v[0]), 2)} for c, v in cats.items()}

    enough = {s: v for s, v in by_slot.items() if v["n"] >= 2}
    best = max(enough, key=lambda s: enough[s]["rate"]) if enough else None
    worst = min(enough, key=lambda s: enough[s]["rate"]) if enough else None
    if best == worst: worst = None

    delays = [max(-180, min(720, (t["completed_ts"] - t["due_ts"]) / 60)) for t, y in lab if y == 1 and t["completed_ts"]]
    avg_delay = round(sum(delays) / len(delays)) if delays else None

    reasons = [t["reason"] for t, y in lab if y == 0 and t["reason"]][-5:]

    days = defaultdict(list)
    for t, y in lab: days[datetime.fromtimestamp(t["due_ts"], tz).date()].append(y)
    d = datetime.fromtimestamp(now, tz).date()
    if d not in days: d -= timedelta(days=1)
    streak = 0
    while d in days and all(days[d]):
        streak += 1
        d -= timedelta(days=1)

    return {
        "confirmed_tasks": n, "done": done, "rate": round(done / n, 2) if n else None,
        "by_slot": by_slot, "by_category": by_cat, "best_slot": best, "worst_slot": worst,
        "avg_delay_min": avg_delay, "recent_reasons": reasons, "streak_days": streak,
    }

def insights_text(ins) -> str:
    if not ins["confirmed_tasks"]: return "No history yet."
    lines = [f"Completed {ins['done']} of {ins['confirmed_tasks']} tasks ({round(ins['rate'] * 100)}%). Streak: {ins['streak_days']} days."]
    if ins["best_slot"]: lines.append(f"Best slot: {ins['best_slot']}.")
    return " ".join(lines)

def predict_success(tasks, due_ts, category, now, tz):
    lab = _labelled(tasks, now)
    if len(lab) < 5:
        return None, "not-enough-data"
    slot = slot_of(datetime.fromtimestamp(due_ts, tz).hour)

    def rate(f):
        ys = [y for t, y in lab if f(t)]
        return _rate(sum(ys), len(ys)), len(ys)

    base, _ = rate(lambda t: True)
    cr, cn = rate(lambda t: t["category"] == category)
    sr, sn = rate(lambda t: slot_of(datetime.fromtimestamp(t["due_ts"], tz).hour) == slot)
    p = base + (cn / (cn + 3)) * (cr - base) + (sn / (sn + 3)) * (sr - base)
    return round(max(0.05, min(0.95, p)) * 100), "smoothed-rate"
