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