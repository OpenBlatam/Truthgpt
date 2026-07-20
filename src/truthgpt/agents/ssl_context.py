"""
SSL trust setup for HTTPS clients (httpx, urllib).

On Windows, Python often lacks a usable CA bundle and fails with:
  CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate

Import and call ensure_ssl_certificates() before any httpx/urllib HTTPS call.
"""

from __future__ import annotations

import logging
import os
import sys

logger = logging.getLogger(__name__)
_applied = False


def ensure_ssl_certificates() -> None:
    """Configure SSL trust store before httpx or urllib make HTTPS requests."""
    global _applied
    if _applied:
        return
    _applied = True

    if os.environ.get("TRUTHGPT_SSL_VERIFY", "1").lower() in ("0", "false", "no"):
        logger.warning(
            "TRUTHGPT_SSL_VERIFY is disabled — HTTPS certificate verification is off (dev only)."
        )
        return

    if sys.platform == "win32":
        try:
            import pip_system_certs  # noqa: F401

            logger.debug("SSL: using Windows system certificate store (pip-system-certs)")
            return
        except ImportError:
            logger.debug("pip-system-certs not installed; falling back to certifi")

    try:
        import certifi

        cafile = certifi.where()
        if not os.environ.get("SSL_CERT_FILE"):
            os.environ["SSL_CERT_FILE"] = cafile
        if not os.environ.get("REQUESTS_CA_BUNDLE"):
            os.environ["REQUESTS_CA_BUNDLE"] = cafile
        logger.debug("SSL: using certifi CA bundle at %s", cafile)
    except ImportError:
        logger.warning(
            "certifi not installed. HTTPS may fail with CERTIFICATE_VERIFY_FAILED. "
            "Install: pip install certifi pip-system-certs"
        )


def httpx_verify_setting():
    """Return the verify= argument for httpx clients (True, False, or SSL context path)."""
    if os.environ.get("TRUTHGPT_SSL_VERIFY", "1").lower() in ("0", "false", "no"):
        return False
    return True


def ssl_error_hint(exc: BaseException) -> str | None:
    """Return a user-facing hint when exc looks like an SSL verification failure."""
    msg = str(exc).lower()
    if "certificate_verify_failed" in msg or "unable to get local issuer certificate" in msg:
        return (
            "SSL certificate verification failed. On Windows run: "
            "pip install pip-system-certs"
            " (then restart TruthGPT). "
            "If you use a corporate proxy/VPN, ensure its root CA is in the Windows trust store."
        )
    return None
