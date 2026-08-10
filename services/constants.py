"""
Atlas constants.

Central location for all status values used throughout the project.
"""

from __future__ import annotations


# --------------------------------------------------
# Research Products
# --------------------------------------------------

RESEARCH_STATUS_NEW = "NEW"
RESEARCH_STATUS_GENERATED = "GENERATED"


# --------------------------------------------------
# AI Validation
# --------------------------------------------------

VALIDATION_PENDING = "PENDING"
VALIDATION_VALID = "VALID"
VALIDATION_INVALID = "INVALID"


# --------------------------------------------------
# Pinterest Queue
# --------------------------------------------------

QUEUE_PENDING = "PENDING"
QUEUE_READY = "READY"
QUEUE_PUBLISHED = "PUBLISHED"
QUEUE_FAILED = "FAILED"


# --------------------------------------------------
# Pinterest Accounts / Boards / Routes
# --------------------------------------------------

STATUS_ACTIVE = "ACTIVE"
STATUS_INACTIVE = "INACTIVE"


# --------------------------------------------------
# Integration Providers (Accounts Foundation)
# --------------------------------------------------

PROVIDER_PINTEREST = "PINTEREST"
PROVIDER_AMAZON_ASSOCIATES = "AMAZON_ASSOCIATES"
PROVIDER_AI = "AI"

PROVIDERS = (
    PROVIDER_PINTEREST,
    PROVIDER_AMAZON_ASSOCIATES,
    PROVIDER_AI,
)


# --------------------------------------------------
# Connection Status (Accounts Foundation)
# --------------------------------------------------
# is_seed and connection_status are separate concepts. A non-seed account is
# NOT automatically connected; only an explicit CONNECTED state means a real
# external connection exists.

CONNECTION_NOT_CONFIGURED = "NOT_CONFIGURED"
CONNECTION_NOT_CONNECTED = "NOT_CONNECTED"
CONNECTION_CONNECTING = "CONNECTING"
CONNECTION_CONNECTED = "CONNECTED"
CONNECTION_ERROR = "ERROR"
CONNECTION_DISCONNECTED = "DISCONNECTED"
CONNECTION_CONFIGURED = "CONFIGURED"

CONNECTION_STATUSES = (
    CONNECTION_NOT_CONFIGURED,
    CONNECTION_NOT_CONNECTED,
    CONNECTION_CONNECTING,
    CONNECTION_CONNECTED,
    CONNECTION_ERROR,
    CONNECTION_DISCONNECTED,
    CONNECTION_CONFIGURED,
)


# --------------------------------------------------
# AI Providers (safe labels only; config lives in env)
# --------------------------------------------------

AI_PROVIDER_OPENROUTER = "OpenRouter"
AI_PROVIDER_GEMINI = "Gemini"
AI_PROVIDER_OPENAI = "OpenAI"
AI_PROVIDER_CUSTOM = "Custom AI Gateway"


# --------------------------------------------------
# Pinterest OAuth (ATLAS-029C)
# --------------------------------------------------
# Credential types stored in connection_credentials (server-side only,
# never returned by the API). Values are secrets and must never be logged.

CREDENTIAL_PINTEREST_ACCESS_TOKEN = "pinterest_access_token"
CREDENTIAL_PINTEREST_REFRESH_TOKEN = "pinterest_refresh_token"
CREDENTIAL_PINTEREST_TOKEN_EXPIRES_AT = "pinterest_token_expires_at"
CREDENTIAL_PINTEREST_SCOPE = "pinterest_scope"

# OAuth state lifetime (seconds): enough for a user to authorize on
# Pinterest, short enough to bound replay risk.
PINTEREST_STATE_TTL_SECONDS = 600

# Minimal scopes needed by Atlas:
#   user_accounts:read -> identify the authenticated Pinterest user
#   boards:read       -> read the user's boards
#   pins:read         -> future Pin publishing (read side)
#   pins:write        -> future Pin publishing (create side)
# Requested at authorization and, when applicable, at refresh time.
PINTEREST_OAUTH_SCOPES = "user_accounts:read,boards:read,pins:read,pins:write"

# Pinterest OAuth endpoints (current official values).
PINTEREST_AUTHORIZE_URL = "https://www.pinterest.com/oauth/"
PINTEREST_TOKEN_URL = "https://api.pinterest.com/v5/oauth/token"
PINTEREST_API_BASE = "https://api.pinterest.com/v5"
PINTEREST_USER_ENDPOINT = PINTEREST_API_BASE + "/user_account"
PINTEREST_BOARDS_ENDPOINT = PINTEREST_API_BASE + "/boards"

# Env variables that configure the Pinterest OAuth app. Secrets must never
# be read into logs, responses, or the DOM.
PINTEREST_CLIENT_ID_ENV = "PINTEREST_CLIENT_ID"
PINTEREST_CLIENT_SECRET_ENV = "PINTEREST_CLIENT_SECRET"
PINTEREST_REDIRECT_URI_ENV = "PINTEREST_REDIRECT_URI"