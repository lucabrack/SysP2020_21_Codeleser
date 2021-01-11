# Raspberry Pi
Files für den Raspi Teil des Projekts. Benötigte Hardware:
* Raspberry Pi (Zero W und 3B+ wurden getestet)
* Raspberry Pi Camera (V2.1 getestet)

Python Libraries:
* OpenCV (4.4.0)

## Installation (nur bei neu aufgesetztem Raspi nötig)
Klone das Repository in den /home/pi/Projekte Ordner:
```bash
mkdir Projekte
cd Projekte
sudo git clone https://github.com/lucabrack/SysP2020_21_Codeleser.git
```
(Optional) Erstelle die Desktopverknüpfungen:
```bash
sudo bash ./SysP2020_21_Codeleser/raspi/bash/create-shortcuts
```

## Programm auf den neusten Stand bringen
Wenn ein neuer Stand des Programms sich auf GitHub befindet, kann der Code wie folgt auf den neusten Stand gebracht werden:
```bash
sudo bash ~/Projekte/SysP2020_21_Codeleser/raspi/bash/update-code
```
Alternativ kann auch der Link auf dem Desktop verwendet werden.
