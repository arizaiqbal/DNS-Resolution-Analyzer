
import struct
import random


def encode_domain_name(domain):
    encoded = b""

    for label in domain.rstrip(".").split("."):
        encoded += bytes([len(label)])
        encoded += label.encode("ascii")

    encoded += b"\x00"

    return encoded


def build_dns_query(domain, record_type=1, use_edns=True, recursion_desired=True):
    transaction_id = random.randint(0, 65535)

    flags = 0x0100 if recursion_desired else 0

    questions = 1
    answers = 0
    authority = 0
    additional = 1 if use_edns else 0

    header = struct.pack(
        "!HHHHHH",
        transaction_id,
        flags,
        questions,
        answers,
        authority,
        additional
    )

    question = encode_domain_name(domain)

    question += struct.pack("!HH", record_type, 1)

    if use_edns:
        edns_record = struct.pack(
            "!BHHIH",
            0,
            41,
            1232,
            0,
            0
        )

        return header + question + edns_record, transaction_id

    return header + question, transaction_id


if __name__ == "__main__":
    packet, transaction_id = build_dns_query(
    "example.com",
    recursion_desired=False
)

    print("Transaction ID:", transaction_id)
    print("DNS Packet:", packet.hex())
    print("Packet Length:", len(packet))
