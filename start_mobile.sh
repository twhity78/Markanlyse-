#!/usr/bin/env bash
# Startet die NK-Abrechnung im lokalen WLAN, erreichbar vom Handy.
#
# Voraussetzung: Handy und dieser Rechner sind im selben WLAN.
# Danach die unten angezeigte Adresse im Handy-Browser öffnen.
set -e

cd "$(dirname "$0")"

# Lokale IP-Adresse ermitteln (Linux/macOS).
IP=$(hostname -I 2>/dev/null | awk '{print $1}')
if [ -z "$IP" ]; then
  IP=$(ipconfig getifaddr en0 2>/dev/null || echo "<DEINE-IP>")
fi

echo "======================================================"
echo " NK-Abrechnung startet ..."
echo " Auf dem Handy im selben WLAN im Browser öffnen:"
echo ""
echo "     http://${IP}:8501"
echo ""
echo " Beenden mit Strg+C"
echo "======================================================"

exec streamlit run streamlit_app.py \
  --server.address 0.0.0.0 \
  --server.port 8501
