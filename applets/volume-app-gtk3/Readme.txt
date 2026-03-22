volume-tray-gtk3.py

This program is a simple tray application for volume.
It tracks the volume change and the card change.

Usage:
right mouse click on the tray icon to get the current audio level 
and the current audio card. Press mixer to launch pavucontrol (read
below) and Quit to exit this program.

Requirements:
python3
gtk3
gir1.2-ayatanaappindicator3-0.1
pulsectl_asyncio (included)
a mixer (optional)

Options:
The mixer command is pavucontrol by default.
That command can be changed at line 3 of the file volume-tray-gtk3.py .
