# wbar
Bar for wayland

Almost no more developed.

free to use and modify

Wbar is a panel to be used under wayland, if the display server support 
the layer-shell protocols. All the lroots based window managers should 
support wbar.

There is a Gtk3 and a Gtk4 version of wbar (in the past the gtk3 version freeze(d) completely for unknown reasons). The gtk3 version has less priority in developing. Requirements: gtk3-layer-shell or gtk4-layer-shell + python3 binding + other if the case (see below). Important: it seems that the lib libgtk4-layer-shell.so.1.0.4 must be preoladed before launching wbar.py (or just launch wbar.sh of the gtk4 version).

The command/env "dbus-update-activation-environment --systemd WAYLAND_DISPLAY DISPLAY XAUTHORITY" may improve the use of the gtk3/4 applications.

Features:
- application menu
- clock
- clipboard (with history)
- taskbar with scrolling support
- tray
- volume
- notifications (with history)
- a simple timer (gtk3 version)
- two command outputs
- a graphical configurator
- sticky notes
- a timer (gtk3 version)

Requirements:
- a wayland display server with layer-shell support
- python3
- gtk3/gtk4 python bindings
- PIL for the tray section (only for the gtk3 version)
- wl-clipboard for the clipboard (wl-paste and wl-copy are needed)
- pactl for volume applet (amixer is supported; read below for more)

The taskbar uses the framework wl_framework from Consolatis.

How to use:
- just unzip the archive and launch waybar.sh

Before using wbar:
- in the file logout.sh change the name WINDOWMANAGER with the name of the 
window manager you are using; the commands poweroff.sh and restart.sh already 
contain the right commands for most distros.

Options and configurations

Wbar has a graphical configurator for many options.

About the file wclipboard.py: the clipboard stores the text of any length, unless an option to skip very large text clip is changed in the file: MAX_CHARS from 0 (that means all characters) to some number, e.g. 1000 if you want to skip text larger than 1000 characters; SKIP_FILES = 1 : with this option the text that seams from copy/cut operations on files/folders are skipped, unlsess it is setted to 0.

The bash scripts volume_SOMENAME.sh use the command pactl for their 
actions. amixer can also be used: switch the commands in those files.

The menu updates automatically; middle mouse click on an item in any 
category, except bookmarks, to force a menu update.

Left mouse click on the volume bar level to mute the output;
right mouse click to open the mixer, if one has been choosen in the 
configurator.

The sticky notes: just open the service menu, usually at right, and choose
the notes tab; there user can choose to add a new note or to show/hide 
all of them. Click on Accept to store the note, click on Delete to 
remove and delete that note. The background colour of the notes can be changed 
in the panelstyle.css file. Initial implementation.

Wbar has two slots for the command out scripts, at left and in the center;
the scripts are located in the scripts folder; the labels in the panel accept the left 
mouse button action to launch a custom application: set its name in the 
files label1.script (left label) and/or label2.script (center label).
The scripts can be of two different types: single shot and continuous shots.
The single shot script has to be in the form output1.#s (output2.#s) or 
output1.#m (output2.#m). #s means the script will be executed every # seconds,
while #m means the scripts will be executed every # minutes.
The continuous shot scripts have to be in the form output1.sh and/or output2.sh:
the scripts have to be able to output something and to control the whole process.

Custom styles

In the foldef configs is the file panelstyle.css.

The file notifications_skipped is a simple file in which to write the 
name of the applications you may want not to be stored in the history list.

------------------------------

Known issue:
- the gtk3 version completely freeze randomly; it is now deprecated.

![My image](https://github.com/frank038/wbar/blob/main/wbar_01.jpg)

![My image](https://github.com/frank038/wbar/blob/main/wbar_02.jpg)

