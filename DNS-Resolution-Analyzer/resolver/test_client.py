
from dns_packet import build_dns_query
from dns_decoder import decode_dns_response
from dns_client import query_dns


server = "1.1.1.1"
domain = "example.com"

packet, transaction_id = build_dns_query(domain)

try:
    result = query_dns(server, packet)

    response = result["response"]
    decoded = decode_dns_response(response)

    print("\nDNS CLIENT TEST")
    print("----------------------")
    print("Server:", server)
    print("Domain:", domain)
    print("Transaction ID:", decoded["transaction_id"])
    print("Protocol:", result["protocol"])
    print("Response time:", round(result["elapsed_ms"], 2), "ms")
    print("TCP fallback:", result["fallback"])
    print("Response code:", decoded["rcode"])
    print("Answers:", decoded["answers"])

    if decoded["transaction_id"] == transaction_id:
        print("\nTEST PASSED")
    else:
        print("\nTRANSACTION ID MISMATCH")

except Exception as error:
    print("DNS client error:", error)
