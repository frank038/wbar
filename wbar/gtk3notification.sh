#!/bin/bash
thisdir=$(dirname "$0")
cd $thisdir
python3 gtk3notification.py &
