# Troubleshooting, updates and disabling

## A command failed

Stop at the first error. Copy the command you ran and its output when asking for help. Include your Pi model and Batocera version. Do not include passwords or other private information.

Commands beginning with `ssh` or `scp` in the installation guide run on **Windows**. Commands using `/userdata/...` or `/boot/...` run on the **Pi through SSH**. A Windows error mentioning `C:\boot` means the Linux command was entered on Windows.

If you accidentally paste a prompt or an error message into SSH, do not keep pasting the resulting errors. Wait for the next prompt and enter only the actual command.

## The scan does not show 3c

- Check that `i2c-1` exists with `i2cdetect -l`.
- Verify `dtparam=i2c_arm=on` is enabled and that the Pi was restarted after the edit.
- Shut down and unplug the Pi before inspecting the four wires. Compare the screen's printed labels with the wiring table.
- A response at `3d` is a different address from the tested configuration. Stop rather than pretending the driver auto-detects it.
- A scan response confirms an address, not the controller. SH1106 and other displays can look similar but require different commands.

Do not scan unrelated I²C buses or change wires on a powered board to experiment.

## The OLED is black after installation

**Raspberry Pi / SSH:**

```sh
cat /tmp/retrogrzmot-oled.log
```

Read the last messages. Missing Python libraries, font files or I²C access are common causes. Check that `fonts/DejaVuSans.ttf` was copied together with the program. Run the dependency check from the installation guide again.

You can also check the service:

```sh
python3 /userdata/system/retrogrzmot/oled.py status
```

That command prints nothing on success. To show its exit status, immediately run:

```sh
echo $?
```

`0` means a matching running process was found; `1` means it was not. This is a process check, not a guarantee that every event is working.

## The screen works but does not follow the menu

Manually simulate one selection:

```sh
python3 /userdata/system/retrogrzmot/oled.py event system-selected nes
```

If that changes the display, check the installed event script:

```sh
cat /userdata/system/configs/emulationstation/scripts/system-selected/retrogrzmot-oled.sh
```

Re-run the main installer if this project's script is missing. Do not replace the entire events directory: it may contain other projects' scripts.

## Invalid service name

Use **`retrogrzmot_oled`** for the Batocera service, with an underscore. Batocera rejects hyphens in service names. Hyphens remain valid in this project's log and event-script filenames. The installer checks the saved autostart setting because Batocera can print a validation error without a nonzero exit code.

## The early logo does not appear

Check:

```sh
cat /tmp/retrogrzmot-early.log
```

`display already owned by service` means the regular service got there first; the early writer correctly avoided a competing write. `I2C unavailable` means the bus did not appear within the eight-second background wait. Python or module errors indicate a different early-boot environment from the tested setup.

The early hook runs in the background and does not wait in the system's main startup path. It cannot show a logo before Linux and the I²C driver are available. An existing custom `boot-custom.sh` needs manual integration; the installer refuses to overwrite it.

## Other known limitations

- Settings-menu detection and individual game graphics are intentionally absent.
- A video/game screensaver can emit `game-selected`, so it may change the displayed console name while browsing. There is no special screensaver filtering yet.
- The three-second animation does not prove the game has finished loading.
- Shutdown/restart messages depend on EmulationStation's menu events. Abrupt power removal cannot show a message. Shutdown from SSH or a hardware button has not been integrated or verified here.
- A halted Pi can still power the OLED. The shutdown caption may stay on screen until power is removed; it does not mean shutdown has already completed.
- Restarting the OLED service while a game is already running does not reconstruct the running-game state; leave the game and launch it again.
- An unknown system falls back to its identifier. Very long names can take time to scroll completely.

## Stop the software without deleting it

**Raspberry Pi / SSH:**

```sh
batocera-services disable retrogrzmot_oled
```

```sh
bash /userdata/system/services/retrogrzmot_oled stop
```

This disables normal automatic startup and stops the regular process. Unless a shutdown event is already active, the OLED is switched off. The early startup hook is separate and may still show a logo at the next boot.

To disable only the early hook, first inspect it:

```sh
cat /boot/boot-custom.sh
```

Only if it is **this project's unmodified hook**, move it out of `/boot`:

```sh
mount -o remount,rw /boot
```

```sh
mv /boot/boot-custom.sh /userdata/system/retrogrzmot/boot-custom.disabled.sh
```

```sh
sync
```

Do not do this if another person has combined other startup actions into that file. The remaining `/boot/retrogrzmot-early` files are inactive without a hook.

For complete removal, disable both startup mechanisms first, preserve any useful backups, then remove only this project's service and seven `retrogrzmot-oled.sh` event files, its program folder and its early-boot directory. Leave other projects' scripts and all parent event directories in place. If you are unsure which files belong to the project, disabling it is sufficient until someone can help.

## Update the OLED software

1. Read the release notes. Download and extract the new version on Windows.
2. Stop the service through SSH.
3. Make a new backup folder on the Pi. For example, if `/userdata/system/retrogrzmot-backup` does **not** already exist:

```sh
cp -a /userdata/system/retrogrzmot /userdata/system/retrogrzmot-backup
```

4. Copy the new `retrogrzmot` directory using the same Windows `scp` command as during installation.
5. Run `install.sh`. Run `install-early.sh` too if early-boot files changed or you changed language.
6. Repeat the complete manual cycle in the installation guide. Keep the backup until satisfied.

Your optional `language.txt` is not shipped with the package, so a normal copy into the existing folder preserves it. To roll back, stop the service and restore files from the saved folder. Install its service/hooks again, and re-install the old early hook/image if needed. Do not overwrite unrelated custom boot scripts.

## After a Batocera update

Compatibility with future versions is not guaranteed. Back up the microSD card or important data before updating Batocera. Then check:

1. `/dev/i2c-1`, address `0x3C`, Python and Pillow are still available.
2. Console names and scrolling, opening game lists, starting and leaving a game.
3. Both device restart and shutdown from the menu.
4. Early startup logo and its log; check whether the update preserved `/boot/boot-custom.sh` and `/boot/retrogrzmot-early`.
5. Any other GPIO projects still work.

Record the actual board and Batocera version when reporting a result. The tested baseline is Batocera 42; a passing local test suite does not replace these hardware checks.
