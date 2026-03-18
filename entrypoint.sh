#!/bin/sh
set -e

CA_DIR="/home/mitmproxy/.mitmproxy"
mkdir -p "$CA_DIR"

if [ -n "$MITMPROXY_CA_B64" ]; then
    echo "$MITMPROXY_CA_B64" | base64 -d > "$CA_DIR/mitmproxy-ca.pem"
    echo "[entrypoint] CA cert restored from MITMPROXY_CA_B64 env var."
else
    echo "[entrypoint] No MITMPROXY_CA_B64 set — a new CA will be generated."
    echo "[entrypoint] After first run, export the CA and set MITMPROXY_CA_B64 to persist it."
fi

PROXY_PORT="${PORT:-8080}"

echo "[entrypoint] Starting mitmdump on 0.0.0.0:${PROXY_PORT}"

exec mitmdump \
    --listen-host 0.0.0.0 \
    --listen-port "$PROXY_PORT" \
    --set confdir="$CA_DIR" \
    -s /home/mitmproxy/addon.py
    
