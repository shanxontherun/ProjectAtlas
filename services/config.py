"""
Atlas configuration.

Project-wide settings.
"""

from __future__ import annotations


# --------------------------------------------------
# AI Validation
# --------------------------------------------------

SEO_TITLE_MIN_LENGTH = 20

PINTEREST_TITLE_MIN_LENGTH = 20
PINTEREST_TITLE_MAX_LENGTH = 100

PINTEREST_DESCRIPTION_MIN_LENGTH = 100
PINTEREST_DESCRIPTION_MAX_LENGTH = 500

MIN_KEYWORDS = 5

INSTAGRAM_CAPTION_MIN_LENGTH = 30

BLOG_SUMMARY_MIN_LENGTH = 100


# --------------------------------------------------
# Queue
# --------------------------------------------------

QUEUE_BATCH_SIZE = 100


# --------------------------------------------------
# Publisher
# --------------------------------------------------

PUBLISH_BATCH_SIZE = 10

MAX_RETRY_COUNT = 3