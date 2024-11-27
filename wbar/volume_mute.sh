#!/bin/bash

# output: on or off

# _mute=`amixer sget Master|grep 'Front Left:'| awk -F ' ' '{print $6}'`
# _lenght=${#_mute}
# if [ $_lenght -eq 4 ];then
# echo -n "${_mute:1:2}"
# else
# echo -n "${_mute:1:3}"
# fi


_state=`pactl get-sink-mute @DEFAULT_SINK@ | awk -F ' ' '{print $2}'`
if [ $_state = "no" ]; then
echo -n "on"
elif [ $_state = "yes" ]; then
echo -n "off"
fi
