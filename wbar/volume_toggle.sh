#!/bin/sh
# amixer -D pulse set Master 1+ toggle
pactl set-sink-mute @DEFAULT_SINK@ toggle
