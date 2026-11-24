#!/usr/bin/env bash
set -euo pipefail
for ns in client r1 r2 unbound rootdns tlddns authdns; do
  if ip netns list | grep -q "^$ns\( \|$\)"; then
    ip netns pids "$ns" | xargs -r kill || true
    sleep .2
    ip netns pids "$ns" | xargs -r kill -KILL || true
    ip netns del "$ns"
  fi
done
