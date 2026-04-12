# the exactly same name of the main directory of this module
_MODULE="test2"
# 0 left - 1 center - 2 right - 99 internal procedure
_POSITION=2
# module data
_NAME="second test"
_VERSION="Version 1.0"
_COMMENT="Just an addon"
_DATA="Sample addon"

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
from gi.repository import Gtk, GLib, Gdk, Gio
import os

class customWidget(Gtk.Box):
    def __init__(self, _parent):
        super().__init__()
        self._parent = _parent
        self._module = _MODULE
        self._position = _POSITION
        self._name = _NAME
        self._version = _VERSION
        self._comment = _COMMENT
        self._data = _DATA
        # HORIZONTAL or VERTICAL
        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self._label = Gtk.Label(label="Hi right")
        self.append(self._label)
        #### with _POSITION=99
        if _POSITION == 99:
            self.set_parent(self._parent.left_box)
            # self._parent.left_box.append
            # self._parent.center_box.append
            # self._parent.right_box.prepend
            self._parent.right_box.prepend(self)
        ####
        
        