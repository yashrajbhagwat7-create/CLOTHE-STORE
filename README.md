# Clothe Store (BlueWave Clothing)

A small FastAPI + Jinja2 web application for a clothing store website. It serves static pages (Home, Men, Women, Kids, About) and provides a **Contact Us** form that persists submissions to a local **SQLite** database.

It also includes **security controls** for the contact form:
- Input validation with user-friendly error messages
- **SQLite-backed rate limiting** (fixed-window)
- **UTC daily limit**
- Temporary **IP banning** after repeated burst abuse

---

## Tech Stack (Languages & Frameworks)

- **Python 3.13+**
- **FastAPI** (web framework)
- **Jinja2** (server-side HTML templating via `Jinja2Templates`)
- **HTML/CSS** (static site UI)
- **SQLite** (local persistence)
- (Standard library)
  - `sqlite3`, `dataclasses`, `time`, `os`, `datetime`

---

## Project Structure

- `main.py`
  - FastAPI app bootstrap
  - mounts `static/` at `/static`
  - includes router from `app/routes/pages.py`

- `app/routes/pages.py`
  - All HTTP routes
  - Renders templates for:
    - `/`, `/men`, `/women`, `/kids`, `/about`
  - Contact form:
    - `GET /contact` (prefill support using query params)
    - `POST /contact` (validation + rate limit + persistence)

- `app/core/contact_db.py`
  - SQLite schema creation (table `contact_submissions`)
  - `save_submission()` to persist contact messages

- `app/core/rate_limiter.py`
  - SQLite schema + logic for:
    - `contact_rate_limits` (fixed-window counters)
    - `ip_bans` (temporary bans)
    - `contact_burst_violations` (counts burst violations per UTC day)

- `templates/`
  - `index.html`, `men.html`, `women.html`, `kids.html`, `about.html`, `contact.html`
  - `templates/partials/seo.html` (shared SEO meta tags)

- `static/`
  - `style.css`
  - `images/` (hero/banner images)

---

## Key Techniques / Implementation Notes

### 1) Server-side rendering (SSR) with Jinja2
Routes use `Jinja2Templates` and `TemplateResponse` to render HTML with:
- `store` context (store details)
- form prefill context on `GET /contact`
- success/error context on `POST /contact`

### 2) Contact form validation + error handling
On `POST /contact`, the server validates:
- `name`: 2–100 chars
- `email`: must contain `@` and <= 255 chars
- `message`: 10–5000 chars
- `subject`: optional

Validation errors return `contact.html` with HTTP 400 and a combined human-readable error message.

### 3) SQLite-backed fixed-window rate limiting
Implemented in `app/core/rate_limiter.py` via:
- window start bucketing (`now // window_seconds`)
- counters stored in SQLite
- `INSERT ... ON CONFLICT ... DO UPDATE` to safely increment per window

Applied checks in `POST /contact`:
- **Daily limit**: 5 submissions per UTC day
- **Burst limit**: 5 submissions per 10 minutes

### 4) IP banning for repeated abuse
If burst attempts fail, the server increments a per-IP **burst violation** counter (per UTC day). After **3** violations, the IP is banned for **1 hour**.

### 5) Persistence to SQLite
`save_submission()` writes a row with:
- `name`, `email`, `subject`, `message`
- `created_at` (UTC ISO timestamp with `Z` suffix)

SQLite database file:
- `data/contact_submissions.sqlite3`

### 6) Static assets
`main.py` mounts:
- `/static` → `static/`

---

## How to Run

### 1) Create a virtual environment (recommended)

```bat
py -3 -m venv .venv
.
```

### 2) Install dependencies

```bat
pip install -r requirements.txt
```

### 3) Start the server

```bat
uvicorn main:app --reload --port 8000
```

### 4) Open in browser
- http://127.0.0.1:8000/

Pages:
- `/` (Home)
- `/men`
- `/women`
- `/kids`
- `/about`
- `/contact`

---

## Requirements

This project relies on FastAPI + Uvicorn + Jinja2.
See `requirements.txt` for the exact versions/ranges.

---

## Notes / Local Data

The application creates/uses the following local folders/files:
- `data/contact_submissions.sqlite3` (created automatically)

No external database service is required.

---

## Security Considerations (Contact Endpoint)

The contact endpoint is protected by:
- server-side validation
- rate limiting (fixed windows)
- daily quota enforcement
- temporary IP bans after repeated burst abuse

(If you deploy publicly, consider adding additional protections like TLS termination, reverse proxy rate limiting, and hardened deployment settings.)

