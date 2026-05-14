# JobHunter — Project Runbook (for Rakshith + Claude Code)

This single file is the source of truth for shipping JobHunter. It's both a
human-facing checklist and a brief Claude Code can act on. Each phase has:

- **What it does** — one-line outcome
- **Status** — `[ ]` not done · `[x]` done · `[~]` in progress
- **Run it yourself** — copy-paste commands
- **Or give to Claude Code** — a self-contained prompt block

---

## Project overview

JobHunter is a personalised cold-email job-application bot. It has two sibling
folders under `Cold Email/`:

| Folder | Audience | Goes to GitHub? |
|---|---|---|
| **`JobHunter/`** | End users (your friends) | optional — usually shipped as `.exe` |
| **`JobHunter-Admin/`** *(this folder)* | You, Rakshith, only | yes — connects to Render |

The **admin folder** contains the license server (deployed to Render free tier)
plus the CLI tool that generates activation keys. End users never see this folder.

### Architecture in 30 seconds

```
End user laptop                              Render (your free server)
┌────────────────────┐                       ┌──────────────────────┐
│ JobHunter-Setup.exe│  POST /api/activate   │ jobhunter-license    │
│  (you build &      │  ──────────────────►  │  (this folder's      │
│   distribute)      │     {key, fp}         │   license_server/)   │
│                    │                       │                      │
│                    │  signed token         │  marks key=used,     │
│                    │  ◄──────────────────  │  binds to fp         │
│                    │                       │                      │
│ Locally cached     │                       │ SQLite DB tracks     │
│ token → never      │                       │ all keys & attempts  │
│ phones home again  │                       │                      │
└────────────────────┘                       └──────────────────────┘
                                                       ▲
                                                       │ X-Admin-Token
                                             ┌──────────────────────┐
                                             │ You run:             │
                                             │   tools/             │
                                             │   license_admin.py   │
                                             │   generate ...       │
                                             └──────────────────────┘
```

---

## Where we are right now

- [x] Keypair generated (`keys/private_key.pem`, `keys/public_key.pem`)
- [x] Public key embedded in `../JobHunter/app/license_manager.py`
- [x] `.gitignore` blocks `keys/`, `*.pem`, `.env`
- [ ] **Pushed to GitHub** ← you are here
- [ ] Render service deployed
- [ ] `SERVER_URL` in the client updated to point at your Render URL
- [ ] `.env` created with admin token
- [ ] First activation key generated and test-activated locally
- [ ] Windows installer (`JobHunter-Setup.exe`) built and shippable

---

## Phase 1 — Push this folder to GitHub  `[ ]`

**Target repo:** <https://github.com/rakshi886/Job-Hunter> (private, empty)

### Run it yourself (PowerShell)

```powershell
cd "C:\Users\raksh\OneDrive\Documents\Claude\Projects\Cold Email\JobHunter-Admin"
git init -b main
git add .
git status                                  # SANITY CHECK — see below
git commit -m "Initial license server + admin tools"
git remote add origin https://github.com/rakshi886/Job-Hunter.git
git push -u origin main
```

**Expected `git status` output — exactly 9 files staged:**

```
new file:   .gitignore
new file:   CLAUDE.md
new file:   README.md
new file:   license_server/Procfile
new file:   license_server/README.md
new file:   license_server/app.py
new file:   license_server/render.yaml
new file:   license_server/requirements.txt
new file:   tools/generate_keypair.py
new file:   tools/license_admin.py
```

If `git status` mentions anything containing `.pem`, `.env`, or `keys/` —
**stop**. The gitignore failed. Ask Claude Code to debug.

### Or give to Claude Code

````
# Brief — Push JobHunter-Admin to GitHub

You're a senior developer. Push the JobHunter-Admin folder to a private GitHub
repo. Do NOT touch the sibling JobHunter/ folder.

Working directory:
  C:\Users\raksh\OneDrive\Documents\Claude\Projects\Cold Email\JobHunter-Admin

Target repo (private, currently empty):
  https://github.com/rakshi886/Job-Hunter

## CRITICAL safety check

The folder contains `keys/private_key.pem` — leaking this is catastrophic
(license forgery). A `.gitignore` already blocks `keys/`, `*.pem`, and `.env`.

Before pushing:
  1. Run `git status --ignored` and show me the output.
  2. Confirm `keys/` and (if present) `.env` are in the "Ignored files" list.
  3. Confirm the "Changes to be committed" section does NOT include any
     `.pem` or `.env` file. If anything in there matches, STOP and tell me.

## Commands

  1. Verify Git for Windows is installed: `git --version`. If missing, tell me.
  2. `git rev-parse --is-inside-work-tree`. If `true`, the folder already has a
     repo — run `git remote -v` and confirm it points at
     github.com/rakshi886/Job-Hunter. If origin points anywhere else, ASK
     ME first.
  3. `git init -b main`  (only if step 2 errored)
  4. `git add .`
  5. Safety check (above). If clean, continue.
  6. `git commit -m "Initial license server + admin tools"`
  7. `git remote add origin https://github.com/rakshi886/Job-Hunter.git`
  8. `git push -u origin main`

## Auth

The push will pop a Git Credential Manager browser window. I (the human) will
handle that. Don't try to script auth.

## On failure

  - "remote contains work that you do not have" → repo isn't empty. Tell me.
  - 401/403 → auth issue. Tell me.
  - Do NOT force-push.
  - Do NOT add `-f` to bypass gitignore.

## Done criteria

Paste all three to me at the end:
  - `git status` showing "up to date with 'origin/main'"
  - `git ls-remote https://github.com/rakshi886/Job-Hunter.git` showing main
  - `git log --oneline -1`
````

### Common errors

| Error | Fix |
|---|---|
| `git: command not found` | Install Git for Windows: <https://git-scm.com/download/win> |
| `support for password authentication was removed` | Git for Windows pops a browser for OAuth. Accept it. |
| `remote contains work that you do not have` | Repo isn't empty. Either pull-rebase, or recreate it empty on GitHub. |
| `Updates were rejected because the tip of your current branch is behind` | Same as above. |

---

## Phase 2 — Deploy to Render  `[ ]`

### Steps (~10 min, in browser)

1. Go to <https://render.com> → sign up with your GitHub account.
2. Click **New → Blueprint**.
3. Connect repo `rakshi886/Job-Hunter`.
4. Render auto-reads `license_server/render.yaml` and asks for three env vars:

   - **`PRIVATE_KEY_PEM`** — paste contents of `keys/private_key.pem`
     (include the `-----BEGIN/END PRIVATE KEY-----` lines)
   - **`PUBLIC_KEY_PEM`** — paste contents of `keys/public_key.pem`
   - **`ADMIN_TOKEN`** — click **Generate Value**. **Save what it shows you** —
     this is the only time you can see it.

5. Click **Apply**. Render builds + deploys (~2 minutes).
6. From the service page, copy the public URL — it'll look like
   `https://jobhunter-license-XXXX.onrender.com`.

### Verify it's alive

```powershell
curl https://jobhunter-license-XXXX.onrender.com/healthz
# expected: ok
```

First request can take 30 seconds (free tier is asleep). Normal.

### Where the bodies are buried

- `render.yaml` already pins the right Python runtime, mounts a 1 GB disk at
  `/var/data` for the SQLite DB, and sets `LICENSE_DB_DIR=/var/data`.
- The service sleeps after 15 min of no traffic. Wake time ~30 s. Fine for an
  installer that hits it once.

---

## Phase 3 — Wire your Render URL into the client  `[ ]`

Once you have the Render URL, edit **one line** in the client:

File: `../JobHunter/app/license_manager.py`

Find:
```python
SERVER_URL = "https://jobhunter-license.onrender.com"   # ← replace after deploy
```

Replace with your actual URL:
```python
SERVER_URL = "https://jobhunter-license-XXXX.onrender.com"
```

### Or give to Claude Code

```
# Brief — Update SERVER_URL in license_manager.py

In  C:\Users\raksh\OneDrive\Documents\Claude\Projects\Cold Email\JobHunter\app\license_manager.py
replace the line:
    SERVER_URL = "https://jobhunter-license.onrender.com"   # ← replace after deploy
with:
    SERVER_URL = "<MY_RENDER_URL_GOES_HERE>"

Keep everything else in the file unchanged. Verify with:
  python -m py_compile app/license_manager.py
```

---

## Phase 4 — Set up `.env` for the admin CLI  `[ ]`

Create `JobHunter-Admin/.env` with two lines:

```
SERVER_URL=https://jobhunter-license-XXXX.onrender.com
ADMIN_TOKEN=<the value Render generated for you>
```

`.gitignore` already blocks `.env` so it never goes to GitHub. Verify:

```powershell
cd "C:\Users\raksh\OneDrive\Documents\Claude\Projects\Cold Email\JobHunter-Admin"
git status                  # .env should NOT appear
```

If `.env` shows up in `git status`, something is wrong — stop, don't commit.

---

## Phase 5 — Generate first key & test  `[ ]`

```powershell
cd "C:\Users\raksh\OneDrive\Documents\Claude\Projects\Cold Email\JobHunter-Admin"
pip install requests
python tools/license_admin.py stats
python tools/license_admin.py generate --customer "Rakshith (self-test)"
```

The second command prints a key like `JHTR-XXXX-XXXX-XXXX-XXXX`. Use this key
to test the JobHunter installer on your own machine.

### Useful admin commands

```powershell
python tools/license_admin.py generate --customer "Friend Name" --email "f@x.com"
python tools/license_admin.py generate --count 10
python tools/license_admin.py generate --customer "Trial" --valid-days 30
python tools/license_admin.py list
python tools/license_admin.py list --status available
python tools/license_admin.py inspect JHTR-XXXX-XXXX-XXXX-XXXX
python tools/license_admin.py revoke  JHTR-XXXX-XXXX-XXXX-XXXX --reason "shared"
python tools/license_admin.py stats
```

---

## Phase 6 — Build the Windows installer  `[ ]`

This is documented in `../JobHunter/installer/windows/README.md`. Short version:

1. Install **Inno Setup 6** from <https://jrsoftware.org/isinfo.php>.
2. `pip install pyinstaller Pillow`.
3. Make sure `SERVER_URL` and `EMBEDDED_PUBLIC_KEY` in `app/license_manager.py`
   are set correctly (Phase 3 above).
4. From `JobHunter\installer\windows\`, double-click `build.bat`.
5. Output: `Output/JobHunter-Setup.exe` — this is the file you ship.

Test it on your own machine first, using a key you generated in Phase 5.

---

## Daily ops — handing out keys to friends

```powershell
cd "C:\Users\raksh\OneDrive\Documents\Claude\Projects\Cold Email\JobHunter-Admin"
python tools/license_admin.py generate --customer "Friend's Name" --email "their@email"
```

Email them the key + the `JobHunter-Setup.exe`. Done.

If they ever come back saying "the key doesn't work on my new laptop":

```powershell
python tools/license_admin.py inspect JHTR-XXXX-XXXX-XXXX-XXXX
# look at the bound fingerprint, decide whether to revoke + reissue
python tools/license_admin.py revoke JHTR-XXXX-XXXX-XXXX-XXXX --reason "device change"
python tools/license_admin.py generate --customer "Friend (re-issue)"
```

---

## Quick reference

| File | What it is |
|---|---|
| `keys/private_key.pem` | **NEVER COMMIT** — used by Render server to sign tokens |
| `keys/public_key.pem` | Pasted into `JobHunter/app/license_manager.py` and Render env |
| `.env` | Local-only — your Render URL + admin token |
| `license_server/app.py` | The Flask server deployed on Render |
| `license_server/render.yaml` | Render Blueprint — tells Render how to build & run |
| `tools/license_admin.py` | CLI you run daily to mint / inspect / revoke keys |
| `tools/generate_keypair.py` | Run **once** to create the keypair (already done) |

---

## Troubleshooting

### Render service won't start

- Check the deploy log on the Render dashboard.
- Most common cause: `PRIVATE_KEY_PEM` env var not set, or missing the BEGIN/END
  PEM lines when you pasted it.
- Fix: Settings → Environment → edit `PRIVATE_KEY_PEM` → make sure the value
  starts with `-----BEGIN PRIVATE KEY-----` and ends with `-----END PRIVATE KEY-----`.

### `license_admin.py` returns 401

- `ADMIN_TOKEN` mismatch between `.env` and the Render env var.
- Get the current Render token: Render dashboard → service → Environment → look
  at `ADMIN_TOKEN`'s value (you may need to "Reveal").
- Paste it into `JobHunter-Admin/.env`.

### A user's activation says "key already used on different device"

- Either they really did already activate it elsewhere, OR they reinstalled and
  the fingerprint changed (rare).
- `python tools/license_admin.py inspect <key>` shows the bound fingerprint.
- If you trust them: `revoke` + `generate` a new key.

### I lost my private key

- Restart from scratch: `python tools/generate_keypair.py`, push the new
  `public_key.pem` to `app/license_manager.py`, re-deploy Render with the new
  `PRIVATE_KEY_PEM`, **every existing user's activation breaks**.
- Don't lose the private key.

---

## What NOT to do

- **Never commit `keys/`, `*.pem`, or `.env`.**
- Never put admin endpoints behind a weak token. The current `ADMIN_TOKEN` from
  Render is fine — just don't replace it with something short.
- Don't `force push` to this repo — if Render is auto-deploying, a force push
  could break the prod service.
- Don't deploy the JobHunter client to GitHub Pages or any public host. Ship it
  as a `.exe`, never as source.
