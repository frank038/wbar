#!/bin/bash

thisdir=$(dirname "$0")
cd $thisdir
# python3 wbar.py &
LD_PRELOAD=./libgtk4-layer-shell.so.1.0.4 python3 wbar.py
