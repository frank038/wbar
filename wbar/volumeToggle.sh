#!/bin/bash

wpctl set-mute @DEFAULT_SINK@ toggle > /dev/null 2>&1 &
# pactl set-sink-mute @DEFAULT_SINK@ toggle > /dev/null 2>&1 &
