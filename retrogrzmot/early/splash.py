"""Early one-shot SSD1306 splash. Standard library only; no /userdata access."""
import fcntl
import os
import sys
import time

BUS = '/dev/i2c-1'
LOCK = '/tmp/retrogrzmot-oled.lock'


def splash(frame_path, wait_seconds=8):
    with open(frame_path, 'rb') as source:
        frame = source.read()
    if len(frame) != 1024:
        raise ValueError('Expected exactly 1024 bytes for 128x64 OLED')
    deadline = time.monotonic() + wait_seconds
    while not os.path.exists(BUS):
        if time.monotonic() >= deadline:
            print('Early splash: I2C unavailable; normal startup continues', flush=True)
            return False
        time.sleep(0.1)
    with open(LOCK, 'a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('Early splash: display already owned by service', flush=True)
            return False
        fd = os.open(BUS, os.O_RDWR)
        try:
            fcntl.ioctl(fd, 0x0703, 0x3C)
            def send(control, payload):
                packet = bytes([control]) + bytes(payload)
                if os.write(fd, packet) != len(packet):
                    raise OSError('Incomplete I2C write')
            send(0, [0xAE, 0xD5, 0x80, 0xA8, 0x3F, 0xD3, 0,
                     0x40, 0x8D, 0x14, 0x20, 0, 0xA1, 0xC8,
                     0xDA, 0x12, 0x81, 0x7F, 0xD9, 0xF1,
                     0xDB, 0x40, 0xA4, 0xA6, 0x2E])
            send(0, [0x21, 0, 127, 0x22, 0, 7])
            for offset in range(0, 1024, 16):
                send(0x40, frame[offset:offset + 16])
            send(0, [0xAF])
            print(f'Early splash displayed at {time.monotonic():.2f}s monotonic', flush=True)
            return True
        finally:
            # Keep the image powered; release the bus and lock for the service.
            os.close(fd)


if __name__ == '__main__':
    frame_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'splash.bin')
    try:
        splash(frame_path)
    except Exception as error:
        print(f'Early splash skipped: {error}', file=sys.stderr, flush=True)
        raise SystemExit(1)
