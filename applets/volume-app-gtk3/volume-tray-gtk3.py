#!/usr/bin/env python3
# V 0.1
MIXER = "pavucontrol-qt"

import os
import signal
import subprocess
import gi
from gi.repository import GLib
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, GObject
gi.require_version('AyatanaAppIndicator3', '0.1')
from gi.repository import AyatanaAppIndicator3 as appindicator
from threading import Thread
import asyncio
import pulsectl_asyncio
from gi.events import GLibEventLoopPolicy
import pulsectl as _pulse

class Indicator:
    
    def __init__(self):
        
        self.indicator = appindicator.Indicator.new(
            "customtray",
            "audio-volume-muted",
            appindicator.IndicatorCategory.APPLICATION_STATUS,
        )
        self.indicator.set_title("Volume")
        self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.menu())
        
        self.pulse = _pulse.Pulse()
        
        # default sink name
        self.default_sink_name = None
        # default sink
        self.default_sink = None
        
        # volume levels at start
        self._on_start_vol()
        self.set_async = 0
        _thread = Thread(target=self.volume_async_func)
        _thread.start()
    
    # at this program start
    def _on_start_vol(self):
        _sink_list = []
        try:
            _sink_list = self.pulse.sink_list()
        except:
            self._reload_pulse()
        # the default sink stored
        try:
            _server_info = self.pulse.server_info()
            self.default_sink_name = _server_info.default_sink_name
            del _server_info
        except:
            self._reload_pulse()
        ####
        _sink = None
        try:
            for el in self.pulse.sink_list():
                if el.name == self.default_sink_name:
                    _sink = el
                    break
        except:
            self._reload_pulse()
            return
        #
        if _sink:
            self.default_sink = _sink
            self.dev_label.set_label(_sink.description)
            self.set_volume(_sink)
    
    def set_volume(self, _sink):
        _volume = _sink.volume.values
        _level = int(round(max(_volume), 2)*100)
        _mute = _sink.mute
        if _level < 0 or not isinstance(_level, int):
            return
        if _mute == 0:
            if 0<=_level<30:
                self.indicator.set_icon_full("audio-volume-low",None)
            elif 30<=_level<65:
                self.indicator.set_icon_full("audio-volume-medium",None)
            elif 65<=_level<=100:
                self.indicator.set_icon_full("audio-volume-high",None)
            elif _level > 100:
                self.indicator.set_icon_full("audio-volume-overamplified",None)
            self.vol_label.set_label("Volume: "+str(_level)+"%")
        elif _mute == 1:
            self.indicator.set_icon_full("audio-volume-muted",None)
            self.vol_label.set_label("Volume: "+str(_level)+"% - Muted")
    
    def _reload_pulse(self):
        try:
            del self.pulse
            self.pulse = _pulse.Pulse()
        except:
            pass
    
    async def some_callback(self):
        async with pulsectl_asyncio.PulseAsync('event-audio') as pulse:
            async for event in pulse.subscribe_events('sink', 'server'):
                if self.set_async == 1:
                    return
                # server
                if event.facility == pulse.event_facilities[5]:
                    # server change
                    if event.t == _pulse.PulseEventTypeEnum.change:
                        _sink = None
                        try:
                            _server_info = self.pulse.server_info()
                            self.default_sink_name = _server_info.default_sink_name
                            _sink_list = self.pulse.sink_list()
                            for el in _sink_list:
                                if self.default_sink_name == el.name:
                                    _sink = el
                                    break
                            del _server_info
                        except:
                            self._reload_pulse()
                        if _sink:
                            self.dev_label.set_label(_sink.description)
                            self.set_volume(_sink)
                # sink
                elif event.facility == pulse.event_facilities[6]:
                    # volume change
                    if event.t == _pulse.PulseEventTypeEnum.change:
                        _sink = None
                        try:
                            _sink_list = self.pulse.sink_list()
                        except:
                            self._reload_pulse()
                            return
                        for el in _sink_list:
                            if el.name == self.default_sink_name:
                                _sink = el
                                break
                        if _sink:
                            self.set_volume(_sink)
    
    def volume_async_func(self):
        print("")
        asyncio.run(self.some_callback())
    
    def menu(self):
        menu = Gtk.Menu()
        
        self.vol_label = Gtk.MenuItem.new_with_label(label="0")
        menu.append(self.vol_label)
        
        self.dev_label = Gtk.MenuItem.new_with_label(label="-----------")
        menu.append(self.dev_label)
        
        _mixer = Gtk.MenuItem(label="Mixer")
        _mixer.connect('activate', self.open_mixer)
        menu.append(_mixer)
        
        menu.append(Gtk.SeparatorMenuItem())
        
        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect('activate', self.destroy_cb, 'quit')
        menu.append(quit_item)
        
        menu.show_all()
        return menu
    
    def open_mixer(self, w):
        try:
            subprocess.Popen([MIXER])
        except:
            pass
    
    def destroy_cb(self, widget, data=None):
        self.set_async = 1
        _vol = self.pulse.volume_get_all_chans(self.default_sink)
        if _vol < 0.9:
            self.pulse.volume_set_all_chans(self.default_sink, _vol+0.0001)
        else:
            self.pulse.volume_set_all_chans(self.default_sink, _vol-0.0001)
        Gtk.main_quit()


if __name__ == "__main__":
    indicator = Indicator()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    asyncio.set_event_loop_policy(GLibEventLoopPolicy())
    Gtk.main()
