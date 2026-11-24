#!/usr/bin/env bash
set -euo pipefail
# Arguments: added RTT in ms, per-direction packet loss percent, optional bandwidth (e.g. 10mbit)
rtt=${1:-0}; loss=${2:-0}; rate=${3:-}
delay=$(awk -v n="$rtt" 'BEGIN {print n/2}')
for pair in 'r1 transit0' 'r2 transit1'; do
  read -r ns dev <<< "$pair"
  ip netns exec "$ns" tc qdisc del dev "$dev" root 2>/dev/null || true
  ip netns exec "$ns" tc qdisc add dev "$dev" root handle 1: netem delay "${delay}ms" loss "${loss}%"
  if [[ -n "$rate" ]]; then
    ip netns exec "$ns" tc qdisc add dev "$dev" parent 1:1 handle 2: tbf rate "$rate" burst 32kb latency 400ms
  fi
done
