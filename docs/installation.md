# Install the OLED software — Windows beginner guide

Allow time for each step. If a result differs from the example, stop and read [Troubleshooting](troubleshooting.md) before continuing.

## 1. Check the starting point

You should already have a working Batocera installation and the four wires connected as shown in [Wiring](wiring.md). This project was tested with **Batocera 42 on Raspberry Pi 3B+**. Do not reinstall a working Batocera system just to use this guide.

Connect the Pi and Windows computer to the same local network. Ethernet is fine. In Batocera, open **MAIN MENU → NETWORK SETTINGS** and note its IP address. We call this `PI_IP` below. Replace that text with your Pi's actual address every time you see it; do not type the letters `PI_IP` literally.

## 2. Learn which window to use

On Windows, open Start, type **PowerShell**, and open it. Its prompt normally looks like:

```text
PS C:\Users\YourName>
```

The prompt is the text before your cursor. **Never copy the prompt, command output or error messages as part of a command.** Copy only the line inside the command box.

There will be two kinds of commands:

| Label in this guide | Where you type it | Prompt usually starts with |
| --- | --- | --- |
| **Windows PowerShell** | Your Windows computer | `PS C:\...>` |
| **Raspberry Pi / SSH** | A PowerShell window after connecting to the Pi | `[root@BATOCERA ~]#` |

Keep a second PowerShell window open for Windows file-copy commands. If you accidentally connected in that window too, type `exit` to return to Windows. `exit` closes the SSH connection; it does not shut down the Pi.

## 3. Connect to the Pi

**Windows PowerShell** — replace `PI_IP`:

```powershell
ssh root@PI_IP
```

If asked whether you trust the device, check that the address is your Pi and enter `yes`. Enter the Batocera password. If unchanged, the standard password is `linux`; if security settings changed it, use your configured password. Password characters are invisible while typing — that is normal. Press Enter.

**Expected:** a prompt starting with `[root@BATOCERA`. You are now typing commands on the Raspberry Pi. Do not share your password in an issue or chat.

If login fails, check Batocera's [SSH and security instructions](https://wiki.batocera.org/access_the_batocera_via_ssh). Do not open SSH to the public Internet for this project.

## 4. Enable the I²C connection

I²C is the two-wire link used by the OLED. First inspect its setting.

**Raspberry Pi / SSH:**

```sh
grep -n i2c_arm /boot/config.txt
```

If you see `dtparam=i2c_arm=on` **without a leading `#`**, skip the edit below and continue to the bus check. If you see the exact line `#dtparam=i2c_arm=on`, perform these steps one at a time:

```sh
mount -o remount,rw /boot
```

```sh
cp -n /boot/config.txt /boot/config.txt.before-oled
```

```sh
sed -i 's/^#dtparam=i2c_arm=on$/dtparam=i2c_arm=on/' /boot/config.txt
```

```sh
grep -n i2c_arm /boot/config.txt
```

**Expected:** the line now has no `#` at the beginning. If the setting is missing, appears several times, is in a board-specific section, or says `off`, do not blindly add conflicting settings: check the full file with someone who understands the configuration.

Save and restart:

```sh
sync
```

```sh
reboot
```

The SSH window disconnects. Wait for Batocera to return, then reconnect using `ssh root@PI_IP` from Windows. A lost connection during a requested restart is expected.

## 5. Confirm that the Pi can see the screen

**Raspberry Pi / SSH:**

```sh
i2cdetect -l
```

**Expected:** a line beginning with `i2c-1`. Another bus such as `i2c-2` can also be present. The screen in this guide uses bus 1.

Scan that bus:

```sh
i2cdetect -y 1
```

**Expected:** a table containing **`3c`**. Most other cells will be `--`. A `3c` response means a device answers at address `0x3C`; it does not independently prove its controller model.

If there is no `3c`, stop. Do not install the display program yet. See [Missing screen or wrong address](troubleshooting.md#the-scan-does-not-show-3c).

## 6. Check Python and Pillow

Python runs the code; Pillow draws the text into a 128×64 image.

**Raspberry Pi / SSH:**

```sh
python3 -c "import sys; print(sys.version); from PIL import Image, ImageDraw, ImageFont; print('Pillow: OK')"
```

**Expected:** the Python version and `Pillow: OK`. Development used Python 3.12.8. If `PIL` cannot be imported or the program later rejects font sizing, stop: your Batocera image has different dependencies. This guide does not install arbitrary packages into Batocera's system image.

## 7. Download the project on Windows

1. Open [the repository](https://github.com/lszumilak/retrogrzmot-oled).
2. Click the green **Code** button, then **Download ZIP**.
3. In Windows File Explorer, right-click the downloaded ZIP and choose **Extract All**. Open the extracted directory until you see `README.md`, `docs`, `tests`, and **`retrogrzmot`**.
4. The inner **`retrogrzmot`** folder is the program that goes onto the Pi. The outer folder also contains documentation and tests.

No GitHub account or Git installation is needed to download the public project.

## 8. Copy the program to the Pi

In File Explorer, open the folder containing that inner `retrogrzmot` folder. Click the address bar, type `powershell` and press Enter. This opens a new PowerShell window in the correct directory. Check that the prompt begins with `PS`, not `[root@BATOCERA`.

**Windows PowerShell** — replace `PI_IP`:

```powershell
scp -r .\retrogrzmot root@PI_IP:/userdata/system/
```

Enter the Pi password if asked. This sends the program folder over your local network.

**Expected:** files copy without errors, and the Windows prompt returns. On the Pi they should now be inside `/userdata/system/retrogrzmot`, not a second nested `retrogrzmot/retrogrzmot` folder.

If Windows does not recognize `ssh` or `scp`, enable the Windows **OpenSSH Client** optional feature, or use an SFTP client to copy the same folder. Use SFTP to port 22, the Pi address, and your Batocera login.

## 9. Install and start the normal service

Return to the window connected to the Pi.

**Raspberry Pi / SSH:**

```sh
ls /userdata/system/retrogrzmot
```

**Expected:** files including `oled.py`, `install.sh`, `install-early.sh`, plus the `fonts` and `early` directories.

Run:

```sh
bash /userdata/system/retrogrzmot/install.sh
```

**Expected:** `RETROGRZMOT OLED is ready...`. The OLED shows the startup screen, then a console name or the selection prompt. Scroll through consoles on the TV: the OLED should follow. A long name starts scrolling after a short pause.

The installer creates one Batocera service named **`retrogrzmot_oled`** and seven small event scripts. It enables automatic startup and starts the service. You do not need to compile anything or use `batocera-save-overlay`.

## 10. Add the earlier startup logo (optional)

Do this only after the normal screen works.

**Raspberry Pi / SSH:**

```sh
bash /userdata/system/retrogrzmot/install-early.sh
```

**Expected:** `Early splash installed...`. If it reports that another `boot-custom.sh` exists, stop. The installer deliberately refuses to overwrite someone else's startup script. The existing file needs to be combined by an experienced person.

Restart the **device** from the Batocera menu. The logo should appear earlier, while Batocera is still loading. Its exact timing depends on when Linux exposes I²C. This does not make the logo appear at the instant power is connected.

## 11. Check the whole cycle

| Action | Expected result |
| --- | --- |
| Scroll through consoles | Names change; long ones scroll |
| Open a console's game list | Console name remains |
| Launch a game | Loading dots for 3 seconds, then game title |
| Leave the game | Console name returns |
| Restart the device from its menu | Restart message, then startup logo |
| Shut down from its menu | Shutdown message |

On a normally mapped PS4 controller, hold **PS** and press **OPTIONS** to leave a game. The general Batocera shortcut is **HOTKEY + START**; it depends on your controller mapping. If SHARE is your HOTKEY, use SHARE + OPTIONS.

The shutdown message may remain while the OLED still receives power. It is not a signal that shutdown is already complete. Use Batocera's normal shutdown procedure before disconnecting the power supply.

If everything matches, installation is complete. Continue to [Customization](customization.md) only if you want to change the display language or timings.
