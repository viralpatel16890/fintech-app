# Finance Dashboard

A personal finance tracker built with Python 3.14 + Flask + SQLite. Track income, expenses, budgets, and monthly trends.

## Stack

| Layer | Technology |
|---|---|
| Language | Python 3.14 |
| Framework | Flask |
| Database | SQLite (`finance.db`) |
| Templates | Jinja2 |
| Dependencies | `flask>=2.3.0`, `gunicorn>=21.0.0` |

## Features

- **Dashboard** — monthly income/expense summary, savings rate, category breakdown chart, 6-month trend
- **Transactions** — add, filter, and delete income/expense records
- **Budgets** — set monthly limits per category with live spend tracking
- **Authentication** — session-based login; all routes protected
- **Input validation** — server-side checks on all write operations (amounts, dates, categories)
- **Safe DB connections** — context-manager pattern; auto-commit/rollback, no connection leaks

## Running Locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
# Open http://localhost:5000
```

Default login: `admin` / `changeme` (override with env vars — see below).

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `PORT` | No | Port to listen on (default: `5000`) |
| `SECRET_KEY` | Yes (production) | Flask session secret — set a long random string |
| `LOGIN_USERNAME` | No | Login username (default: `admin`) |
| `LOGIN_PASSWORD` | No | Login password (default: `changeme`) — **change before deploying** |

Set these in your hosting dashboard before going live. Never commit them to source control.

---

## Hosting Plan

### Current: Railway (trial until ~2026-06-30)

- Deploy as-is — no code changes needed
- SQLite file persists across restarts via Railway volumes
- ~$5/month credit covers this app

### Upcoming: Render (free tier, after trial)

Render's free tier requires migrating from SQLite to PostgreSQL:

| Change | Detail |
|---|---|
| Add dependency | `psycopg2-binary` to `requirements.txt` |
| DB driver | Replace `sqlite3` with `psycopg2` |
| Query placeholders | `?` → `%s` |
| Connection | Use `DATABASE_URL` env var (Render provides this) |
| Env vars | Set `SECRET_KEY`, `LOGIN_USERNAME`, `LOGIN_PASSWORD` in Render dashboard |

Render offers a free PostgreSQL instance — pair it with a free web service for $0/month.

---

## Hosting Compatibility Matrix

| Platform | Python | SQLite Persists | Free | Notes |
|---|---|---|---|---|
| GoDaddy Node.js Hosting | No | — | Yes | Node.js only — incompatible |
| Netlify | No | — | Yes | Static/JS only — incompatible |
| Vercel | Partial | No | Yes | Serverless, ephemeral FS |
| **Render** | Yes | No* | Yes | Use free PostgreSQL instead |
| **Railway** | Yes | Yes | $5 credit/mo | Best for SQLite as-is |
| Fly.io | Yes | Yes | Yes | Works, needs Dockerfile |
| GCP Cloud Run | Yes | No | Yes** | Serverless, ephemeral FS |
| GCP Compute Engine | Yes | Yes | Yes** | e2-micro always-free, more setup |
| AWS EC2 | Yes | Yes | 12 mo only | New accounts, t2.micro |
| AWS Lambda | Partial | No | Yes | Serverless, not ideal for Flask |

\* SQLite resets on redeploy — use Render's free PostgreSQL  
\*\* See GCP/AWS free tier notes below

---

## GCP & AWS Free Tier Notes

### Google Cloud Platform
- **Cloud Run** (recommended): Serverless containers, 2M requests/month free forever. SQLite won't persist — pair with Cloud SQL (paid) or swap to PostgreSQL.
- **Compute Engine e2-micro**: 1 VM free *forever* (us-central1/us-west1/us-east1), 30 GB disk. SQLite works. Requires manual server setup (nginx + gunicorn).

### Amazon AWS
- **EC2 t2.micro**: 750 hrs/month free for **12 months** (new accounts only). SQLite works with EBS storage. Needs manual setup.
- **Elastic Beanstalk**: Free orchestration layer over EC2 — same 12-month limit applies.
- **Lambda**: 1M requests/month free forever. Serverless — not well-suited for Flask + SQLite.
- **RDS PostgreSQL**: Free for 12 months (new accounts), db.t3.micro.

### Verdict on GCP/AWS
Both work but have a steeper setup curve compared to Railway/Render. Best use case:
- GCP **e2-micro** if you want SQLite to persist for free, forever, and don't mind a one-time VM setup
- AWS if you already have an account within the 12-month free window
