#!/bin/bash
# update ollama, rewrite service from initial settings and restart
# use with sudo

OLLAMA_SERVICE=$(cat /etc/systemd/system/ollama.service)

curl -fsSL https://ollama.com/install.sh | sh

echo "$OLLAMA_SERVICE" > /etc/systemd/system/ollama.service

systemctl daemon-reload
systemctl restart ollama