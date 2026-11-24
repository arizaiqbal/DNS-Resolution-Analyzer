
import socket
import struct
import time


def receive_exact(sock, size):
    data = b""

    while len(data) < size:
        part = sock.recv(size - len(data))

        if not part:
            raise ConnectionError("Connection closed unexpectedly")

        data += part

    return data


def send_udp_query(server, packet, timeout=5):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)

    start = time.perf_counter()

    try:
        sock.sendto(packet, (server, 53))
        response, address = sock.recvfrom(4096)

        elapsed = (time.perf_counter() - start) * 1000

        return response, elapsed, address

    finally:
        sock.close()


def send_tcp_query(server, packet, timeout=5):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)

    start = time.perf_counter()

    try:
        sock.connect((server, 53))

        message = struct.pack("!H", len(packet)) + packet
        sock.sendall(message)

        response_length = struct.unpack(
            "!H", receive_exact(sock, 2)
        )[0]

        response = receive_exact(sock, response_length)

        elapsed = (time.perf_counter() - start) * 1000

        return response, elapsed

    finally:
        sock.close()


def query_dns(server, packet):
    response, elapsed, address = send_udp_query(server, packet)

    flags = struct.unpack("!H", response[2:4])[0]
    truncated = bool(flags & 0x0200)

    if truncated:
        print("UDP response truncated. Switching to TCP.")

        response, tcp_elapsed = send_tcp_query(server, packet)

        return {
            "response": response,
            "protocol": "TCP",
            "elapsed_ms": tcp_elapsed,
            "fallback": True
        }

    return {
        "response": response,
        "protocol": "UDP",
        "elapsed_ms": elapsed,
        "fallback": False
    }
