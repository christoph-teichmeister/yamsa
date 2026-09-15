# yamsa: logging in

App-specific login flow, so this doesn't need rediscovering per session. Full background
(auth mechanism, seed command, all test accounts) is in `docs/ai/testing.md` — this file is
just the copy-paste `playwright-cli` version.

## 1. Find the running server's port

Scripts and `docker-compose.yml` default to `8000`; the README's manual instructions use
`8002`. Don't assume — check what's actually listening:

```bash
lsof -iTCP -sTCP:LISTEN -P | grep -E ':(8000|8002)'
# or, if using docker-compose:
docker compose ps backend
```

## 2. Seed test data (once per DB reset)

```bash
uv run python manage.py restore_test_data
```

Creates (all password `Admin123$`):

- Superuser: `admin@yamsa.local`
- Registered users: `registered_user_1@yamsa.local` … `registered_user_5@yamsa.local`

Guest users (`guest_1`…`guest_5`) are also seeded but cannot log in through this form — they
have no usable password by design and only authenticate via a room-invite link.

## 3. Log in

```bash
playwright-cli open http://localhost:8000/account/login/
playwright-cli fill "#id_email" "admin@yamsa.local"
playwright-cli fill "#id_password" "Admin123$"
playwright-cli click "#login-submit-button"
playwright-cli snapshot
```

A rejected login re-renders the same URL and shows `#login-error`; a successful one redirects
away from `/account/login/`.
