#!/bin/sh

# amixer set Master $1%
pactl set-sink-volume @DEFAULT_SINK@ $1%
