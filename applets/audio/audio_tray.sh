#!/bin/bash

thisdir=$(dirname "$0")
cd $thisdir

python3 audio_tray.py

cd $HOME
