#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p unbound/certs
umask 077
openssl req -x509 -newkey rsa:2048 -nodes -days 365 -subj '/CN=DNS Lab CA' -keyout unbound/certs/ca.key -out unbound/certs/ca.crt
openssl req -new -newkey rsa:2048 -nodes -subj '/CN=10.10.2.53' -keyout unbound/certs/server.key -out unbound/certs/server.csr
printf 'subjectAltName=IP:10.10.2.53,DNS:resolver.example.lab\nextendedKeyUsage=serverAuth\n' > unbound/certs/server.ext
openssl x509 -req -in unbound/certs/server.csr -CA unbound/certs/ca.crt -CAkey unbound/certs/ca.key -CAcreateserial -days 365 -extfile unbound/certs/server.ext -out unbound/certs/server.crt
