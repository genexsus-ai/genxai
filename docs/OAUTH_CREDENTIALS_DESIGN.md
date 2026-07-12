# Managed OAuth Credentials — Design

Status: **P1 implemented** (GitHub end-to-end; P2 refresh + Google pending)
Scope: Workflow Studio backend + frontend, small framework-level refresh hook.

## Problem

Connector credentials today are static secrets (API tokens, bot tokens) typed
into the Credentials panel. That works for GitHub PATs and Slack bot tokens,
but the majority of SaaS APIs users will ask for next (Google Workspace,
Microsoft 365, Notion, HubSpot, Salesforce) are OAuth2-first: short-lived
access tokens obtained via a browser consent flow and kept alive with refresh
tokens. Without OAuth support, each of those connectors is effectively
unusable for non-developers — which is the single biggest practical gap
versus n8n's credential system.

## Goals

1. "Connect account" button per provider: click → provider consent screen →
   redirected back → credential stored and usable by connector nodes.
2. Transparent token refresh: workflow runs never fail because an access
   token expired; refresh happens at use time, invisibly.
3. Reuse the existing credential store (encrypted at rest via
   `GENXAI_CONNECTOR_CONFIG_KEY`, write-only through the API) — an OAuth
   credential is just a credential whose config the system maintains.
4. Provider onboarding is data, not code: adding a provider means adding a
   registry entry (auth URL, token URL, scopes), not a new module.

## Non-goals

- A hosted "GenXAI OAuth app" that users piggyback on (n8n cloud model).
  GenXAI is self-hosted; deployments register their **own** OAuth app per
  provider and paste its client ID/secret once (n8n self-hosted works the
  same way). Revisit only if a managed cloud offering ships.
- OAuth 1.0a (Twitter/X legacy) and device-code flows. Out of scope until a
  connector needs them.
- Multi-user consent isolation. The studio is currently single-tenant;
  credentials are deployment-global. RBAC integration is future work.

## Design

### 1. Provider registry (backend, data-driven)

`app/oauth_providers.py`:

```python
OAUTH_PROVIDERS: dict[str, OAuthProviderDef] = {
    "google": OAuthProviderDef(
        auth_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/spreadsheets"],
        extra_auth_params={"access_type": "offline", "prompt": "consent"},
        connector_type="google_workspace",
    ),
    "github":    ...,   # note: GitHub OAuth tokens don't expire by default
    "slack":     ...,   # bot token via OAuth v2, no refresh
    "microsoft": ...,   # MS identity platform, refresh tokens
}
```

Each entry declares: auth/token endpoints, default scopes (overridable per
credential), whether refresh tokens are issued, and which connector type the
resulting credential serves. Scope presets can later be split per-connector
(gmail vs sheets) without changing the flow.

### 2. App registration (BYO client credentials)

A new settings section (Credentials panel → "OAuth apps") stores one
`client_id`/`client_secret` per provider, in the same encrypted store under
reserved names (`__oauth_app__google`). Env-var override
(`GENXAI_OAUTH_GOOGLE_CLIENT_ID/SECRET`) for containerized deployments.
The redirect URI to register with the provider is displayed for copy/paste:
`{api_base}/api/v1/oauth/callback`.

### 3. Authorization flow (backend endpoints)

```
POST /api/v1/oauth/{provider}/start   {credential_name, scopes?}
  → { "authorize_url": "...", "state": "..." }

GET  /api/v1/oauth/callback?code=...&state=...
  → exchanges code, stores credential, returns a tiny HTML page that
    window.close()s (the frontend opened authorize_url in a popup)
```

- `state` is a signed, single-use nonce (stored server-side with a 10-minute
  TTL) binding the callback to the initiating request — CSRF protection.
- PKCE (S256) always: `code_verifier` kept with the pending state; providers
  that ignore PKCE tolerate the extra params.
- On success the credential is written to the existing store:

```json
{
  "name": "my-gmail",
  "connector_type": "google_workspace",
  "config": {
    "auth_kind": "oauth2",
    "provider": "google",
    "access_token": "...",
    "refresh_token": "...",
    "expires_at": "2026-07-11T21:14:00Z",
    "scopes": ["..."]
  }
}
```

Static-secret credentials keep working unchanged (`auth_kind` absent).

### 4. Transparent refresh (the part workflows feel)

`app/oauth_refresh.py` exposes one function used by the connector execution
path (`ConnectorActionTool._execute`, before instantiating the connector):

```python
async def fresh_access_token(entry: ConnectorConfigEntry) -> str:
    # not oauth2 → return static token as-is
    # expires_at more than 60s away → return access_token
    # else → POST token_url with refresh_token, persist rotated tokens,
    #        return new access_token
```

- A per-credential `asyncio.Lock` prevents concurrent refreshes when
  parallel branches use the same credential.
- Refresh failure (revoked consent) surfaces as a node error naming the
  credential: `"Credential 'my-gmail' needs re-authorization"` — and the
  Credentials panel shows a ⚠ badge with a "Reconnect" button (same start
  endpoint, overwrites tokens in place).
- Providers without refresh tokens (GitHub, Slack) skip refresh; if the API
  returns 401 the same "reconnect" UX applies.

### 5. Frontend (CredentialsPanel)

- Provider entries in the connector catalog gain `auth: "oauth2"`. For those,
  the "Add credential" form becomes: name field + **Connect account** button
  (disabled with a hint until the provider's OAuth app is configured).
- Click → `POST /oauth/{provider}/start` → `window.open(authorize_url)` →
  poll `GET /credentials` until the new name appears (or listen for the
  popup closing) → success toast.
- Credential rows show kind (`oauth2` vs `token`), provider, and a
  reconnect action. Secret values remain write-only, as today.

### 6. Security notes

- Tokens live only in the encrypted store; `safe_listing()` continues to
  exclude config values, and new endpoints never echo tokens.
- `state` nonces and PKCE verifiers are held in-memory with TTL (a restart
  aborts in-flight consents — acceptable).
- The callback endpoint validates `state` before touching the code, and the
  token exchange happens server-side; the browser never sees tokens.
- Refresh-token rotation (Google/Microsoft rotate on use) is handled by
  always persisting whatever the token response returns.

## Phasing

| Phase | Contents | Effort |
|---|---|---|
| P1 | Provider registry, start/callback endpoints, PKCE/state, storage schema, GitHub provider (no refresh — simplest end-to-end proof) | ~1 session |
| P2 | Refresh machinery + Google provider (offline access, rotation), reconnect UX | ~1 session |
| P3 | Slack + Microsoft entries, per-connector scope presets, env-var app config | incremental |

## Touched files (P1+P2)

- `backend/app/oauth_providers.py` (new) — registry + defs
- `backend/app/oauth_flow.py` (new) — state store, PKCE, code exchange
- `backend/app/oauth_refresh.py` (new) — `fresh_access_token`
- `backend/app/api/routes.py` — `/oauth/{provider}/start`, `/oauth/callback`,
  OAuth-app CRUD
- `backend/app/connectors_catalog.py` — `auth` field per connector;
  `ConnectorActionTool` calls `fresh_access_token`
- `backend/app/schemas.py` — request/response models
- `frontend/src/components/CredentialsPanel.tsx` — Connect flow, badges
- `frontend/src/api.ts`, `types.ts`
- tests: state/PKCE validation, mocked token exchange, refresh rotation,
  static-credential passthrough

## Open questions

1. Which Google scopes to preset first? (gmail.readonly + spreadsheets is a
   guess — should track which connector actions actually exist.)
2. Popup vs full-page redirect: popup keeps canvas state, but some corporate
   browsers block popups; fallback link should be shown in the panel.
3. Should webhook-provider secrets (GitHub HMAC) eventually merge into the
   same credential store? (Today they live on `AutomationConfig`.)
