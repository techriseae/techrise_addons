# Techrise Workspace License

Central licence registry for the **TechRise HR mobile app**. Client Odoo
instances (with `techrise_mobile_api`) and the app itself call
`POST /techrise/workspace/check` with the client's `database.uuid`.

- Unknown workspace → registered as **Trial**, 30 days from today
  (`techrise_workspace.trial_days`).
- Trial/active past its end date → **Expired** (clients go read-only).
- **Blocked** → the app refuses sign-in.
- Activate / Block / Reset from **Techrise → Workspaces**.

## Install

On `157.230.90.9`, pull the module changes and upgrade it on the **same
database as `techrise_device_license`** so the shared
`techrise_license.signing_key_path` parameter applies:

```bash
cd /odoo18/techrise_addons
git pull --ff-only
/odoo18/venv/bin/python /odoo18/odoo18-server/odoo-bin \
  -c /etc/odoo18-server.conf -d <existing_device_license_database> \
  -u techrise_workspace_license --stop-after-init
```

Replace `<existing_device_license_database>` with the actual database name.
Run the upgrade as the Odoo service user during the deployment maintenance
window, then restart the service. Ensure `cryptography` is installed in the
Odoo virtual environment and the service user can read the signing key.
Verify the actual Odoo listening port using the running service configuration
and `ss -ltnp` **before writing nginx rules**; replace the example port below
with that verified port.

## Lifecycle

| Admin state | Effective status handed to clients |
|-------------|-------------------------------------|
| Trial       | `trial` until `trial_end`, then `expired` |
| Active      | `active`; `expired` once `licence_end` has passed (blank = perpetual) |
| Expired     | `expired` (also written by the daily cron once a date has passed) |
| Blocked     | `blocked` — `verified: false`, sign-in refused |

Buttons on the workspace form:

- **Activate** — `state = active`. Set `licence_end` first for a fixed-term
  licence, or leave it blank for perpetual.
- **Block** — `state = blocked`. The app refuses sign-in on its next check.
- **Reset to Trial** — restarts the 30-day clock from today and **clears
  `licence_end`** so a stale date from a previous active period cannot leak
  into the new trial's end date.

Identity is the client's `db_uuid`. A server URL or database rename does not
reset the trial; the display fields (`name`, `server_url`, `db_name`) are
simply refreshed from the latest check.

## Signature

Responses are Ed25519-signed with the key configured for
`techrise_device_license` (`techrise_license.signing_key_path`). Message:
`techrise-workspace:v1\n<db_uuid>\n<status>\n<ends>\n<iat>`.

Public key for clients:
```bash
python3 - <<'EOF'
from cryptography.hazmat.primitives import serialization
k = serialization.load_pem_private_key(open('/etc/techrise/license_ed25519_private.pem','rb').read(), None)
import base64; print(base64.b64encode(k.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)).decode())
EOF
```
Requires HTTPS on a real hostname (`license.techriseae.com`) — see the v2 design spec §4.5.

## Deployment hardening

`/techrise/workspace/check` is `auth='public'`, unauthenticated and
unthrottled at the Odoo level. Put the following in place before exposing it.

### Rate limit per IP (nginx)

```nginx
# http {} block
limit_req_zone $binary_remote_addr zone=techrise_check:10m rate=10r/m;

# server {} block for license.techriseae.com
location = /techrise/workspace/check {
    limit_req zone=techrise_check burst=20 nodelay;
    limit_req_status 429;
    proxy_pass http://127.0.0.1:8069;
    include proxy_params;   # must forward X-Forwarded-For / X-Real-IP
}
```

A healthy client checks once per app launch plus once every few hours; 10/min
with a burst of 20 leaves ample headroom while stopping registration floods
(each unknown `db_uuid` creates a row). Raise `rate`/`burst` if a customer
site puts many phones behind one NAT address — a 429 is harmless (the app
keeps its cached, signed envelope) but noisy.

### Single database / `dbfilter`

`auth='public'` only binds when Odoo can resolve exactly one database for the
request. Run the licence server with a single database, or set
`dbfilter = ^techrise_license$` (or `db_name = ...`) in the server config.
Without this the endpoint answers with a database-selector error and clients
fall back to their cached envelope.

### `proxy_mode = True`

`last_ip` is taken from `request.httprequest.remote_addr`. Behind nginx that
is `127.0.0.1` unless `proxy_mode = True` is set in the Odoo config **and**
nginx forwards `X-Forwarded-For`. Do not enable `proxy_mode` on a server that
is reachable directly (the header would then be client-controlled).

### HTTPS only

Serve the endpoint on `https://license.techriseae.com` only. Redirect plain
HTTP to HTTPS and do not expose the Odoo port directly. Clients pin the
Ed25519 public key, so TLS protects the *request* (the `db_uuid` and
metadata) rather than the response's integrity — but it still matters.

### What a `db_uuid` holder can and cannot do

Anyone who knows a client's `db_uuid` can call the endpoint and thereby
**rewrite that workspace's display metadata** (`name`, `server_url`,
`db_name`, `app_versions`, telemetry counters). This is by design — the
client refreshes its own record on every check and there is no secret to
share with a brand-new install.

What they **cannot** do: change the workspace's `state`, `trial_start`,
`trial_end` or `licence_end`. Those are written only from the backend form
(Activate / Block / Reset) and the expiry cron. Treat the display fields as
informational and the dated/status fields as authoritative.
