#!/bin/bash

# amixer -D pipewire sset Master 4%+ > /dev/null 2>&1 &
wpctl set-volume @DEFAULT_SINK@ .04+ > /dev/null 2>&1 &
# pactl -- set-sink-volume @DEFAULT_SINK@ +4% > /dev/null 2>&1 &
