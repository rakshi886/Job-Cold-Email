# JobHunter License Server

Tiny Flask app that issues and validates JobHunter activation keys.
Designed to run on **Render's free tier** with zero recurring cost.

This folder lives **on your laptop only**. It is never shipped to users.

---

## Architecture

```
       Render (free)                                User's laptop
  ┌────────────────────┐                       ┌──────────────────────┐
  │ license server     │   POST /api/activate  │ JobHunter installer  │
  │ (this folder)      │  ◄──────────────────  │ enters key on first  │
  │                    │                       │ install              │
  │  • SQLite DB       │   signed token        │                      │
  │  • Ed25519 signing │  ──────────────────►  │ saves token locally  │
  └────────────────────┘                       │ never phones home    │
                                               │ again                │
                                               └──────────────────────┘
```

After the one-time activation, the user's app verifies the cached signed token
locally using the embedded public key. Your server can sleep — it's only needed
for the next installation.

---

## One-time setup

### 1. Generate your signing keypair (on your laptop, only once)

```bash
cd JobHunter-Admin
python -m pip install cryptography
python tools/generate_keypair.py
```

This creates `JobHunter-Admin/keys/private_key.pem` and `public_key.pem`.
**Never commit `private_key.pem`** to git or share it.

### 2. Embed the public key in the client

Open `JobHunter/app/license_manager.py` and paste the **entire contents** of
`public_key.pem` into the `EMBEDDED_PUBLIC_KEY` constant near the top of the file.

### 3. Deploy the server to Render

a. Push the `JobHunter-Admin/` folder to a **private** GitHub repo (or just `license_server/`).
b. Go to <https://render.com> → New → Blueprint → connect your repo.
c. Render detects `license_server/render.yaml` and asks you to set env vars:
   - `PRIVATE_KEY_PEM` → paste the entire contents of `keys/private_key.pem`
   - `PUBLIC_KEY_PEM` → paste the entire contents of `keys/public_key.pem`
   - `ADMIN_TOKEN` → Render auto-generates this. **Save it.**
d. Click Apply. After ~2 minutes you'll get a URL like
   `https://jobhunter-license-XXXX.onrender.com`.

### 4. Wire the URL into the JobHunter client

Open `JobHunter/app/license_manager.py` and set:

```python
SERVER_URL = "https://jobhunter-license-XXXX.onrender.com"
```

### 5. Create your `.env` for the admin tool

```bash
# JobHunter-Admin/.env
SERVER_URL=https://jobhunter-license-XXXX.onrender.com
ADMIN_TOKEN=...the value you saved from Render...
```

---

## Daily usage — generating keys for friends

```bash
cd JobHunter-Admin

# One key for a specific person:
python tools/license_admin.py generate --customer "Alice Smith" --email "alice@x.com"

# Bulk keys (for handing out at events, etc.):
python tools/license_admin.py generate --count 20

# Time-limited (must activate within 30 days):
python tools/license_admin.py generate --customer "Trial user" --valid-days 30

# See everything:
python tools/license_admin.py list
python tools/license_admin.py list --status available
python tools/license_admin.py list --status used

# Inspect one key (when was it activated, from which IP, attempts log):
python tools/license_admin.py inspect JHTR-XXXX-YYYY-ZZZZ-AAAA

# Kill a key if abused:
python tools/license_admin.py revoke JHTR-XXXX-YYYY-ZZZZ-AAAA --reason "shared on Twitter"

# Overall stats:
python tools/license_admin.py stats
```

---

## Render free tier — practical notes

- Free web service sleeps after 15 min of inactivity. First request after a sleep
  takes ~30 seconds. That's fine for an installer — the user only hits the server
  once.
- 750 web hours/month free across all services on your account.
- 1 GB persistent disk attached at `/var/data` (where the SQLite DB lives).
- Auto-deploys on every git push if you connected a GitHub repo.

---

## Local testing (optional)

```bash
cd license_server
python -m pip install -r requirements.txt
export ADMIN_TOKEN=devtoken
export PRIVATE_KEY_PEM="$(cat ../keys/private_key.pem)"
export PUBLIC_KEY_PEM="$(cat ../keys/public_key.pem)"
python app.py
# server now at http://localhost:8080
```

Then in another shell:

```bash
curl -X POST http://localhost:8080/api/admin/keys \
     -H "X-Admin-Token: devtoken" -H "Content-Type: application/json" \
     -d '{"customer_name": "Test"}'
```

---

## Endpoints

| Endpoint                       | Auth         | Purpose                                       |
|--------------------------------|--------------|-----------------------------------------------|
| `GET /healthz`                 | none         | Health check (used by Render)                 |
| `POST /api/activate`           | none         | Installer phones home with key + fingerprint  |
| `POST /api/admin/keys`         | X-Admin-Token | Create one or many keys                       |
| `GET  /api/admin/keys`         | X-Admin-Token | List keys (filter by status)                  |
| `GET  /api/admin/keys/<key>`   | X-Admin-Token | Inspect a single key + recent attempts        |
| `DELETE /api/admin/keys/<key>` | X-Admin-Token | Revoke a key                                  |
| `GET  /api/admin/stats`        | X-Admin-Token | Counts overview                               |
