
import struct
import socket


def decode_name(packet, offset):
    labels = []
    original_offset = offset
    jumped = False
    visited = set()

    while True:
        if offset >= len(packet):
            raise ValueError("Invalid DNS packet")

        length = packet[offset]

        if length == 0:
            if not jumped:
                original_offset = offset + 1
            break

        if (length & 0xC0) == 0xC0:
            if offset + 1 >= len(packet):
                raise ValueError("Invalid compression pointer")

            pointer = ((length & 0x3F) << 8) | packet[offset + 1]

            if pointer >= len(packet) or pointer in visited:
                raise ValueError("Invalid compression pointer")

            visited.add(pointer)

            if not jumped:
                original_offset = offset + 2
                jumped = True

            offset = pointer
            continue

        if length & 0xC0:
            raise ValueError("Invalid DNS label")

        offset += 1

        if offset + length > len(packet):
            raise ValueError("Invalid DNS label length")

        label = packet[offset:offset + length].decode("ascii")
        labels.append(label)

        offset += length

        if not jumped:
            original_offset = offset

    return ".".join(labels), original_offset


def decode_question(packet, offset):
    name, offset = decode_name(packet, offset)

    if offset + 4 > len(packet):
        raise ValueError("Incomplete DNS question")

    qtype, qclass = struct.unpack("!HH", packet[offset:offset + 4])

    return {
        "name": name,
        "type": qtype,
        "class": qclass
    }, offset + 4


def decode_record(packet, offset):
    name, offset = decode_name(packet, offset)

    if offset + 10 > len(packet):
        raise ValueError("Incomplete DNS record")

    rtype, rclass, ttl, rdlength = struct.unpack(
        "!HHIH", packet[offset:offset + 10]
    )

    offset += 10

    if offset + rdlength > len(packet):
        raise ValueError("Incomplete record data")

    start = offset
    end = offset + rdlength
    data = packet[start:end]

    if rtype == 1 and rdlength == 4:
        value = socket.inet_ntoa(data)

    elif rtype == 28 and rdlength == 16:
        value = socket.inet_ntop(socket.AF_INET6, data)

    elif rtype in (2, 5, 12):
        value, _ = decode_name(packet, start)

    elif rtype == 15 and rdlength >= 3:
        preference = struct.unpack("!H", data[:2])[0]
        exchange, _ = decode_name(packet, start + 2)
        value = {
            "preference": preference,
            "exchange": exchange
        }

    elif rtype == 16:
        parts = []
        position = 0

        while position < rdlength:
            size = data[position]
            position += 1
            parts.append(data[position:position + size].decode(
                "utf-8", errors="replace"
            ))
            position += size

        value = parts

    elif rtype == 41:
        value = {
            "udp_payload_size": rclass,
            "extended_rcode": (ttl >> 24) & 0xFF,
            "version": (ttl >> 16) & 0xFF,
            "flags": ttl & 0xFFFF,
            "options": data.hex()
        }

    else:
        value = data.hex()

    record = {
        "name": name,
        "type": rtype,
        "class": rclass,
        "ttl": ttl,
        "data": value
    }

    return record, end


def decode_dns_response(packet):
    if len(packet) < 12:
        raise ValueError("DNS packet is too short")

    transaction_id, flags, qdcount, ancount, nscount, arcount = (
        struct.unpack("!HHHHHH", packet[:12])
    )

    offset = 12

    questions = []
    answers = []
    authority = []
    additional = []

    for _ in range(qdcount):
        question, offset = decode_question(packet, offset)
        questions.append(question)

    for _ in range(ancount):
        record, offset = decode_record(packet, offset)
        answers.append(record)

    for _ in range(nscount):
        record, offset = decode_record(packet, offset)
        authority.append(record)

    for _ in range(arcount):
        record, offset = decode_record(packet, offset)
        additional.append(record)

    return {
        "transaction_id": transaction_id,
        "is_response": bool(flags & 0x8000),
        "authoritative": bool(flags & 0x0400),
        "truncated": bool(flags & 0x0200),
        "recursion_desired": bool(flags & 0x0100),
        "recursion_available": bool(flags & 0x0080),
        "rcode": flags & 0x000F,
        "questions": questions,
        "answers": answers,
        "authority": authority,
        "additional": additional
    }

