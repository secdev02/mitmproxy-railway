#!/bin/sh
set -e

CA_DIR="/home/mitmproxy/.mitmproxy"
mkdir -p "$CA_DIR"

# If a CA cert was injected via env (base64-encoded), restore it before starting.
# This keeps the CA stable across Railway redeploys so clients don't need to
# re-import the cert on every deployment.
if [ -n "$MITMPROXY_CA_B64" ]; then
    echo "$MITMPROXY_CA_B64" | base64 -d > "$CA_DIR/mitmproxy-ca.pem"
    echo "[entrypoint] CA cert restored from MITMPROXY_CA_B64 env var."
else
    echo "[entrypoint] No MITMPROXY_CA_B64 set — a new CA will be generated."
    echo "[entrypoint] After first run, export the CA and set MITMPROXY_CA_B64 to persist it."
fi

exec mitmdump \
    --listen-host 0.0.0.0 \
    --listen-port 8080 \
    --set confdir="$CA_DIR" \
    -s /home/mitmproxy/addon.py
