"""RETROGRZMOT OLED v0.5: handover from optional early boot splash.

Hardware: SSD1306 128x64 on /dev/i2c-1, address 0x3c.
Requires Python 3 and Pillow. Event forwarding uses only the standard library.
"""
import json
import os
from pathlib import Path
import signal
import socket
import sys
import time

BASE = Path('/tmp/retrogrzmot-oled')
SOCKET = str(BASE) + '.sock'
PID = Path(str(BASE) + '.pid')
LAST = Path(str(BASE) + '.json')
APP = '/userdata/system/retrogrzmot/oled.py'
SCROLL_SPEED = 18  # pixels per second
SCROLL_PAUSE = 1.5  # seconds at each end
LOADING_SECONDS = 3.0  # agreed animation duration, NOT measured loading progress
POWER = Path(str(BASE) + '.power.json')
MIN_POWER_SECONDS = 1.5

# English documentation, with the original Polish OLED labels as the default.
TEXT = {
    'pl': {'game': 'Gra', 'choose': 'Wybierz konsole', 'powered': 'napędzane przez',
           'loading': 'WCZYTYWANIE', 'favorites': 'Ulubione',
           'all': 'Wszystkie gry', 'recent': 'Ostatnio grane',
           'shutdown': [('WYŁĄCZANIE', 12), ('RETROGRZMOTA', 36)],
           'reboot': [('PONOWNE', 5), ('URUCHAMIANIE', 25), ('RETROGRZMOTA', 45)]},
    'en': {'game': 'Game', 'choose': 'Choose a system', 'powered': 'powered by',
           'loading': 'LOADING', 'favorites': 'Favorites',
           'all': 'All games', 'recent': 'Recently played',
           'shutdown': [('SHUTTING DOWN', 12), ('RETROGRZMOT', 36)],
           'reboot': [('RESTARTING', 12), ('RETROGRZMOT', 36)]},
}
try:
    LANGUAGE = Path(__file__).with_name('language.txt').read_text(encoding='utf-8').strip()
except FileNotFoundError:
    LANGUAGE = 'pl'
if LANGUAGE not in TEXT:
    raise ValueError('language.txt must contain pl or en')
UI = TEXT[LANGUAGE]


def power_action(event, args=()):
    if event in ('shutdown', 'reboot'):
        return event
    if event == 'quit' and args and args[0] in ('shutdown', 'reboot'):
        return args[0]
    return None


def scroll_offset(elapsed, overflow):
    """Move to the end and back, pausing at both ends; never cut the tail."""
    if overflow <= 0:
        return 0
    travel = overflow / SCROLL_SPEED
    phase = max(0, elapsed) % (2 * (SCROLL_PAUSE + travel))
    if phase < SCROLL_PAUSE:
        return 0
    if phase < SCROLL_PAUSE + travel:
        return min(overflow, int((phase - SCROLL_PAUSE) * SCROLL_SPEED))
    if phase < 2 * SCROLL_PAUSE + travel:
        return overflow
    return max(0, overflow - int((phase - 2 * SCROLL_PAUSE - travel) * SCROLL_SPEED))


def process_id():
    try:
        pid = int(PID.read_text())
        args = Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
        if APP.encode() in args and b'run' in args:
            return pid
    except (OSError, ValueError):
        pass
    return None


def forward(event, args):
    payload = {'event': event}
    action = power_action(event, args)
    if action:
        payload = {'event': action}
        # Survives SIGTERM racing with the datagram during service teardown.
        temporary = Path(str(POWER) + f'.{os.getpid()}')
        try:
            temporary.write_text(json.dumps(payload), encoding='utf-8')
            os.replace(temporary, POWER)
        finally:
            temporary.unlink(missing_ok=True)
    elif event == 'quit':
        return  # Closing/restarting only ES is not a machine shutdown.
    elif event in ('system-selected', 'game-selected'):
        if not args:
            raise ValueError('Selection event requires a system name')
        payload['system'] = args[0]
    elif event == 'game-start':
        # ES launchGame sends ROM path, ROM basename, metadata title.
        # The first argument is NOT a system identifier for this event.
        title = args[2] if len(args) > 2 and args[2].strip() else ''
        if not title and len(args) > 1:
            title = args[1]
        if not title and args:
            title = Path(args[0].strip("'\"")).stem
        payload['title'] = ' '.join(title.split()) or UI['game']
    elif event != 'game-end':
        raise ValueError('Unsupported event')
    message = json.dumps(payload, ensure_ascii=False)
    # Retain only browsing selections, never replay a launch after restart.
    if 'system' in payload:
        temporary = Path(str(LAST) + f'.{os.getpid()}')
        try:
            temporary.write_text(message, encoding='utf-8')
            os.replace(temporary, LAST)
        finally:
            temporary.unlink(missing_ok=True)
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as client:
        try:
            client.sendto(message.encode('utf-8'), SOCKET)
        except (FileNotFoundError, ConnectionRefusedError):
            pass


class ScreenState:
    """Game state has priority over incidental selection events."""
    def __init__(self, system=''):
        self.system = system
        self.mode = 'browse'
        self.title = ''
        self.launched = 0.0
        self.generation = 0

    def handle(self, message, now):
        if not isinstance(message, dict):
            return
        event = message.get('event')
        if event in ('shutdown', 'reboot'):
            if self.mode not in ('shutdown', 'reboot'):
                self.mode = event
                self.generation += 1
            return
        if self.mode in ('shutdown', 'reboot'):
            return
        if event in ('system-selected', 'game-selected'):
            system = message.get('system')
            if self.mode == 'browse' and isinstance(system, str) and system:
                self.system = system
        elif event == 'game-start':
            title = message.get('title')
            self.title = title if isinstance(title, str) and title else UI['game']
            self.mode = 'loading'
            self.launched = now
            self.generation += 1
        elif event == 'game-end':
            self.mode = 'browse'
            self.title = ''
            self.generation += 1

    def advance(self, now):
        if self.mode == 'loading' and now - self.launched >= LOADING_SECONDS:
            self.mode = 'game'


def names():
    import xml.etree.ElementTree as ET
    result = {
        'nes': 'Nintendo NES', 'snes': 'Super Nintendo',
        'megadrive': 'Sega Mega Drive', 'mastersystem': 'Sega Master System',
        'psx': 'PlayStation', 'n64': 'Nintendo 64', 'gb': 'Game Boy',
        'gbc': 'Game Boy Color', 'gba': 'Game Boy Advance',
        'atari2600': 'Atari 2600', 'favorites': UI['favorites'],
        'all': UI['all'], 'recent': UI['recent'],
    }
    files = [Path('/usr/share/emulationstation/es_systems.cfg')]
    files += sorted(Path('/userdata/system/configs/emulationstation').glob('es_systems*.cfg'))
    for file in files:
        try:
            for system in ET.parse(file).getroot().findall('system'):
                key, label = system.findtext('name'), system.findtext('fullname')
                if key and label:
                    result[key] = label
        except (OSError, ET.ParseError):
            continue
    return result


class Display:
    def __init__(self):
        import fcntl
        from PIL import Image, ImageDraw, ImageFont
        self.Image, self.ImageDraw = Image, ImageDraw
        self.font = ImageFont.load_default(size=20)
        self.small = ImageFont.load_default(size=11)
        # Dedicated Unicode font for power screens; preserve accepted menu font.
        power_font = Path(__file__).resolve().parent / 'fonts' / 'DejaVuSans.ttf'
        self.power_font = ImageFont.truetype(str(power_font), 14)
        self.power_small = ImageFont.truetype(str(power_font), 10)
        brand_size = 17
        self.brand_font = ImageFont.truetype(str(power_font), brand_size)
        while self.brand_font.getlength('RETROGRZMOT') > 124:
            brand_size -= 1
            self.brand_font = ImageFont.truetype(str(power_font), brand_size)
        self.label = None
        self.label_image = None
        # Prefer a Unicode font when available; needed for Polish characters.
        for path in ('/usr/share/fonts/dejavu/DejaVuSans.ttf',
                     '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
            if Path(path).is_file():
                self.font = ImageFont.truetype(path, 20)
                self.small = ImageFont.truetype(path, 10)
                break
        self.fd = os.open('/dev/i2c-1', os.O_RDWR)
        try:
            fcntl.ioctl(self.fd, 0x0703, 0x3C)
            self.send(0, [0xAE, 0xD5, 0x80, 0xA8, 0x3F, 0xD3, 0,
                          0x40, 0x8D, 0x14, 0x20, 0, 0xA1, 0xC8,
                          0xDA, 0x12, 0x81, 0x7F, 0xD9, 0xF1,
                          0xDB, 0x40, 0xA4, 0xA6, 0x2E])
        except BaseException:
            os.close(self.fd)
            raise

    def send(self, control, payload):
        packet = bytes([control]) + bytes(payload)
        if os.write(self.fd, packet) != len(packet):
            raise OSError('Incomplete I2C write')

    def prepare_label(self, label):
        if self.label != label:
            draw = self.ImageDraw.Draw(self.Image.new('1', (1, 1)))
            box = draw.textbbox((0, 0), label, font=self.font)
            width = max(1, box[2] - box[0])
            self.label_image = self.Image.new('1', (width, 32))
            self.ImageDraw.Draw(self.label_image).text(
                (-box[0], (32 - (box[3] - box[1])) // 2 - box[1]),
                label, font=self.font, fill=1)
            self.label = label
        return max(0, self.label_image.width - 124)

    def show(self, label, boot=False, offset=0, loading_dots=None, power=None):
        image = self.Image.new('1', (128, 64))
        draw = self.ImageDraw.Draw(image)
        def centered(text, y, font):
            box = draw.textbbox((0, 0), text, font=font)
            x = (128 - (box[2] - box[0])) // 2 - box[0]
            draw.text((x, y - box[1]), text, font=font, fill=1)
        if boot:
            centered('RETROGRZMOT', 8, self.brand_font)
            draw.line((10, 30, 117, 30), fill=1)
            centered(UI['powered'], 38, self.power_small)
            centered('BATOCERA', 52, self.power_small)
        elif power:
            lines = UI['reboot'] if power == 'reboot' else UI['shutdown']
            for text, y in lines:
                centered(text, y, self.power_font)
        elif loading_dots is not None:
            centered('RETROGRZMOT', 3, self.small)
            draw.line((2, 18, 125, 18), fill=1)
            # Small lightning mark, drawn in pixels for the monochrome OLED.
            draw.polygon([(64, 22), (58, 33), (63, 33),
                          (60, 40), (70, 28), (64, 28)], fill=1)
            text = UI['loading']
            box = draw.textbbox((0, 0), text + '...', font=self.small)
            x = (128 - (box[2] - box[0])) // 2 - box[0]
            draw.text((x, 48 - box[1]), text + '.' * loading_dots,
                      font=self.small, fill=1)
        else:
            centered('RETROGRZMOT', 3, self.small)
            draw.line((2, 18, 125, 18), fill=1)
            overflow = self.prepare_label(label)
            if overflow:
                offset = max(0, min(overflow, offset))
                strip = self.label_image.crop((offset, 0, offset + 124, 32))
                image.paste(strip, (2, 25))
            else:
                image.paste(self.label_image, ((128 - self.label_image.width) // 2, 25))
        data = bytes(sum((1 << bit) if image.getpixel((x, page * 8 + bit)) else 0
                         for bit in range(8)) for page in range(8) for x in range(128))
        self.send(0, [0x21, 0, 127, 0x22, 0, 7])
        for offset in range(0, 1024, 16):
            self.send(0x40, data[offset:offset + 16])
        self.send(0, [0xAF])

    def close(self, keep_image=False):
        try:
            if not keep_image:
                self.send(0, [0xAE])
        finally:
            os.close(self.fd)


def run():
    import fcntl
    with open(str(BASE) + '.lock', 'w') as lock:
        # Early splash writes once under this same lock. Allow a short handover.
        for attempt in range(41):
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if attempt < 40:
                    time.sleep(0.05)
        else:
            raise SystemExit('Display service is already running')
        display = None
        power_shown_at = None
        running = True
        def stop(*_):
            nonlocal running
            running = False
        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as server:
            Path(SOCKET).unlink(missing_ok=True)
            server.bind(SOCKET)
            server.settimeout(0.05)
            try:
                POWER.unlink(missing_ok=True)
                display = Display()
                mapping = names()
                display.show('', boot=True)
                PID.write_text(str(os.getpid()))
                print('OLED ready: i2c-1 / 0x3c', flush=True)
                banner_until = time.monotonic() + 2
                state = ScreenState()
                shown = None
                label, overflow, started, last_frame, next_frame = '', 0, 0, None, 0
                try:
                    state.handle(json.loads(LAST.read_text(encoding='utf-8')), time.monotonic())
                except (OSError, ValueError):
                    pass
                while running:
                    try:
                        message = json.loads(server.recv(8192).decode('utf-8'))
                        state.handle(message, time.monotonic())
                    except socket.timeout:
                        pass
                    except (ValueError, UnicodeError):
                        continue
                    now = time.monotonic()
                    state.advance(now)
                    if now < banner_until and state.mode == 'browse' and state.generation == 0:
                        continue
                    key = (state.mode, state.title if state.mode != 'browse' else state.system,
                           state.generation)
                    if shown != key:
                        if state.mode == 'browse':
                            label = mapping.get(state.system, state.system) if state.system else UI['choose']
                        elif state.mode in ('shutdown', 'reboot'):
                            label = state.mode
                        else:
                            label = state.title
                        overflow = display.prepare_label(label) if state.mode in ('browse', 'game') else 0
                        started, last_frame, next_frame = now, None, now
                        shown = key
                        print(f'Screen: {state.mode} -> {label}', flush=True)
                    if now >= next_frame:
                        if state.mode in ('shutdown', 'reboot'):
                            frame = ('power', state.mode)
                            if frame != last_frame:
                                display.show('', power=state.mode)
                                power_shown_at = time.monotonic()
                        elif state.mode == 'loading':
                            frame = ('loading', 1 + int((now - state.launched) / 0.4) % 3)
                            if frame != last_frame:
                                display.show('', loading_dots=frame[1])
                        else:
                            frame = ('text', scroll_offset(now - started, overflow))
                            if frame != last_frame:
                                display.show(label, offset=frame[1])
                        last_frame = frame
                        next_frame = time.monotonic() + 0.1
            finally:
                PID.unlink(missing_ok=True)
                Path(SOCKET).unlink(missing_ok=True)
                if display is not None:
                    action = None
                    try:
                        saved = json.loads(POWER.read_text(encoding='utf-8'))
                        action = power_action(saved.get('event'))
                    except (OSError, ValueError, AttributeError):
                        pass
                    try:
                        if action:
                            if power_shown_at is None:
                                display.show('', power=action)
                                power_shown_at = time.monotonic()
                            # Brief bounded hold, never a long shutdown delay.
                            remaining = MIN_POWER_SECONDS - (time.monotonic() - power_shown_at)
                            if remaining > 0:
                                time.sleep(remaining)
                    finally:
                        display.close(keep_image=bool(action))


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else ''
    if command == 'run':
        run()
    elif command == 'language':
        print(LANGUAGE)
    elif command == 'event':
        forward(sys.argv[2], sys.argv[3:])
    elif command == 'status':
        raise SystemExit(0 if process_id() else 1)
    elif command == 'stop':
        pid = process_id()
        if pid:
            os.kill(pid, signal.SIGTERM)
            for _ in range(40):
                if process_id() != pid:
                    break
                time.sleep(0.1)
            else:
                raise SystemExit('Service did not stop; inspect /tmp/retrogrzmot-oled.log')
    else:
        raise SystemExit('Usage: oled.py run|status|stop|language|event EVENT [ARG...]')


if __name__ == '__main__':
    main()
