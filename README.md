# TLS Intercepting Proxy — Railway Deployment

A TLS-intercepting HTTP/HTTPS proxy built on the official [`mitmproxy/mitmproxy`](https://hub.docker.com/r/mitmproxy/mitmproxy) Docker image, deployable directly to [Railway](https://railway.app).

All intercepted requests, responses, and TLS handshakes are logged as structured JSON to stdout, which Railway captures automatically.

---

## Repository Structure

```
.
├── Dockerfile        # Wraps official mitmproxy image
├── entrypoint.sh     # Handles CA cert persistence via env var
├── addon.py          # mitmproxy addon: structured JSON logging
├── railway.toml      # Railway build + deploy config
└── README.md
```

---

## Deploy to Railway

### 1. Import this repo into Railway

1. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**
2. Select this repository
3. Railway will detect `railway.toml` and build the Dockerfile automatically

### 2. Expose port 8080

In Railway dashboard → your service → **Settings** → **Networking**:
- Add a **TCP Proxy** on port `8080`
- Note the assigned Railway domain + port (e.g. `your-service.railway.app:12345`)

---

## Persisting the CA Certificate

Without persistence, mitmproxy generates a new CA on every redeploy — breaking all clients.

### First deploy (CA generation)

Deploy once **without** `MITMPROXY_CA_B64`. The entrypoint will log:
```
[entrypoint] No MITMPROXY_CA_B64 set — a new CA will be generated.
```

### Extract the CA cert

```bash
# Via Railway CLI
railway run --service <your-service-name> \
  cat /home/mitmproxy/.mitmproxy/mitmproxy-ca.pem > mitmproxy-ca.pem
```

### Persist it as an env var

```bash
# Base64-encode the cert (no line wrapping)
base64 -w0 mitmproxy-ca.pem
# On macOS: base64 -i mitmproxy-ca.pem | tr -d '\n'
```

Paste the output into Railway → **Variables** → `MITMPROXY_CA_B64`.

Redeploy — the CA is now stable across all future deploys. The entrypoint will log:
```
[entrypoint] CA cert restored from MITMPROXY_CA_B64 env var.
```

---

## Client Configuration

Use the `mitmproxy-ca.pem` file extracted above on each client.

### curl

```bash
export HTTPS_PROXY=http://<railway-host>:<port>
curl --cacert mitmproxy-ca.pem https://example.com
```

### Python (requests)

```python
import requests

proxies = {"http": "http://<host>:<port>", "https": "http://<host>:<port>"}

resp = requests.get(
    "https://example.com",
    proxies=proxies,
    verify="/path/to/mitmproxy-ca.pem",
)
print(resp.status_code)
```

### Node.js

```bash
npm install https-proxy-agent
```

```javascript
const https = require("https");
const fs = require("fs");
const { HttpsProxyAgent } = require("https-proxy-agent");

const agent = new HttpsProxyAgent("http://<host>:<port>", {
    ca: fs.readFileSync("/path/to/mitmproxy-ca.pem"),
});

https.get("https://example.com", { agent }, (res) => {
    console.log("Status:", res.statusCode);
});
```

### Linux system-wide

```bash
sudo cp mitmproxy-ca.pem /usr/local/share/ca-certificates/mitmproxy.crt
sudo update-ca-certificates

export HTTP_PROXY=http://<host>:<port>
export HTTPS_PROXY=http://<host>:<port>
```

### macOS system-wide

```bash
sudo security add-trusted-cert -d -r trustRoot \
  -k /Library/Keychains/System.keychain mitmproxy-ca.pem

networksetup -setwebproxy Wi-Fi <host> <port>
networksetup -setsecurewebproxy Wi-Fi <host> <port>
```

### Windows (PowerShell)

```powershell
Import-Certificate -FilePath "mitmproxy-ca.pem" `
  -CertStoreLocation Cert:\LocalMachine\Root

$p = "<host>:<port>"
[System.Environment]::SetEnvironmentVariable("HTTP_PROXY",  "http://" + $p, "Machine")
[System.Environment]::SetEnvironmentVariable("HTTPS_PROXY", "http://" + $p, "Machine")
```

---

## Viewing Logs

Railway captures all stdout. Logs are structured JSON, one line per event.

```bash
# Stream logs via Railway CLI
railway logs --tail
```

Example output:
```json
{"event": "tls_handshake", "ts": 1710000000.1, "client": "1.2.3.4:54321"}
{"event": "request",  "ts": 1710000000.2, "client_ip": "1.2.3.4", "method": "GET", "url": "https://example.com/", "status_code": null, ...}
{"event": "response", "ts": 1710000000.5, "client_ip": "1.2.3.4", "url": "https://example.com/", "status_code": 200, ...}
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `MITMPROXY_CA_B64` | Recommended | Base64-encoded `mitmproxy-ca.pem`. Keeps CA stable across redeploys. |

---

## Notes

- Apps using **certificate pinning** cannot be intercepted without patching the app first.
- The proxy validates upstream TLS by default (`ssl_insecure=false`). To disable for testing: add `--set ssl_insecure=true` to the `mitmdump` command in `entrypoint.sh`.
- To extend logging behaviour (filter hosts, forward to Datadog/Loki, etc.), edit `addon.py`.
