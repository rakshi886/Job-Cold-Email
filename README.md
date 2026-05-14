# JobHunter Admin

This folder stays **on your laptop**. It is never shipped to users.

```
JobHunter-Admin/
├── license_server/        ← deploy to Render free tier (one-time)
├── tools/
│   ├── generate_keypair.py   ← run once to create your signing keys
│   └── license_admin.py      ← daily CLI for generating/managing keys
├── keys/                  ← created by generate_keypair.py (gitignored)
│   ├── private_key.pem       ← NEVER commit, NEVER share
│   └── public_key.pem        ← paste into JobHunter/app/license_manager.py
└── .env                   ← SERVER_URL + ADMIN_TOKEN (gitignored)
```

## First-time setup checklist

1. **Generate keypair:**
   ```
   cd JobHunter-Admin
   pip install cryptography requests
   python tools/generate_keypair.py
   ```

2. **Deploy server to Render** — see `license_server/README.md`.

3. **Embed public key in client:** open `../JobHunter/app/license_manager.py`,
   paste `keys/public_key.pem` contents into `EMBEDDED_PUBLIC_KEY`.

4. **Set server URL in client:** same file, set `SERVER_URL` to your Render URL.

5. **Create `.env`** with `SERVER_URL` and `ADMIN_TOKEN`.

6. **Test:**
   ```
   python tools/license_admin.py stats
   python tools/license_admin.py generate --customer "Test"
   ```

## Daily usage

```
python tools/license_admin.py generate --customer "Friend's Name"
# → outputs key like JHTR-ABCD-EFGH-JKLM-NPQR
```

Send the key to your friend. They paste it into JobHunter's installer.
Done.
