#!/usr/bin/python3

"""
This script skips texts that seem file path,
and optionally text whose lenght is greater than MAX_CHARS.
"""
# whether to skip file manager copy/cut operations on files/folders
# just a guess; set to 0 to disable this behaviour
SKIP_FILES = 1

# the text will be stored if its lenght is less than MAX_CHARS
# 0 means the text will be always stored
MAX_CHARS = 0

import sys,os,time

_curr_dir = os.getcwd()
clips_path = os.path.join(_curr_dir, "clips")

# for line in sys.stdin:
#     pass

_text = sys.stdin.read()

_not_path = 1
def _find_urls(_text):
    global _not_path
    _text_list = _text.split("\n")
    for el in _text_list:
        if not os.path.exists(el):
            _not_path = 0
            break

if SKIP_FILES:
    if MAX_CHARS > 0 and len(_text) < MAX_CHARS:
        _find_urls(_text)
    else:
        _find_urls(_text)
else:
    _not_path = 0

if MAX_CHARS:
    if len(_text) > MAX_CHARS:
        _not_path = 1

i = 0
if _not_path == 0 and _text:
    if not os.path.exists(os.path.join(_curr_dir,"donotdisturb.mode")):
        time_now = str(int(time.time()))
        while os.path.exists(os.path.join(clips_path, time_now)):
            time.sleep(0.1)
            time_now = str(int(time.time()))
            i += 1
            if i == 10:
                break
        try:
            with open(os.path.join(clips_path, time_now), "w") as ffile:
                ffile.write(_text)
        except:
            pass
