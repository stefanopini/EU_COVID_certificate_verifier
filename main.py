import json
import sys
import zlib

import base45
import cbor2
from cose.messages import CoseMessage


def main():
    # credits to Hacker Noon
    # https://hackernoon.com/how-to-decode-your-own-eu-vaccination-green-pass-with-a-few-lines-of-python-9v2c37s1

    # payload = sys.argv[1][4:]
    payload = input()[4:]
    print("decoding payload: " + payload)

    # decode Base45 (remove HC1: prefix)
    decoded = base45.b45decode(payload)

    # decompress using zlib
    decompressed = zlib.decompress(decoded)
    # decode COSE message (no signature verification done)
    cose = CoseMessage.decode(decompressed)
    # decode the CBOR encoded payload and print as json
    print(json.dumps(cbor2.loads(cose.payload), indent=2))


if __name__ == '__main__':
    main()
