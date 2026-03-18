FROM mitmproxy/mitmproxy:latest

USER root

COPY entrypoint.sh /home/mitmproxy/entrypoint.sh
COPY addon.py /home/mitmproxy/addon.py

RUN chmod +x /home/mitmproxy/entrypoint.sh

USER mitmproxy

ENTRYPOINT ["/home/mitmproxy/entrypoint.sh"]
