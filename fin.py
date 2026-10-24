"""Finance analytics: mashik budget, daily khoroch, projection."""
import calendar
from collections import Counter, defaultdict
from datetime import datetime

FIN_CATS = ["food", "transport", "study", "bills", "shopping", "health", "entertainment", "other"]


def month_key(ts, tz):
    return datetime.fromtimestamp(ts, tz).strftime("%Y-%m")


def summary(expenses, budget, now, tz):
    d = datetime.fromtimestamp(now, tz)
    mk = d.strftime("%Y-%m")
    month_exp = [e for e in expenses if month_key(e["ts"], tz) == mk]
    spent = sum(e["amount"] for e in month_exp)
    today = d.date()
    today_spent = sum(e["amount"] for e in month_exp if datetime.fromtimestamp(e["ts"], tz).date() == today)

    dim = calendar.monthrange(d.year, d.month)[1]
    day = d.day
    days_left = dim - day + 1  # ajker din soho
    daily_avg = spent / day
    projected = daily_avg * dim

    by_cat = defaultdict(float)
    purposes = Counter()
    for e in month_exp:
        by_cat[e["category"]] += e["amount"]
        purposes[e["purpose"].strip().lower()] += e["amount"]
    by_category = {c: {"amount": round(v), "pct": round(v / spent * 100) if spent else 0}
                   for c, v in sorted(by_cat.items(), key=lambda kv: -kv[1])}
    top_purposes = [{"purpose": p, "amount": round(a)} for p, a in purposes.most_common(5)]

    out = {
        "month": mk, "budget": budget, "spent": round(spent), "today_spent": round(today_spent),
        "daily_avg": round(daily_avg), "projected": round(projected),
        "days_left": days_left, "by_category": by_category, "top_purposes": top_purposes,
        "remaining": None, "safe_daily": None, "today_left": None, "status": "no_budget",
    }
    if budget:
        out["remaining"] = round(budget - spent)
        safe = max(0.0, (budget - (spent - today_spent)) / days_left)  # ajker shoho baki dine proti din
        out["safe_daily"] = round(safe)
        out["today_left"] = round(safe - today_spent)
        if spent > budget:
            out["status"] = "over"
        elif day >= 3 and projected > budget:
            out["status"] = "at_risk"
        else:
            out["status"] = "on_track"
    return out


def summary_text(s) -> str:
    if not s["spent"] and not s["budget"]:
        return "No budget set and no expenses recorded this month."
    lines = []
    if s["budget"]:
        lines.append(f"Monthly budget: {s['budget']} Tk. Spent so far: {s['spent']} Tk. Remaining: {s['remaining']} Tk "
                     f"with {s['days_left']} days left (including today).")
        lines.append(f"Safe daily spending from now: about {s['safe_daily']} Tk/day. Spent today: {s['today_spent']} Tk "
                     f"(room left today: {s['today_left']} Tk).")
        lines.append(f"At the current pace the month would end at about {s['projected']} Tk. Status: {s['status']}.")
    else:
        lines.append(f"NO monthly budget set yet. Spent so far this month: {s['spent']} Tk (avg {s['daily_avg']} Tk/day).")
    if s["by_category"]:
        lines.append("Spending by category: " + ", ".join(
            f"{c} {v['amount']} Tk ({v['pct']}%)" for c, v in s["by_category"].items()))
    if s["top_purposes"]:
        lines.append("Biggest purposes: " + ", ".join(f"{p['purpose']} {p['amount']} Tk" for p in s["top_purposes"]))
    return "\n".join(lines)
