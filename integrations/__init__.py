"""External API integrations for fact-checking."""

from .google_factcheck import google_factcheck_search, google_factcheck_multi
from .web_search import web_fallback

__all__ = ["google_factcheck_search", "google_factcheck_multi", "web_fallback"]
