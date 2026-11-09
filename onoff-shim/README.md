# RETROGRZMOT — Pimoroni OnOff SHIM w Batocerze

Sprawdzone na Raspberry Pi 3B+ z Batocerą 43.1, modułem Pimoroni OnOff SHIM (PIM269) i adapterem FAN Adapter V2.

## Konfiguracja

W `/userdata/system/batocera.conf` ustaw:

```ini
system.power.switch=ONOFFSHIM
```

W `/boot/config.txt` dodaj:

```ini
gpio=17=ip,pu
dtoverlay=gpio-poweroff,gpiopin=4,active_low=1,input=1
```

## Połączenia w RETROGRZMOCIE

| Sygnał | Pin fizyczny na SHIM-ie | FAN Adapter V2 |
| --- | --- | --- |
| 5 V | 2 | pin 2 |
| GND | 6 | pin 20 |
| BCM GPIO4 | 7 | D4, pin 7 |
| BCM GPIO17 | 11 | D17, pin 11 |

Przycisk obudowy podłączono do obu pól BTN. Zasilacz konsoli podłączono do gniazda microUSB SHIM-a. Gniazdo microUSB Raspberry Pi pozostaje puste.

Przycisk zamyka Batocerę, a SHIM odcina zasilanie Raspberry Pi. Kolejne naciśnięcie uruchamia konsolę. Po prawidłowym wyłączeniu, odłączeniu zasilacza na minutę i ponownym podłączeniu konsola czekała na naciśnięcie przycisku.

## English

Tested on a Raspberry Pi 3B+ running Batocera 43.1 with a Pimoroni OnOff SHIM (PIM269) and FAN Adapter V2. Apply the settings to the two files listed above. The table shows the physical pin numbers and the adapter labels. Wire the case button across the two BTN pads. Plug the console's power supply into the SHIM's micro-USB port and leave the Pi's micro-USB port empty.

The button shuts down Batocera, then the SHIM cuts power to the Pi. Press the button again to boot. After a clean shutdown and a one-minute power disconnect, the console waited for a button press when power was restored.

## Dokumentacja / References

- [Batocera — Add power devices](https://wiki.batocera.org/add_powerdevices_rpi_only)
- [Raspberry Pi — Overlay and parameter reference](https://github.com/raspberrypi/firmware/blob/master/boot/overlays/README)
