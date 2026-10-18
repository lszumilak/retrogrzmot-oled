"""Render power screens and build the early splash from actual I2C frames."""
from pathlib import Path
import sys
import types
from unittest.mock import patch
from PIL import Image, ImageDraw
from test_oled import oled

packets = []
def write(fd, packet):
    packets.append(packet)
    return len(packet)

sheet = Image.new('RGB', (128 * 4, (64 * 4 + 28) * 3), '#171717')
labels = [('START', {'boot': True}),
          ('WYLACZANIE', {'power': 'shutdown'}),
          ('RESTART', {'power': 'reboot'})]
with patch.dict(sys.modules, {'fcntl': types.SimpleNamespace(ioctl=lambda *args: None)}), \
     patch.object(oled.os, 'open', return_value=99), \
     patch.object(oled.os, 'write', side_effect=write), \
     patch.object(oled.os, 'close'):
    screen = oled.Display()
    for language in ('pl', 'en'):
        with patch.object(oled, 'UI', oled.TEXT[language]):
            for index, (label, options) in enumerate(labels):
                packets.clear()
                screen.show('', **options)
                data = b''.join(p[1:] for p in packets if p[0] == 64)
                if options.get('boot'):
                    filename = 'splash.bin' if language == 'pl' else 'splash-en.bin'
                    splash = Path(__file__).resolve().parents[1] / 'retrogrzmot' / 'early' / filename
                    splash.write_bytes(data)
                if language == 'pl':
                    frame = Image.new('1', (128, 64))
                    frame.putdata([255 if data[(y // 8) * 128 + x] & (1 << (y % 8)) else 0
                                   for y in range(64) for x in range(128)])
                    y0 = index * (64 * 4 + 28)
                    ImageDraw.Draw(sheet).text((8, y0 + 6), label, fill='white')
                    sheet.paste(frame.convert('RGB').resize((512, 256), Image.Resampling.NEAREST), (0, y0 + 28))
    screen.close()
output = Path(__file__).resolve().parents[1] / 'docs' / 'images' / 'power-preview.png'
sheet.save(output)
print(output)
