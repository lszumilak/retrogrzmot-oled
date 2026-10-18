#!/bin/bash
set -eu
APP=/userdata/system/retrogrzmot
SERVICE=/userdata/system/services/retrogrzmot_oled
OLD_SERVICE=/userdata/system/services/retrogrzmot-oled
HOOKS=/userdata/system/configs/emulationstation/scripts
test -f "$APP/oled.py"
test -f "$APP/retrogrzmot-oled"
test -f "$APP/fonts/DejaVuSans.ttf"
test -c /dev/i2c-1
python3 -c 'import fcntl; from PIL import Image, ImageDraw, ImageFont'
python3 -m py_compile "$APP/oled.py"
command -v batocera-services > /dev/null
mkdir -p /userdata/system/services
if test -e "$OLD_SERVICE"; then
    if ! grep -q '/userdata/system/retrogrzmot/oled.py' "$OLD_SERVICE"; then
        echo 'A different retrogrzmot-oled service exists. Stopping without overwriting it.' >&2
        exit 1
    fi
    bash "$OLD_SERVICE" stop
    # Keep backups outside services: Batocera enumerates every file there.
    mv "$OLD_SERVICE" "$APP/service-before-name-fix"
fi
if test -e "$SERVICE"; then
    if ! grep -q '/userdata/system/retrogrzmot/oled.py' "$SERVICE"; then
        echo 'A different retrogrzmot_oled service exists. Stopping without overwriting it.' >&2
        exit 1
    fi
    bash "$SERVICE" stop
    cp -n "$SERVICE" "$APP/service-before-update"
fi
cp "$APP/retrogrzmot-oled" "$SERVICE"
chmod +x "$SERVICE"
for event in system-selected game-selected game-start game-end quit shutdown reboot; do
    mkdir -p "$HOOKS/$event"
    target="$HOOKS/$event/retrogrzmot-oled.sh"
    if test -e "$target"; then
        if ! grep -q '/userdata/system/retrogrzmot/oled.py' "$target"; then
            echo "A different script exists at $target. Stopping without overwriting it." >&2
            exit 1
        fi
        cp -n "$target" "$APP/$event.before-update"
    fi
    cat > "$target" <<EOF
#!/bin/bash
# RETROGRZMOT OLED v0.5
python3 /userdata/system/retrogrzmot/oled.py event "$event" "\$@" || true
EOF
    chmod +x "$target"
done
batocera-services enable retrogrzmot_oled
# Batocera can print an error but return success: verify the saved setting.
case " $(batocera-settings-get system.services) " in
    *" retrogrzmot_oled "*) ;;
    *) echo 'OLED automatic startup was not saved. Installation stopped.' >&2; exit 1 ;;
esac
bash "$SERVICE" start
echo 'RETROGRZMOT OLED is ready. Optional early splash: run install-early.sh separately.'
