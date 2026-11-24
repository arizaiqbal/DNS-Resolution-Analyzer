#!/usr/bin/env bash
set -euo pipefail
# Run on Ubuntu as root; cleanup first if recreating.
for ns in client r1 r2 unbound rootdns tlddns authdns; do
  ip netns add "$ns"
  ip -n "$ns" link set lo up
done
link() {
  ip link add "$2" type veth peer name "$4"
  ip link set "$2" netns "$1"
  ip link set "$4" netns "$3"
  ip -n "$1" link set "$2" up
  ip -n "$3" link set "$4" up
}
link client eth0 r1 lan0
link r1 transit0 r2 transit1
link r2 res0 unbound eth0
ip -n r2 link add br-auth type bridge
ip -n r2 link set br-auth up
for ns in rootdns tlddns authdns; do
  link "$ns" eth0 r2 "p-$ns"
  ip -n r2 link set "p-$ns" master br-auth
done
for ns in r1 r2; do ip netns exec "$ns" sysctl -qw net.ipv4.ip_forward=1; done
bash "$(dirname "$0")/configure_routes.sh"
