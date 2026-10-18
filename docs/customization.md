# Change display settings

You can keep every default. These steps are optional.

## Choose the OLED language

The program defaults to Polish, matching the original RETROGRZMOT console. English labels are included. Console and game names still come from Batocera's metadata; they are not translated.

Connect to the Pi with SSH as explained in [Installation](installation.md).

**Raspberry Pi / SSH — switch to English:**

```sh
bash /userdata/system/services/retrogrzmot_oled stop
```

```sh
printf 'en\n' > /userdata/system/retrogrzmot/language.txt
```

```sh
bash /userdata/system/services/retrogrzmot_oled start
```

**Expected:** the startup tagline says `powered by` and the loading caption says `LOADING`.

If you installed the early startup screen, update its saved image too:

```sh
bash /userdata/system/retrogrzmot/install-early.sh
```

To return to Polish, repeat those steps with `pl` instead of `en`. The file must contain only `pl` or `en`. If the program reports an invalid language, fix the file before starting the service.

The original Polish behavior was checked on hardware. English rendering has local automated tests but still needs a physical-screen confirmation.

## Change scrolling or loading time

These are ordinary constants near the beginning of `retrogrzmot/oled.py`:

| Setting | Default | Meaning |
| --- | --- | --- |
| `SCROLL_SPEED` | `18` | Pixels moved per second; larger means faster |
| `SCROLL_PAUSE` | `1.5` | Seconds paused at each end |
| `LOADING_SECONDS` | `3.0` | Duration of the launch animation, not actual load progress |
| `MIN_POWER_SECONDS` | `1.5` | Minimum time the shutdown/restart message is kept visible during service teardown |

Read [Editing and testing](development.md) before changing a file. Keep timing values positive. After editing `oled.py`, restart the service to load the new code.

## Display address and size

The shipped driver and early splash both use **bus 1, address 0x3C and 128×64 pixels**. There is no automatic controller detection. If an OLED responds at 0x3D, both drivers would need a corresponding change and a hardware test. Changing the resolution needs changes to initialization, rendering and the saved early image. This guide does not claim support for those variants.

## Font and branding

Power screens use the bundled DejaVu font so Polish letters render reliably. Console/game text retains the font-selection behavior of the tested project. Not every character in every game's title is guaranteed to exist in the selected font.

Changing `RETROGRZMOT` or the startup layout requires rebuilding the early image too. The [development guide](development.md#rebuild-the-early-image) explains how. Individual game artwork and custom per-game fonts are deliberately outside this version's scope.
