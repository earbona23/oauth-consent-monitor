# oauth-consent-monitor

**Catch the illicit consent grant — the Microsoft 365 attack where a user is tricked into
approving a third-party app that then reads their mail and keeps a refresh token — by
watching your tenant's OAuth consents and flagging the ones that fit the pattern.**

![CI](https://github.com/earbona23/oauth-consent-monitor/actions/workflows/ci.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/license-MIT-blue)
![Read-only](https://img.shields.io/badge/tenant%20access-read--only-brightgreen)

Read-only, always — it never revokes or modifies a grant, and a test enforces that.

---

## The problem

Illicit consent is one of the most effective attacks against M365 because it never touches
a password or trips MFA. A user clicks "Accept" on a convincing-looking app, and it walks
away with `Mail.Read` and `offline_access` — the ability to read their mail and a refresh
token to keep doing it. No failed login, no malware, nothing for the usual alerts to catch.

Meanwhile the tenant's consent surface — every third-party and gallery app a user or admin
ever approved — grows quietly, and nobody reviews the new arrivals. **This watches that door.**

## See it in 10 seconds — no tenant required

```bash
git clone https://github.com/earbona23/oauth-consent-monitor
cd oauth-consent-monitor
python -m monitor.cli --demo
```

Everything is `DEMO DATA`. The output puts the illicit-consent pattern first:

```
⚠ SOSPECHOSO  Free PDF Converter Pro
      consented by: user ana.gomez@contoso.com   ·   max risk: high
        • Mail.Read (high) — reads all of the user's mail. Classic illicit-consent exfiltration.
        ⚠ Persistence + data access (offline_access with a data scope)
        ⚠ Consented by a user (not an admin) with a high-risk scope
        ⚠ App from another organization (multi-tenant)
```

![Demo output](docs/screenshot.png)

It separates that from the merely high-but-admin-approved app, so the one that looks like an
attack stands out from the ones that are just business as usual.

## What makes the detection smart

The tool scores each granted scope from an editable catalog
([`rules/consent_risk.yaml`](rules/consent_risk.yaml)) — but the illicit-consent signal is
**not any single scope. It's the combination**, which is what actually fingerprints the
attack:

- **Persistence + data:** `offline_access` (a refresh token) together with a data scope like
  `Mail.Read` — read the mail, and keep reading it.
- **User consent, not admin:** a high-risk scope approved by a regular user, not an admin.
  Illicit consent targets users precisely because they can approve without review.
- **Another organization's app:** a multi-tenant app owned outside your tenant carrying
  high-risk scopes.

A consent is flagged `SOSPECHOSO` when it shows at least one of these signals *and* holds a
high-risk scope. A scope the catalog doesn't know is treated as `unknown` — surfaced, never
assumed harmless.

## How this differs from an app-registration audit

This is **not** an audit of the app registrations you own. Its subject is the *consent
surface*: the `oauth2PermissionGrants` — what users and admins granted to apps, usually
third-party — watched over time for new, risky consents. An over-privilege audit of your own
apps answers a different question; this one watches the door third parties come in through.

## Use it on a real tenant

```bash
pip install -r requirements.txt
cp config.example.yaml config.yaml
export OCM_CLIENT_SECRET=...
python -m monitor.cli --live                                  # evaluate now
python -m monitor.cli snapshot --live --salida today.json     # capture, e.g. daily
python -m monitor.cli diff yesterday.json today.json          # what got consented since
```

`diff` evaluates only the *new* consents and exits with code `3` when any is suspicious — so
it works as a scheduled alert (a cron or CI step) that pages you when a risky app is newly
consented, which is exactly when the attack shows up.

**Permissions — all read-only:** `Directory.Read.All` (service principals and grants) and
`User.Read.All` (to resolve who consented). The Graph client exposes only `get()`/`get_all()`,
and `tests/test_readonly_guarantee.py` fails if a write verb appears anywhere.

## Limitations

- **It flags, it doesn't revoke.** Read-only is deliberate — revoking a consent has blast
  radius (you might break a sanctioned integration), so this surfaces candidates for a human.
- **Signals are heuristics, not verdicts.** A multi-tenant app with `Mail.Read` may be an
  approved vendor. The tool ranks what deserves a look; the look is yours.
- **Coverage is delegated grants** (`oauth2PermissionGrants`). Application-permission grants
  to service principals (`appRoleAssignments`) are a natural next step, named here rather
  than silently omitted.
- **`--live` is unit-tested with mocked Graph responses.** Validate against your tenant first.

## Contributing

New entries in the scope-risk catalog are welcome — add the scope, its level, and the
reason. Keep collectors read-only. Run `pytest -q` and `ruff check .`.

## License

MIT — see [LICENSE](LICENSE).
