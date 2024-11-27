#!/bin/sh
# amixer set Master 5%-
pactl set-sink-volume @DEFAULT_SINK@ -5%
