""" Saves a capture of the official client's client area, for test fixtures and anchor templates.

    python helpers/CaptureClient.py tests/testdata/client_1920x1080.png [--title Knight]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.Dpi import make_dpi_aware  # noqa: E402

make_dpi_aware()

import cv2  # noqa: E402

from core.ClientWindow import find_client_windows  # noqa: E402
from core.ScreenCapture import ScreenCapture  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('output', help='PNG file to write')
    parser.add_argument('--title', help='part of the client window title, when several are open')
    args = parser.parse_args()

    clients = find_client_windows()
    if args.title:
        clients = [c for c in clients if args.title in c.title]
    if not clients:
        sys.exit('No official Tibia client window found')
    if len(clients) > 1:
        sys.exit('Several clients found; pass --title: ' + ', '.join(c.title for c in clients))

    client = clients[0]
    if client.client_rect is None:
        sys.exit(f"'{client.title}' is minimized")
    image = ScreenCapture().capture_client(client)
    if not cv2.imwrite(args.output, image):
        sys.exit(f"Could not write {args.output}")
    print(f"Saved {client.title} ({image.shape[1]}x{image.shape[0]}) to {args.output}")


if __name__ == '__main__':
    main()
