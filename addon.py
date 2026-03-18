"""
addon.py — Structured JSON logging addon for mitmproxy.

Logs every request, response, and TLS handshake as a JSON line to stdout.
Railway captures stdout automatically, so no extra log shipping is needed.
"""

import json
import time
import logging
import mitmproxy.http
from mitmproxy import ctx

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("tlsproxy")


def _serialize_headers(headers) -> dict:
    """Convert mitmproxy headers to a plain dict."""
    result = {}
    for name, value in headers.fields:
        key = name.decode("utf-8", errors="replace")
        val = value.decode("utf-8", errors="replace")
        # Accumulate duplicate header names into a list
        if key in result:
            existing = result[key]
            if isinstance(existing, list):
                existing.append(val)
            else:
                result[key] = [existing, val]
        else:
            result[key] = val
    return result


class TLSLogger:

    def request(self, flow: mitmproxy.http.HTTPFlow) -> None:
        entry = {
            "event": "request",
            "ts": time.time(),
            "client_ip": flow.client_conn.peername[0] if flow.client_conn.peername else None,
            "method": flow.request.method,
            "url": flow.request.pretty_url,
            "host": flow.request.pretty_host,
            "path": flow.request.path,
            "http_version": flow.request.http_version,
            "headers": _serialize_headers(flow.request.headers),
            "content_length": len(flow.request.content or b""),
        }
        log.info(json.dumps(entry))

    def response(self, flow: mitmproxy.http.HTTPFlow) -> None:
        entry = {
            "event": "response",
            "ts": time.time(),
            "client_ip": flow.client_conn.peername[0] if flow.client_conn.peername else None,
            "url": flow.request.pretty_url,
            "status_code": flow.response.status_code,
            "reason": flow.response.reason,
            "headers": _serialize_headers(flow.response.headers),
            "content_length": len(flow.response.content or b""),
        }
        log.info(json.dumps(entry))

    def tls_start_client(self, tls_start) -> None:
        entry = {
            "event": "tls_handshake",
            "ts": time.time(),
            "client": str(tls_start.context.client.peername),
        }
        log.info(json.dumps(entry))

    def tls_failed_client(self, tls_start) -> None:
        entry = {
            "event": "tls_failed",
            "ts": time.time(),
            "client": str(tls_start.context.client.peername),
        }
        log.info(json.dumps(entry))


addons = [TLSLogger()]
