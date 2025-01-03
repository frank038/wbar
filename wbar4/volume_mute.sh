#!/bin/bash

# output: 0=mute enabled or 1=mute disabled

#_mute=`amixer sget Master|grep 'Front Left:'| awk -F ' ' '{print $6}'`
#if [ $_mute == "[on]" ]; then
#echo 0
#elif [ $_mute == "[off]" ]; then
#echo 1
#fi


_state=`pactl get-sink-mute @DEFAULT_SINK@ | awk -F ' ' '{print $2}'`
if [ $_state == "no" ]; then
echo 0
elif [ $_state == "yes" ]; then
echo 1
fi
