"""Local tests without a connected screen; run with Python + Pillow."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

from PIL import Image, ImageDraw, ImageFont  # Load before mocking OS I/O.

spec = importlib.util.spec_from_file_location(
    'oled', Path(__file__).resolve().parents[1] / 'retrogrzmot' / 'oled.py')
oled = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oled)


class StateTests(unittest.TestCase):
    def test_power_has_priority_and_plain_quit_is_ignored(self):
        self.assertIsNone(oled.power_action('quit'))
        self.assertIsNone(oled.power_action('quit', ['restart']))
        self.assertEqual(oled.power_action('quit', ['shutdown']), 'shutdown')
        self.assertEqual(oled.power_action('quit', ['reboot']), 'reboot')
        state = oled.ScreenState('nes')
        state.handle({'event': 'shutdown'}, 1)
        for message in ({'event': 'game-start', 'title': 'Mario'},
                        {'event': 'game-end'}, {'event': 'system-selected', 'system': 'snes'}):
            state.handle(message, 2)
        state.advance(100)
        self.assertEqual((state.mode, state.system), ('shutdown', 'nes'))

    def test_shutdown_marker_survives_missed_socket_message(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            marker = root / 'power.json'
            fake_fcntl = types.SimpleNamespace(flock=Mock(side_effect=[BlockingIOError(), None]), LOCK_EX=1, LOCK_NB=2)
            def interrupted_receive(*args):
                marker.write_text('{"event":"shutdown"}', encoding='utf-8')
                raise KeyboardInterrupt
            with patch.dict(sys.modules, {'fcntl': fake_fcntl}), \
                 patch.object(oled, 'BASE', root / 'base'), \
                 patch.object(oled, 'PID', root / 'pid'), \
                 patch.object(oled, 'LAST', root / 'last'), \
                 patch.object(oled, 'POWER', marker), \
                 patch.object(oled, 'SOCKET', str(root / 'socket')), \
                 patch.object(oled.socket, 'AF_UNIX', 1, create=True), \
                 patch.object(oled.socket, 'socket') as factory, \
                 patch.object(oled, 'Display') as constructor, \
                 patch.object(oled.signal, 'signal'), \
                 patch.object(oled.time, 'sleep'):
                factory.return_value.__enter__.return_value.recv.side_effect = interrupted_receive
                with self.assertRaises(KeyboardInterrupt):
                    oled.run()
                constructor.return_value.show.assert_any_call('', power='shutdown')
                constructor.return_value.close.assert_called_once_with(keep_image=True)
                self.assertEqual(fake_fcntl.flock.call_count, 2)

    def test_launch_title_and_return(self):
        state = oled.ScreenState('nes')
        state.handle({'event': 'game-start', 'title': 'Super Mario Bros.'}, 10)
        self.assertEqual(state.mode, 'loading')
        state.advance(12.99)
        self.assertEqual(state.mode, 'loading')
        state.advance(13)
        self.assertEqual((state.mode, state.title), ('game', 'Super Mario Bros.'))
        state.handle({'event': 'game-end'}, 20)
        self.assertEqual((state.mode, state.system), ('browse', 'nes'))

    def test_early_exit_cancels_loading(self):
        state = oled.ScreenState('psx')
        state.handle({'event': 'game-start', 'title': 'Crash'}, 1)
        state.handle({'event': 'game-end'}, 2)
        state.advance(100)
        self.assertEqual((state.mode, state.title), ('browse', ''))

    def test_selection_does_not_replace_active_game(self):
        state = oled.ScreenState('nes')
        state.handle({'event': 'game-start', 'title': 'Mario'}, 1)
        for moment in (2, 6):
            state.advance(moment)
            state.handle({'event': 'game-selected', 'system': 'snes'}, moment)
            self.assertEqual(state.system, 'nes')
            self.assertEqual(state.title, 'Mario')

    def test_launch_arguments_and_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            snapshot = Path(folder) / 'last.json'
            with patch.object(oled, 'LAST', snapshot), \
                 patch.object(oled.socket, 'AF_UNIX', 1, create=True), \
                 patch.object(oled.socket, 'socket') as factory:
                import json
                client = factory.return_value.__enter__.return_value
                oled.forward('system-selected', ['nes'])
                before = snapshot.read_bytes()
                oled.forward('game-start', ['/userdata/roms/nes/Mario.zip', 'Mario', 'Super Mario Bros.'])
                payload = json.loads(client.sendto.call_args.args[0])
                self.assertEqual(payload['title'], 'Super Mario Bros.')
                self.assertNotIn('system', payload)
                self.assertEqual(snapshot.read_bytes(), before)
                oled.forward('game-start', ['/roms/My Game.zip'])
                payload = json.loads(client.sendto.call_args.args[0])
                self.assertEqual(payload['title'], 'My Game')
                oled.forward('game-end', [])
                payload = json.loads(client.sendto.call_args.args[0])
                self.assertEqual(payload, {'event': 'game-end'})

    def test_scroll_pauses_and_bounds(self):
        for distance in (0, 1, 150, 400):
            self.assertEqual(oled.scroll_offset(1, distance), 0)
            self.assertEqual(oled.scroll_offset(1.5 + distance / 18, distance), distance)
            for tick in range(600):
                self.assertTrue(0 <= oled.scroll_offset(tick / 10, distance) <= distance)
            if distance:
                self.assertEqual(oled.scroll_offset(3 + 2 * distance / 18, distance), 0)


class RenderingTests(unittest.TestCase):
    def test_text_endpoints_and_loading_frames(self):
        packets = []
        def write(fd, packet):
            packets.append(packet)
            return len(packet)
        with patch.dict(sys.modules, {'fcntl': types.SimpleNamespace(ioctl=lambda *args: None)}), \
             patch.object(oled.os, 'open', return_value=99), \
             patch.object(oled.os, 'write', side_effect=write), \
             patch.object(oled.os, 'close'):
            display = oled.Display()
            packets.clear()
            display.show('', boot=True)
            boot_frame = b''.join(p[1:] for p in packets if p[0] == 64)
            saved_frame = Path(oled.__file__).parent / 'early' / 'splash.bin'
            self.assertEqual(boot_frame, saved_frame.read_bytes())
            for text in ('NES', 'Nintendo Entertainment System', 'Super Mario Bros. 3'):
                overflow = display.prepare_label(text)
                for offset in (0, overflow):
                    packets.clear()
                    display.show(text, offset=offset)
                    data = b''.join(p[1:] for p in packets if p[0] == 64)
                    self.assertEqual(len(data), 1024)
                    image = Image.new('1', (128, 64))
                    image.putdata([255 if data[(y // 8) * 128 + x] & (1 << (y % 8)) else 0
                                   for y in range(64) for x in range(128)])
                    expected = display.label_image.crop((offset, 0, offset + 124, 32)) if overflow else display.label_image
                    x0 = 2 if overflow else (128 - expected.width) // 2
                    self.assertEqual(image.crop((x0, 25, x0 + expected.width, 57)).tobytes(), expected.tobytes())
            frames = []
            for dots in (1, 2, 3):
                packets.clear()
                display.show('', loading_dots=dots)
                frame = b''.join(p[1:] for p in packets if p[0] == 64)
                self.assertEqual(len(frame), 1024)
                frames.append(frame)
            self.assertEqual(len(set(frames)), 3)
            for power in ('shutdown', 'reboot'):
                packets.clear()
                display.show('', power=power)
                data = b''.join(p[1:] for p in packets if p[0] == 64)
                self.assertEqual(len(data), 1024)
            for text in ('WYŁĄCZANIE', 'RETROGRZMOTA', 'URUCHAMIANIE'):
                box = display.power_font.getbbox(text)
                self.assertLessEqual(box[2] - box[0], 124)
            packets.clear()
            display.close(keep_image=True)
            self.assertEqual(packets, [])
            display.close()
            self.assertEqual(packets[-1], bytes([0, 0xAE]))

    def test_english_screens_and_saved_image(self):
        packets = []
        def write(fd, packet):
            packets.append(packet)
            return len(packet)
        with patch.dict(sys.modules, {'fcntl': types.SimpleNamespace(ioctl=lambda *args: None)}), \
             patch.object(oled.os, 'open', return_value=99), \
             patch.object(oled.os, 'write', side_effect=write), \
             patch.object(oled.os, 'close'), \
             patch.object(oled, 'UI', oled.TEXT['en']):
            display = oled.Display()
            for text, y in oled.UI['shutdown'] + oled.UI['reboot']:
                box = display.power_font.getbbox(text)
                self.assertLessEqual(box[2] - box[0], 124)
                self.assertLessEqual(y + box[3] - box[1], 64)
            packets.clear()
            display.show('', boot=True)
            frame = b''.join(p[1:] for p in packets if p[0] == 64)
            self.assertEqual(frame, (Path(oled.__file__).parent / 'early/splash-en.bin').read_bytes())
            for power in ('shutdown', 'reboot'):
                packets.clear()
                display.show('', power=power)
                self.assertEqual(sum(len(p)-1 for p in packets if p[0] == 64), 1024)
            self.assertEqual(oled.names()['favorites'], 'Favorites')
            state = oled.ScreenState()
            state.handle({'event': 'game-start'}, 0)
            self.assertEqual(state.title, 'Game')
            display.close()


class EarlySplashTests(unittest.TestCase):
    def setUp(self):
        self.fcntl = types.SimpleNamespace(flock=Mock(), ioctl=Mock(), LOCK_EX=1, LOCK_NB=2)
        spec = importlib.util.spec_from_file_location(
            'early_splash', Path(oled.__file__).parent / 'early' / 'splash.py')
        self.early = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'fcntl': self.fcntl}):
            spec.loader.exec_module(self.early)
        self.frame_path = Path(oled.__file__).parent / 'early' / 'splash.bin'

    def test_early_transfer_and_handover(self):
        packets = []
        def write(fd, packet):
            packets.append(packet)
            return len(packet)
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(self.early, 'LOCK', str(Path(directory) / 'lock')), \
                 patch.object(self.early.os.path, 'exists', return_value=True), \
                 patch.object(self.early.os, 'open', return_value=99), \
                 patch.object(self.early.os, 'write', side_effect=write), \
                 patch.object(self.early.os, 'close') as close:
                self.assertTrue(self.early.splash(self.frame_path))
                data = b''.join(p[1:] for p in packets if p[0] == 64)
                self.assertEqual(data, self.frame_path.read_bytes())
                self.assertEqual(packets[-1], bytes([0, 0xAF]))
                close.assert_called_once_with(99)

    def test_early_skips_busy_display(self):
        self.fcntl.flock.side_effect = BlockingIOError
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(self.early, 'LOCK', str(Path(directory) / 'lock')), \
                 patch.object(self.early.os.path, 'exists', return_value=True), \
                 patch.object(self.early.os, 'open') as bus_open:
                self.assertFalse(self.early.splash(self.frame_path))
                bus_open.assert_not_called()

    def test_missing_bus_and_invalid_frame(self):
        with patch.object(self.early.os.path, 'exists', return_value=False), \
             patch.object(self.early.time, 'monotonic', side_effect=[0, 1]), \
             patch.object(self.early.os, 'open') as bus_open:
            self.assertFalse(self.early.splash(self.frame_path, wait_seconds=0))
            bus_open.assert_not_called()
        with self.assertRaises(ValueError):
            self.early.splash(Path(oled.__file__))


if __name__ == '__main__':
    unittest.main()
