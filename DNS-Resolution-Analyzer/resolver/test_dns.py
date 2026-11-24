
import socket

from dns_packet import build_dns_query
from dns_decoder import decode_dns_response


server = "1.1.1.1"
domain = "example.com"

packet, transaction_id = build_dns_query(domain)

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)

    sock.sendto(packet, (server, 53))

    response, address = sock.recvfrom(4096)

    result = decode_dns_response(response)

    print("DNS server:", address)
    print("Transaction ID:", result["transaction_id"])
    print("Response code:", result["rcode"])
    print("Questions:", result["questions"])
    print("Answers:", result["answers"])
    print("Authority:", result["authority"])
    print("Additional:", result["additional"])

    if result["transaction_id"] != transaction_id:
        print("WARNING: Transaction ID does not match")

except socket.timeout:
    print("Request timed out. Check your internet connection.")

except Exception as error:
    print("Error:", error)

finally:
    if "sock" in locals():
        sock.close()
