# Editing and testing

## You do not need to compile this project

Python reads `.py` files when it starts. Bash reads `.sh` files. The font and saved 1024-byte startup image are included. You do not need an Arduino IDE, a C compiler, or a custom build of Batocera/EmulationStation.

`python3 -m py_compile` checks Python syntax; it is not a required build step and it does not prove hardware compatibility.

## Where to write code

Keep an extracted copy of the repository on your Windows computer. Use a code editor such as Visual Studio Code, or another editor that supports **UTF-8** and **LF** line endings. Do not edit code in Word or another word processor.

The program on the Pi lives at `/userdata/system/retrogrzmot`. Edit your local copy, save it, then copy it to the Pi. Saving a Windows file does not automatically update the Pi.

| File | Purpose |
| --- | --- |
| `retrogrzmot/oled.py` | Drawing, I²C transfer, display states and event forwarding |
| `retrogrzmot/retrogrzmot-oled` | Start/stop/status service wrapper |
| `retrogrzmot/install.sh` | Install service and seven Batocera event scripts |
| `retrogrzmot/install-early.sh` | Install optional early boot files |
| `retrogrzmot/early/splash.py` | One-shot early image writer, no Pillow needed |
| `retrogrzmot/early/boot-custom.sh` | Starts that writer in the background |
| `retrogrzmot/early/splash.bin` | Polish startup image, exactly 1024 bytes |
| `retrogrzmot/early/splash-en.bin` | English startup image, exactly 1024 bytes |
| `tests/test_oled.py` | Local tests without an attached OLED |
| `tests/preview_oled.py` | Build screen preview and both saved startup images |

Do not change files inside Batocera's system image for ordinary edits. This integration uses `/userdata` and a small optional `/boot` hook.

## A small edit, step by step

1. Make a backup of the working Pi program as described in [Updates](troubleshooting.md#update-the-oled-software).
2. Change one setting in your Windows copy of `retrogrzmot/oled.py`, for example `SCROLL_PAUSE`.
3. Save the file as UTF-8. Bash scripts must use LF, not Windows CRLF.
4. Through SSH, stop the OLED service:

```sh
bash /userdata/system/services/retrogrzmot_oled stop
```

5. From Windows PowerShell, opened in the extracted repository directory, copy the edited file. Replace `PI_IP`:

```powershell
scp .\retrogrzmot\oled.py root@PI_IP:/userdata/system/retrogrzmot/
```

6. Back in SSH, check syntax:

```sh
python3 -m py_compile /userdata/system/retrogrzmot/oled.py
```

No output means syntax passed. A traceback means stop and fix the problem before starting the service.

7. Start the service:

```sh
bash /userdata/system/services/retrogrzmot_oled start
```

8. Check actual behavior. If it failed, read `/tmp/retrogrzmot-oled.log` and restore your backup.

Re-run the installer if you changed service or event scripts. Do not run a separate test program that writes to the screen while the service is active.

## Rebuild the early image

The startup image is pre-rendered so early boot does not need Pillow or `/userdata`. If you change branding or the startup layout, regenerate both language images on your development computer before copying the program to the Pi.

Install Python 3 and Pillow on the development computer if needed. This is for your computer, not an instruction to install packages into Batocera. From the repository directory:

```sh
python -m pip install -r requirements-dev.txt
```

```sh
python tests/preview_oled.py
```

This creates `docs/images/power-preview.png`, plus `retrogrzmot/early/splash.bin` and `splash-en.bin`. It captures the driver's actual output bytes with hardware access mocked. View the PNG, copy the changed files to the Pi and run `install-early.sh` again.

Different Pillow/FreeType versions can shift individual font pixels between Windows and Linux. The saved splash remains a valid 1024-byte frame. Tests verify its layout and transfer separately rather than requiring every font pixel to match a different machine's rasterizer.

## Run local tests

From the repository directory:

```sh
python tests/test_oled.py
```

The tests check display-state transitions, interrupted loading, title arguments, scroll limits, full frame transfer, shutdown priority, the shutdown race and early-writer handover. They also check both languages and their saved startup images.

GitHub Actions runs the tests on Linux after repository changes and checks Bash syntax. The local Windows test environment mocks Linux-specific interfaces. Neither environment measures a physical OLED or verifies a new Batocera release.

## Event flow

Batocera calls the small scripts under `/userdata/system/configs/emulationstation/scripts/<event>/`. Those scripts forward data over a local Unix socket. A single process owns the display and renders the current state. During a game, incidental selection events cannot overwrite the title; shutdown/reboot takes priority over all ordinary states.

`game-selected` supplies the system identifier. `game-start` has a different argument layout in the tested integration: ROM path, ROM basename, metadata title. Keep this distinction when changing event handling.

The early writer and normal service share `/tmp/retrogrzmot-oled.lock`. Do not bypass it or create a second permanent display-writing process.
