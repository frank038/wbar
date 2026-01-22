# wbar
Panel/Bar for wayland

free to use and modify

Download the latest package from the release section.

Wbar is a panel to be used under wayland, if the display server support the layer-shell protocols. All the wlroots based window managers should support wbar.

There is a Gtk3 and a Gtk4 version of wbar.

Features:
- graphical configurator
- application menu
- clock
- clipboard (with history)
- volume widget (gtk4 version - deprecated)
- taskbar with scrolling support
- tray
- notifications (with history)
- calendar appointments
- two command outputs
- sticky notes
- a timer (gtk3 version)
- a menu editor (gtk3 version)
- languages (gtk3 version)
- three applets: audio (can also manage cards and microphones); volume; mpris.

Requirements:
- a wayland display server with layer-shell support
- python3
- gtk3 or gtk4 python bindings
- gtk-launch command line (gtk4 version)
- wl-clipboard for the clipboard (wl-paste and wl-copy are needed)
- pactl for volume applet (gtk4 version; amixer is supported; read below for more)
- pyqt6 for the internal menu editor and for the applets

How to use:
- just unzip the archive and launch waybar_launch.sh/waybar.sh

Options and configurations:
- Wbar has a graphical configurator for almost all options.


Custom styles:
In the folder configs is the file panelstyle.css, that can optionally enabled in the configuration dialog. 


The languages files:
just copy and translate in your language the content of the file EN.py, and rename the new file in LANGUAGE_CODE.py; then choose the LANGUAGE_CODE in the configurator.

The calendar appointments:
just double click a day to launch a dialog; the new events will be markded in the calendar and list in the appointment section.

The command/env "dbus-update-activation-environment --systemd WAYLAND_DISPLAY DISPLAY XAUTHORITY" may improve the use of the gtk3/4 applications.

The taskbar uses the framework wl_framework from Consolatis.


About the file wclipboard.py: the clipboard stores the text of any length, unless an option to skip very large text clip is changed in the file: MAX_CHARS from 0 (that means all characters) to some number, e.g. 1000 if you want to skip text larger than 1000 characters; SKIP_FILES = 1 : with this option the text that seams from copy/cut operations on files/folders are skipped, unlsess it is setted to 0.

The bash scripts volume_SOMENAME.sh use the command pactl for their actions. amixer can also be used: switch the commands in those files.

The menu updates automatically; middle mouse click on an item in any category, except bookmarks, to force a menu update.


The sticky notes: just open the service menu, usually at right, and choose the notes tab; there user can choose to add a new note or to show/hide all of them. Click on Accept to store the note, click on Delete to remove and delete that note. The background colour of the notes can be changed in the panelstyle.css file. Initial implementation.

Wbar has two slots for the command out scripts, at left and in the center; the scripts are located in the scripts folder; the labels in the panel accept the left mouse button action to launch a custom application: set its name in the files label1.script (left label) and/or label2.script (center label).
The scripts can be of two different types: single shot and continuous shots.
The single shot script has to be in the form output1.#s (output2.#s) or output1.#m (output2.#m). #s means the script will be executed every # seconds, while #m means the scripts will be executed every # minutes.
The continuous shot scripts have to be in the form output1.sh and/or output2.sh: the scripts have to be able to output something and to control the whole process.



------------------------------

Known issue:

- the gtk4 version: it seems that in some cases the lib libgtk4-layer-shell.so.1.0.4 must be preoladed before launching wbar.py (or just launch wbar.sh of the gtk4 version)

- the gtk4 version: the volume widget may freeze the application randomly (when it happens, it must be executed again; maybe disabling the internal widget and using the external applet may solde the issue).

![My image](https://github.com/frank038/wbar/blob/main/wbar_01.jpg)

![My image](https://github.com/frank038/wbar/blob/main/wbar_02.jpg)

