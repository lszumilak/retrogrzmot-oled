# Install Batocera on Raspberry Pi 3B+

Skip this guide if your Pi already starts Batocera. Flashing an image erases the destination card, including existing games, saves and settings.

## 1. Prepare the parts

You need a Raspberry Pi 3B+, its power supply, a microSD card, a card reader for your computer, an HDMI display and a controller. Batocera's installation guide recommends a card of at least 32 GB for full functionality. Back up anything you need from the card before proceeding.

## 2. Download the correct image

1. Open the official [Batocera downloads page](https://batocera.org/download).
2. Find the build for **Raspberry Pi 3 / 3B+**, not a Raspberry Pi 4/5 or a PC image. Check the supported devices listed for the download.
3. This OLED project was tested on **Batocera 42**. Newer versions need the verification checklist in [Troubleshooting](troubleshooting.md#after-a-batocera-update). If using an older release, obtain it from Batocera's official release/archive links.
4. Save the `.img.gz` file to your computer. Do not obtain a preloaded image of unknown origin for this guide.

The development Pi identifies its platform as `bcm2837`. That is a hardware target, not a Batocera version number.

## 3. Write the image to the card

1. Install [Raspberry Pi Imager](https://www.raspberrypi.com/software/) from the official site.
2. Insert your microSD card into the computer's reader.
3. In Imager, choose the downloaded image using **Use custom** under the OS selection. Button labels can differ between Imager versions.
4. Choose the microSD card as the destination. Check its capacity and identity carefully; writing to the wrong drive erases that drive.
5. Write the image and let verification finish. Use the downloaded Batocera image without applying Raspberry Pi OS-specific account/Wi-Fi customizations unless Batocera's current instructions explicitly support them.
6. If Windows offers to format another partition afterwards, click **Cancel**. Windows may not understand Batocera's Linux data partition.
7. Safely eject the card.

## 4. First startup

1. With the Pi unplugged, insert the card.
2. Connect HDMI, a controller and optionally an Ethernet cable.
3. Connect power. Give the first startup time to expand the data partition; it may restart itself. Do not interrupt that operation.
4. Once the menu appears, set the language, configure the controller if asked, and configure Wi-Fi if not using Ethernet.
5. Open network settings and note the Pi's address for the [OLED installation guide](installation.md).

The OLED can stay black until its software is installed. It is a separate screen from the HDMI display.

## 5. Games, BIOS and safe shutdown

Follow Batocera's [games and BIOS guide](https://wiki.batocera.org/add_games_bios) for folder locations and emulator requirements. Supply only games and BIOS files that you are entitled to use. This repository distributes neither.

Use Batocera's menu to shut the Pi down before disconnecting power or removing the card.

This is a focused companion guide. The official [Batocera installation instructions](https://wiki.batocera.org/install_batocera) remain the source for current image-writing and first-boot behavior.
