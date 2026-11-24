#!/usr/bin/env bash
set -euo pipefail
addr(){ ip -n "$1" addr replace "$3" dev "$2"; }
addr client eth0 10.10.1.10/24
addr r1 lan0 10.10.1.1/24
addr r1 transit0 10.10.0.1/30
addr r2 transit1 10.10.0.2/30
addr r2 res0 10.10.2.1/24
addr unbound eth0 10.10.2.53/24
addr r2 br-auth 10.10.3.1/24
addr rootdns eth0 10.10.3.11/24
addr tlddns eth0 10.10.3.12/24
addr authdns eth0 10.10.3.13/24
ip -n client route replace default via 10.10.1.1
ip -n r1 route replace 10.10.2.0/24 via 10.10.0.2
ip -n r1 route replace 10.10.3.0/24 via 10.10.0.2
ip -n r2 route replace 10.10.1.0/24 via 10.10.0.1
ip -n unbound route replace default via 10.10.2.1
for ns in rootdns tlddns authdns; do ip -n "$ns" route replace default via 10.10.3.1; done
