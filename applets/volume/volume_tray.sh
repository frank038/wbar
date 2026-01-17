#!/bin/bash

thisdir=$(dirname "$0")
cd $thisdir

python3 volume_tray.py

cd $HOME
