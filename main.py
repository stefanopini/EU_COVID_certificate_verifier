import argparse
import json
import warnings
import zlib

import base45
import cbor2
import cv2
from cose.messages import CoseMessage
from pyzbar import pyzbar


def decode_cert(payload):
    # credits to Hacker Noon
    # https://hackernoon.com/how-to-decode-your-own-eu-vaccination-green-pass-with-a-few-lines-of-python-9v2c37s1

    # decode Base45 (remove HC1: prefix)
    decoded = base45.b45decode(payload)

    # decompress using zlib
    decompressed = zlib.decompress(decoded)

    # decode COSE message (no signature verification done)
    cose = CoseMessage.decode(decompressed)

    # decode the CBOR encoded payload and print as json
    decoded_payload = cbor2.loads(cose.payload)

    return cose, decoded_payload


def read_qr_from_image(path):
    img = cv2.imread(path, cv2.IMREAD_ANYCOLOR)
    if img is None:
        raise RuntimeError(f'Unable to open image from path: {path}')

    # detector = cv2.QRCodeDetector()
    # data, bbox, straight_qrcode = detector.detectAndDecode(img)
    decoded_qrs = pyzbar.decode(img)
    if len(decoded_qrs) == 0:
        raise RuntimeError(f'No qr code detected in the loaded image.')

    if len(decoded_qrs) > 1:
        warnings.warn('Multiple QRs detected, loading the first one only.')

    return decoded_qrs[0].data


def read_qr_from_camera(camera_id):
    video = cv2.VideoCapture(camera_id)
    if not video.isOpened():
        raise RuntimeError(f'Unable to open stream from camera with id: {camera_id}')

    # detector = cv2.QRCodeDetector()

    while True:
        ret, frame = video.read()
        if not ret:
            raise RuntimeError(f'Video stream closed without detecting any qr code.')

        cv2.imshow('wc', frame)
        cv2.waitKey(1)
        # data, bbox, straight_qrcode = detector.detectAndDecode(frame)
        decoded_qrs = pyzbar.decode(frame)
        if len(decoded_qrs) > 0:
            break

    if len(decoded_qrs) > 1:
        warnings.warn('Multiple QRs detected, loading the first one only.')

    data = decoded_qrs[0].data.decode('utf-8')
    return data


def main(arguments):
    mode = arguments.mode

    if mode == 'input':
        payload = input()
    elif mode == 'arg':
        payload = arguments.payload
    elif mode == 'image':
        payload = read_qr_from_image(arguments.image_path)
    elif mode == 'camera':
        payload = read_qr_from_camera(arguments.camera_id)
    else:
        raise ValueError

    print("decoding payload: " + payload)

    # verify valid QR code header for EU COVID certificate
    if payload[:4] != 'HC1:':
        raise ValueError('Invalid QR code header')
    # remove first 4 characters
    payload = payload[4:]

    cose_msg, decoded_payload = decode_cert(payload)

    print(json.dumps(decoded_payload, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(default='input', type=str, dest='mode',
                        help="The input modality. Allowed options are: `input`, `arg`, `image`, `camera`.")
    parser.add_argument('--payload', default=None, type=str, required=False,
                        help="The qr-code content. Used only when mode == `arg`.")
    parser.add_argument('--image_path', default=None, type=str, required=False,
                        help="The qr-code image path. Used only when mode == 'image'.")
    parser.add_argument('--camera_id', default=0, type=int, required=False,
                        help="The camera id. Used only when mode == 'camera'.")
    args = parser.parse_args()

    if args.mode not in ('input', 'arg', 'image', 'camera'):
        raise ValueError('Invalid input type.')
    if args.mode == 'arg' and args.payload is None:
        raise ValueError('Missing `payload` argument.')
    if args.mode == 'arg' and args.image_path is None:
        raise ValueError('Missing `image_path` argument.')
    if args.mode == 'arg' and args.camera_id is None:
        raise ValueError('Missing `camera_id` argument.')

    main(args)
