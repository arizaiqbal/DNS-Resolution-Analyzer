#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
P=$PWD
mkdir -p runtime
[[ -f unbound/certs/server.key ]] || bash network/generate_certificates.sh
for pair in 'root rootdns' 'tld tlddns' 'authoritative authdns'; do
  read -r role ns <<< "$pair"
  sed "s|@PROJECT@|$P|g" "dns_servers/$role/named.conf" > "runtime/$role.conf"
  named-checkconf -z "runtime/$role.conf"
  ip netns exec "$ns" named -g -c "$P/runtime/$role.conf" > "runtime/$role.log" 2>&1 &
done
sed "s|@PROJECT@|$P|g" unbound/unbound.conf > runtime/unbound.conf
unbound-checkconf runtime/unbound.conf
ip netns exec unbound unbound -d -c "$P/runtime/unbound.conf" > runtime/unbound.log 2>&1 &
PYTHON="$P/.venv/bin/python"
ip netns exec unbound "$PYTHON" "$P/unbound/doh_server.py" > runtime/doh.log 2>&1 &
sleep 2
ip netns exec client dig @10.10.2.53 example.lab +time=3 +tries=1
