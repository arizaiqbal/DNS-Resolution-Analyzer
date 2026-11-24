# DNS Resolution Analyzer — CS-3001

Existing iterative resolver files are retained for Fatima's work. The transport and network implementation is for the controlled lab. Ubuntu 22.04/24.04 required for namespaces; Python editing and static checks can be done on macOS.

## Ubuntu setup

```bash
sudo apt update
sudo apt install iproute2 bind9 bind9-utils unbound dnsutils tcpdump tshark traceroute openssl python3-venv
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
sudo bash network/setup_topology.sh
sudo bash network/start_services.sh
```

Run from the repository root, preferably in a path without spaces. Do not run on a production machine. Services use isolated namespaces but share the host filesystem; the lab CA is generated locally and not installed system-wide. BIND configurations are templates expanded by the launcher. If startup fails, check runtime/*.log and clean up before retrying.

## Verify routing and DNS

```bash
sudo ip -n r1 route
sudo ip -n r2 route
sudo ip netns exec client traceroute -n 10.10.3.13
sudo ip netns exec client dig @10.10.3.11 example.lab +norecurse
sudo ip netns exec client dig @10.10.3.12 example.lab +norecurse
sudo ip netns exec client dig @10.10.3.13 www.example.lab +norecurse
sudo ip netns exec client dig @10.10.2.53 example.lab
sudo ip netns exec client .venv/bin/python comparison/transport_comparison.py www.example.lab
sudo ip netns exec client .venv/bin/python resolver/iterative_resolver.py
```

## Experiments

```bash
sudo .venv/bin/python experiments/run_experiments.py --smoke --capture --output experiments/smoke.csv
sudo .venv/bin/python experiments/run_experiments.py --runs 5 --capture
.venv/bin/python analysis/analyze_results.py experiments/results.csv
```

The full factorial run covers 20/100/200 ms added RTT, 0/2/5% loss per direction, cold/warm cache, five transport/mode combinations and five repetitions, 200 names per combination (90,000 measured lookups). Start with smoke tests. Use --limit to reduce the test set during debugging. Capture mode saves individual pcapng files and sums captured Ethernet frame lengths; this is not physical-layer byte accounting. The capture begins after cache priming and persistent connection setup, and ends after the measured request (new connection close is included where observable). Persistent setup is intentionally excluded from those captures. DNS payload bytes do not include framing, headers or TLS. DoH is HTTP/1.1 POST with TLS, not HTTP/2; compare only the implemented configuration. HTTP timing uses httpcore trace events. Cache flushing clears RRsets/messages and infrastructure cache, but does not restart the resolver or reset every internal state. Warm cache priming uses Do53. Public names are not available in the isolated hierarchy. The 200 lab names are synthetic popular/long-tail proxies, CNAMEs, and NXDOMAIN cases, 50 each; do not describe them as real popular websites. Packet loss is configured on each transit direction, not per round trip. No experimental results are supplied or fabricated.

For individual captures, use Wireshark filters `dns`, `tcp.port == 853`, and `tcp.port == 443`. Capture iterative traffic separately, e.g. `sudo ip netns exec client tcpdump -i eth0 -w captures/iterative/trace.pcap port 53`, run the resolver in another terminal, stop capture, then use `editcap -F pcapng`.

## Cleanup

```bash
sudo bash network/cleanup.sh
```

## AI disclosure

AI assistance was used to generate the network, measurement and experiment code and README. Review, adapt and verify all code and disclose actual usage under course policy. Existing resolver still needs missing-glue handling, trace reporting, correctness validation and integration testing by its owner.
