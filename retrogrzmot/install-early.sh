#!/bin/bash
set -eu
APP=/userdata/system/retrogrzmot
HOOK=/boot/boot-custom.sh
DEST=/boot/retrogrzmot-early

test -f "$APP/early/splash.py"
test -f "$APP/early/splash.bin"
test -f "$APP/early/boot-custom.sh"
python3 -m py_compile "$APP/early/splash.py"
language=$(python3 "$APP/oled.py" language)
FRAME="$APP/early/splash.bin"
if test "$language" = en; then
    FRAME="$APP/early/splash-en.bin"
fi
python3 -c 'import sys; from pathlib import Path; assert len(Path(sys.argv[1]).read_bytes()) == 1024' "$FRAME"
bash -n "$APP/early/boot-custom.sh"

if test -e "$HOOK" && ! grep -qx '# RETROGRZMOT EARLY BOOT v1' "$HOOK"; then
    echo 'A custom boot-custom.sh exists. Stopping without overwriting it.' >&2
    exit 1
fi
if test -e "$DEST" && ! test -f "$DEST/retrogrzmot-managed"; then
    echo 'An unmanaged /boot/retrogrzmot-early directory exists. Installation stopped.' >&2
    exit 1
fi

was_readonly=0
case ",$(awk '$2 == "/boot" {print $4}' /proc/mounts)," in
    *,ro,*) was_readonly=1 ;;
esac
mount -o remount,rw /boot
finish() {
    sync
    if test "$was_readonly" = 1; then
        mount -o remount,ro /boot
    fi
}
trap finish EXIT
if test -e "$HOOK"; then
    cp -n "$HOOK" "$APP/boot-custom.before-early-update.sh"
fi
mkdir -p "$DEST"
printf 'RETROGRZMOT EARLY BOOT v1\n' > "$DEST/retrogrzmot-managed"
cp "$APP/early/splash.py" "$DEST/splash.py"
cp "$FRAME" "$DEST/splash.bin"
# Install the hook last, after all dependencies are in place.
cp "$APP/early/boot-custom.sh" "$HOOK"
bash -n "$HOOK"
echo 'Early splash installed. Restart the device from the Batocera menu.'
