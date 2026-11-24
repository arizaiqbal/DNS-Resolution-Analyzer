
from dns_packet import build_dns_query
from dns_decoder import decode_dns_response
from dns_client import query_dns


ROOT_SERVER = "10.10.3.11"


def find_nameserver_ip(response):
    nameservers = []

    for record in response["authority"]:
        if record["type"] == 2:
            nameservers.append(record["data"])

    for nameserver in nameservers:
        for record in response["additional"]:
            if (
                record["type"] == 1
                and record["name"].lower() == nameserver.lower()
            ):
                return record["data"], nameserver

    return None, None


def iterative_lookup(domain, root_server=ROOT_SERVER, max_steps=15):
    current_domain = domain.rstrip(".")
    current_server = root_server
    visited = set()
    trace = []

    for step in range(max_steps):
        key = (current_domain.lower(), current_server)

        if key in visited:
            raise Exception("Repeated DNS query detected")

        visited.add(key)

        print(f"\nStep {step + 1}")
        print("Querying:", current_server)
        print("Domain:", current_domain)

        packet, transaction_id = build_dns_query(
            current_domain,
            record_type=1,
            recursion_desired=False
        )

        result = query_dns(current_server, packet)

        response = decode_dns_response(result["response"])

        if response["transaction_id"] != transaction_id:
            raise Exception("Transaction ID mismatch")

        if response["rcode"] != 0:
            raise Exception(
                f"DNS error: response code {response['rcode']}"
            )

        trace.append({
            "step": step + 1,
            "server": current_server,
            "domain": current_domain,
            "protocol": result["protocol"],
            "time_ms": result["elapsed_ms"]
        })

        # Check for an A record answer
        for record in response["answers"]:
            if record["type"] == 1:
                print("Final IP address:", record["data"])
                return {
                    "domain": current_domain,
                    "ip_address": record["data"],
                    "trace": trace
                }

        # Follow a CNAME if present
        cname_found = False

        for record in response["answers"]:
            if record["type"] == 5:
                print("CNAME found:", record["data"])
                current_domain = record["data"].rstrip(".")
                current_server = root_server
                cname_found = True
                break

        if cname_found:
            continue

        # Find the next nameserver using referral and glue
        next_server, nameserver = find_nameserver_ip(response)

        if next_server:
            print("Referral:", nameserver)
            print("Next server IP:", next_server)

            current_server = next_server
            continue

        raise Exception(
            "No answer or usable glue record found. "
            "Missing-glue handling will be added next."
        )

    raise Exception("Maximum DNS lookup steps exceeded")


if __name__ == "__main__":
    domain = "example.lab"

    try:
        result = iterative_lookup(domain)

        print("\n========== DNS TRACE ==========")

        for item in result["trace"]:
            print(item)

        print("\nResolved domain:", result["domain"])
        print("Resolved IP:", result["ip_address"])

    except Exception as error:
        print("\nResolution failed:", error)
