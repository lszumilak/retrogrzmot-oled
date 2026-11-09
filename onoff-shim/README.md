# RETROGRZMOT — OnOff SHIM krok po kroku

[English instructions](#english-step-by-step)

Pimoroni OnOff SHIM pozwala włączać i wyłączać konsolę przyciskiem na obudowie. Po naciśnięciu Batocera kończy pracę, a moduł odcina zasilanie Raspberry Pi.

**Sprawdzony zestaw:** Raspberry Pi 3 Model B+, Batocera 43.1, Pimoroni OnOff SHIM (PIM269), FAN Adapter V2, przycisk chwilowy i zasilacz microUSB. Zacznij od działającej instalacji Batocery. Dla tego układu wystarczą ustawienia w dwóch plikach.

## 1. Podłącz moduł i przycisk

Zamknij Batocerę z menu i odłącz zasilacze. Sprawdź oznaczenia złączy. **GPIO4** to nazwa sygnału (BCM), a **pin 7** to jego fizyczne miejsce w złączu. Dobieraj przewody według oznaczeń, nie według kolorów.

| Sygnał | Pin fizyczny na SHIM-ie | FAN Adapter V2 |
| --- | --- | --- |
| 5 V | 2 | pin 2 |
| GND | 6 | pin 20 |
| BCM GPIO4 | 7 | D4, pin 7 |
| BCM GPIO17 | 11 | D17, pin 11 |

Podłącz po jednym przewodzie przycisku do każdego z dwóch pól **BTN** na SHIM-ie. Podłącz zasilacz do gniazda microUSB **SHIM-a**. Gniazdo microUSB Raspberry Pi zostaw puste. Włącz konsolę przyciskiem, jeśli nie uruchomi się po podłączeniu zasilacza.

## 2. Połącz się z Batocerą z Windows

1. Podłącz komputer i konsolę do tej samej sieci lokalnej. W menu Batocery otwórz **Ustawienia sieci** i odczytaj adres IP.
2. W Windows otwórz **PowerShell**. Wpisz poniższe polecenie, zastępując `PI_IP` adresem swojej konsoli. Skopiuj tylko polecenie z ramki.

```powershell
ssh root@PI_IP
```

3. Przy pierwszym połączeniu potwierdź, że adres należy do Twojej konsoli. Podaj hasło Batocery. Podczas wpisywania hasła terminal nie pokazuje znaków. Gdy zobaczysz wiersz zaczynający się od `[root@BATOCERA`, kolejne polecenia będą wykonywane na konsoli. W razie kłopotów z połączeniem zobacz [instrukcję SSH Batocery](https://wiki.batocera.org/access_the_batocera_via_ssh).

## 3. Zrób kopie plików

**Na konsoli przez SSH.** Uruchamiaj polecenia po kolei. Jeśli któreś zwróci błąd, przerwij przed edycją plików. Pierwsze polecenie umożliwia zapis w katalogu `/boot`. Opcja `-n` chroni wcześniejsze kopie przed nadpisaniem.

```sh
mount -o remount,rw /boot
cp -n /userdata/system/batocera.conf /userdata/system/batocera.conf.before-onoffshim
cp -n /boot/config.txt /boot/config.txt.before-onoffshim
ls -l /userdata/system/batocera.conf.before-onoffshim /boot/config.txt.before-onoffshim
```

Po ostatnim poleceniu powinny pojawić się oba pliki z końcówką `.before-onoffshim`. Jeśli kopie zostały zrobione przy wcześniejszej próbie, sprawdź ich zawartość przed dalszą edycją.

## 4. Wpisz ustawienia

**Na konsoli przez SSH** otwórz pierwszy plik w edytorze tekstu:

```sh
nano /userdata/system/batocera.conf
```

Jeżeli istnieje aktywna linia zaczynająca się od `system.power.switch=`, zmień jej wartość. Jeżeli takiej linii nie ma, dopisz poniższą na końcu pliku.

```ini
system.power.switch=ONOFFSHIM
```

Zapisz przez **Ctrl+O**, potwierdź nazwę pliku klawiszem **Enter** i wyjdź przez **Ctrl+X**. Otwórz drugi plik:

```sh
nano /boot/config.txt
```

Dodaj poniższe dwie linie w części wspólnej konfiguracji. Jeśli plik używa sekcji w nawiasach kwadratowych, umieść wpisy pod `[all]`. Jeśli plik ma sekcje, ale brakuje `[all]`, dopisz taki nagłówek na końcu, tuż przed nowymi liniami. Jeśli widzisz już ustawienie dla GPIO17, konfigurację `gpio-poweroff` lub inne przypisanie GPIO4, sprawdź je przed zapisaniem, żeby uniknąć konfliktu.

```ini
gpio=17=ip,pu
dtoverlay=gpio-poweroff,gpiopin=4,active_low=1,input=1
```

Zapisz i wyjdź tak samo jak z poprzedniego pliku. Sprawdź zapisane linie:

```sh
grep -n '^system.power.switch=' /userdata/system/batocera.conf
grep -n -e '^gpio=17=ip,pu$' -e '^dtoverlay=gpio-poweroff,gpiopin=4,active_low=1,input=1$' /boot/config.txt
```

Pierwsze polecenie powinno pokazać jedną linię z `ONOFFSHIM`, a drugie obie linie konfiguracji startowej. Gdy wynik się zgadza, zapisz dane na kartę i uruchom konsolę ponownie:

```sh
sync
reboot
```

Połączenie SSH się zamknie. Poczekaj na powrót menu Batocery.

## 5. Sprawdź przycisk

1. W menu głównym Batocery naciśnij krótko przycisk obudowy. Poczekaj na zamknięcie systemu. Gdy SHIM odetnie zasilanie, czerwona dioda zasilania Raspberry Pi zgaśnie.
2. Naciśnij przycisk ponownie. Powinno wrócić menu Batocery.
3. Jeśli przycisk nie zamyka systemu, sprawdź ustawienie `ONOFFSHIM` i połączenie D17. Jeśli system się zamyka, ale czerwona dioda pozostaje zapalona, sprawdź linię `gpio-poweroff`, połączenie D4 i miejsce wpięcia zasilacza. Przed przepinaniem przewodów zamknij system i odłącz zasilacze.

### Jak przywrócić poprzednie ustawienia

Jeżeli konsola się uruchamia i masz dostęp przez SSH, przywróć kopie utworzone w kroku 3. Te polecenia zastąpią obecną zawartość obu plików zapisanymi kopiami.

```sh
mount -o remount,rw /boot
cp /boot/config.txt.before-onoffshim /boot/config.txt
cp /userdata/system/batocera.conf.before-onoffshim /userdata/system/batocera.conf
sync
reboot
```

Jeżeli po edycji `config.txt` Batocera nie startuje, włóż kartę microSD do komputera. Na partycji rozruchowej znajdź `config.txt.before-onoffshim` i skopiuj go pod nazwą `config.txt`. [Instrukcja dostępu do partycji rozruchowej](https://wiki.batocera.org/edit_boot_partition)

## English step by step

**Tested setup:** Raspberry Pi 3 Model B+, Batocera 43.1, Pimoroni OnOff SHIM (PIM269), FAN Adapter V2, a momentary push button and a micro-USB power supply. Start with a working Batocera installation.

1. **Wire the hardware.** Shut down Batocera and disconnect power. Follow the pin table in step 1. BCM numbers identify signals, while physical pin numbers identify positions on the connector. Connect one button wire to each BTN pad. Plug the power supply into the SHIM's micro-USB port and leave the Pi's micro-USB port empty. Press the case button if the console does not start on its own.
2. **Connect from Windows.** Put Windows and Batocera on the same local network. Find the Pi's IP address in Batocera's **Network Settings**. Open PowerShell and run the command in step 2 with your console's IP in place of `PI_IP`. Confirm the address on the first connection and enter the Batocera password. The terminal hides password characters as you type. A prompt beginning with `[root@BATOCERA` means the next commands run on the Pi.
3. **Back up both files.** In the SSH window, run the commands in step 3 one at a time. If any command reports an error, stop before editing. The final command should list both `.before-onoffshim` files. If the copies already existed, check their contents before proceeding.
4. **Edit the settings.** Open both files using the `nano` commands in step 4. In `batocera.conf`, replace the value of the existing `system.power.switch=` line or add the line if it is missing. In `/boot/config.txt`, add the two lines to the shared configuration, under `[all]` if the file uses sections. If there are sections but no `[all]`, add that heading at the end before the two lines. Check for existing assignments for GPIO17, GPIO4 or `gpio-poweroff` before saving. In Nano, press **Ctrl+O**, **Enter**, then **Ctrl+X** to save and exit. Run the two `grep` checks in step 4. They should print the single `ONOFFSHIM` setting and both boot settings. Then run `sync` and `reboot`. The SSH session will disconnect.
5. **Test.** From Batocera's main menu, press the case button. Wait for the Pi's red power LED to turn off. Press the button again and wait for the menu to return. If shutdown does not start, check the `ONOFFSHIM` setting and D17. If shutdown completes but power stays on, check `gpio-poweroff`, D4 and the power supply connection. Shut down and disconnect power before moving any wires.
6. **Restore if needed.** If you can still connect through SSH, use the backup restore commands above. If Batocera cannot boot after editing `config.txt`, use a computer to copy `config.txt.before-onoffshim` to `config.txt` on the card's boot partition.

## Dokumentacja / References

- [Batocera — Raspberry Pi power switches](https://wiki.batocera.org/add_powerdevices_rpi_only)
- [Batocera — Editing the boot partition](https://wiki.batocera.org/edit_boot_partition)
- [Raspberry Pi — Overlay and parameter reference](https://github.com/raspberrypi/firmware/blob/master/boot/overlays/README)
