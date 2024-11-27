wbar v. 0.5

free to use and modify

Wbar is a panel to be used under wayland, if the display server support 
the layer-shell protocols. All the lroots based window managers should 
support wbar.

Features:
- application menu (at left)
- clock
- clipboard (with history)
- tray
- volume
- notifications (with history)
- a simple timer
- command outputs
- a graphical configurator (at right)

Requirements:
- a wayland display server with layer-shell support
- python3
- gtk3 python bindings
- PIL for the tray section
- wl-clipboard for the clipboard (wl-paste and wl-copy are needed)
- pactl for volume applet (amixer is supported; read below for more)

How to use:
- just unzip the archive and launch waybar.sh

Before using wbar:
- in the file logout.sh change the name WINDOWMANAGER with the name of the 
window manager you are using; the commands poweroff.sh and restart.sh already 
contain the right commands for most distros.

Options and configurations

Wbar has a graphical configurator for many options. Other options have 
to be changed manually.

The bash scripts volume_SOMENAME.sh use the command pactl for their 
actions. amixer can also be used: switch the commands in those files.

Wbar has two slots for the command out scripts, at left and in the center;
the scripts are located in the scripts folder; the labels in the panel accept the left 
mouse button action to launch a custom application: set its name in the 
files label1.script (left label) and/or label2.script (center label).
The scripts can be of two different type: single shot and continuous shots.
The single shot script has to be in the form output1.#s (output2.#s) or 
output1.#m (output2.#m). #s means the script will be executed every # second,
while #m means the scripts will be executed every # minutes.
The continuous shot scripts have to be in the form output1.sh and/or output2.sh:
the scripts have to be able to output something and to control the whole process.

Custom styles

In the foldef configs is the file panelstyle.css.

The file notifications_skipped is a simple file in which to write the 
name of the applications you may want not to be stored in the history list.


