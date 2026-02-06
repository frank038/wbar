#!/usr/bin/env python3

# V. 0.9.1

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QLabel, QWidget, QApplication, QBoxLayout, QPushButton, QSlider, QRadioButton, QCheckBox
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QSizePolicy, QScrollArea
from PyQt6.QtGui import QIcon, QCursor, QPixmap, QWheelEvent 
from PyQt6.QtCore import Qt, QSize, QPoint, pyqtSignal, pyqtSlot, QThread, QEvent, QTimer

import sys, os
from subprocess import Popen

from cfg_volume import *


curr_path = os.getcwd()

menu_is_shown = 0

_TRAY = None

class myMenu(QMenu):
    def __init__(self):
        super(myMenu, self).__init__()
        self.setWindowTitle("qtaudio1")
        self.pixel_ratio = self.devicePixelRatio()
        # 1
        self.scroll = QScrollArea()
        self._widget = QWidget()
        self.scroll_box = QHBoxLayout()
        self._widget.setLayout(self.scroll_box)
        #
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self._widget)
        #
        self.scroll_box.setContentsMargins(0,0,0,0)
        self.scroll_box.setSpacing(0)
        #
        layout = QBoxLayout(QBoxLayout.Direction.TopToBottom)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        self.setLayout(layout)
        #
        layout.addWidget(self.scroll)
        #
        _audio = winAudio(self)
        #
        self.scroll_box.insertWidget(0, _audio)
        #########
        btn = QPushButton("Exit")
        layout.addWidget(btn)
        btn.clicked.connect(self._exit)
    
    def _exit(self):
        sys.exit(0)
    
    def sizeHint(self):
        return QSize(int(WIN_WIDTH/self.pixel_ratio),int(WIN_HEIGHT/self.pixel_ratio))

    def hideEvent(self, event):
        global menu_is_shown
        menu_is_shown = 0
        super(myMenu, self).hideEvent(event)


class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self):
        super(SystemTrayIcon, self).__init__()
        if not self.isSystemTrayAvailable():
            print("tray not available, exiting...")
            QMessageBox.critical(None, "Systray",
                "I couldn't detect any system tray on this system.")
            sys.exit(1)
        # 
        self._icon = QIcon()
        _icon1 = os.path.join(curr_path,"icons","audio-volume-muted.svg")
        self._icon.addFile(_icon1)
        self.setIcon(self._icon)
        #
        self.setToolTip("Audio manager")
        self.activated.connect(self._activateMenu)
        #
        self.setVisible(True)
        #
        global _TRAY
        _TRAY = self
        #
        ##########
        self._myMenu = myMenu()
        self.setContextMenu(self._myMenu)
        
    def eventFilter(self, obj, event):
        return super().eventFilter(obj, event)
    
    def _activateMenu(self, reason):
        global menu_is_shown
        # QSystemTrayIcon::MiddleClick
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if menu_is_shown == 0:
                # self._myMenu.exec(QCursor.pos())
                self._myMenu.show()
                menu_is_shown = 1
            else:
                menu_is_shown = 0
                self._myMenu.hide()
        
       
# audio
class winAudio(QWidget):
    def __init__(self, parent=None):
        super(winAudio, self).__init__(parent)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint|Qt.WindowType.FramelessWindowHint|Qt.WindowType.Popup)
        self.window = parent
        self.pixel_ratio = self.devicePixelRatio()
        #
        self.audiobox = QVBoxLayout()
        self.audiobox.setContentsMargins(2,2,2,2)
        self.setLayout(self.audiobox)
        #
        self.hbox1 = QHBoxLayout()
        self.hbox1.setContentsMargins(0,0,0,0)
        self.audiobox.addLayout(self.hbox1)
        #
        self.btn_audio = QPushButton()
        self.btn_audio.setObjectName("btnbackground")
        # self.btn_audio.setStyleSheet("background: "+self._background_color+";")
        self.btn_audio.setFlat(True)
        #
        self.btn_audio.setIconSize(QSize(int(button_size/self.pixel_ratio), int(button_size/self.pixel_ratio)))
        _icon = "audio-volume-muted"
        iicon = QIcon.fromTheme(_icon, QIcon("icons/audio-volume-muted.svg"))
        self.btn_audio.setIcon(iicon)
        self.btn_audio.setToolTip("No audio devices")
        self.hbox1.insertWidget(0, self.btn_audio)
        #
        self.btn_audio.winid = -999
        self.btn_audio.value = [-999, -999]
        self.btn_audio.clicked.connect(self._mute_audio)
        #
        self.mslider = QSlider(Qt.Orientation.Horizontal)
        self.mslider.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.mslider.setFocus()
        self.mslider.setTickPosition(QSlider.TickPosition.TicksBothSides)
        self.mslider.setMinimum(0)
        self.mslider.setMaximum(100)
        self.mslider.setTickInterval(10)
        self.mslider.setSingleStep(AUDIO_STEP)
        self.mslider.setPageStep(AUDIO_STEP)
        # self.mslider.valueChanged.connect(self.on_vslider_changed)
        self.mslider.is_pressed = 0
        self.mslider.sliderPressed.connect(self.on_vslider_pressed)
        self.mslider.sliderReleased.connect(self.on_vslider_released)
        self.mslider.installEventFilter(self)
        self.hbox1.addWidget(self.mslider)
        self.mbtn = QPushButton("Volume control")
        self.mbtn.clicked.connect(self.on_mbtn_mixer)
        self.audiobox.addWidget(self.mbtn)
        # sources
        self.card_lbl = QLabel("None")
        self.card_lbl.setContentsMargins(0,0,0,0)
        self.audiobox.addWidget(self.card_lbl)
        # the stored sink in the file
        self.start_sink_name = None
        #
        import pulsectl as _pulse
        self.pulse = _pulse.Pulse()
        #
        # default sink name
        self.default_sink_name = None
        #
        self.icon_rect = 0.75
        self._on_start_vol()
        self.on_populate_amenu()
        #
        self.athread = audioThread(_pulse)
        self.athread.sig.connect(self.athreadslot)
        self.athread.start()
    
    def eventFilter(self, obj, event):
        if obj == self.mslider:
            if isinstance(event, QWheelEvent):
                self.on_volume_change("slider")
        return super().eventFilter(obj, event)
    
    def on_vslider_pressed(self):
        self.mslider.is_pressed = 1
    
    def on_vslider_released(self):
        self.mslider.is_pressed = 0
        self.on_volume_change("slider")
    
    # def on_vslider_changed(self):
        # if self.mslider.is_pressed == 1:
            # self.on_volume_change("slider")
    
    # rebuild the volume menu - sink
    def on_populate_amenu(self):
        _sink_list = []
        try:
            _sink_list = self.pulse.sink_list()
        except:
            self._reload_pulse()
            return
        #
        _sink_list_names = []
        for ell in _sink_list:
            _sink_list_names.append(ell.name)
        #
        _sink_list_listed = []
        _sink_list_widget = []
        #
        _descr = "None"
        _vol = 0
        try:
            _server_info = self.pulse.server_info()
            self.default_sink_name = _server_info.default_sink_name
            for ell in _sink_list:
                if self.default_sink_name == ell.name:
                    _descr = ell.description
                    self.card_lbl.setText(_descr or "None")
                    self._set_volume("vol_change")
                    break
            del _server_info
        except:
            self._reload_pulse()
        #
        del _sink_list_names
    
    # at this program start
    def _on_start_vol(self):
        # # card list
        # self.card_list = self.pulse.card_list()
        # # default sink name
        self.default_sink_name = None
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
        #
        _sink_name = self.default_sink_name
        #
        if self.start_sink_name:
            if self.start_sink_name != "auto_null":
                self.default_sink_name = self.start_sink_name
        #
        for el in _sink_list:
            if el.name == _sink_name and el.name != "auto_null":
                self.pulse.sink_default_set(el)
                break
        #
        # set the icon and tooltip - volume
        self._set_volume("start")
    
    # event.angleDelta() : negative down - positive up
    def on_volume_change(self, _direction):
        dsink = None
        try:
            _sink_list = self.pulse.sink_list()
        except:
            self._reload_pulse()
            return
        for el in _sink_list:
            if el.name == self.default_sink_name:
                dsink = el
                break
        if dsink == None:
            return
        #
        _vol = None
        if _direction == "slider":
            if dsink:
                _vol = round(((self.mslider.value()//AUDIO_STEP)*AUDIO_STEP)/100, 2)
        else:
            # volume : 0.0 - 1.0
            if _direction.y() < 0:
                if dsink:
                    try:
                        _vol = round(self.pulse.volume_get_all_chans(dsink),2) - (AUDIO_STEP/100)
                    except:
                        self._reload_pulse()
                        return
                    if _vol < 0:
                        _vol = 0
            # volume +
            elif _direction.y() > 0:
                if dsink:
                    try:
                        _vol = round(self.pulse.volume_get_all_chans(dsink),2) + (AUDIO_STEP/100)
                    except:
                        self._reload_pulse()
                        return
                    if _vol > 1:
                        _vol = 1.0
        #
        if _vol:
            try:
                self.pulse.volume_set_all_chans(dsink, _vol)
                self._set_volume()
            except:
                self._reload_pulse()
    
    def _mute_audio(self):
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
        if not _sink:
            return
        _mute_state = not _sink.mute
        try:
            self.pulse.mute(_sink, mute=_mute_state)
        except:
            self._reload_pulse()
        self._set_volume("vol_change")
    
    def _reload_pulse(self):
        try:
            del self.pulse
            self.pulse = _pulse.Pulse()
        except:
            pass
    
    def athreadslot(self, _list):
        if _list[0] == "remove-sink":
            self.on_list_audio(_list[1], 101)
        elif _list[0] == "new-sink":
            self.on_list_audio(_list[1], 102)
        elif _list[0] == "change-sink":
            self.on_list_audio(_list[1], 103)
        elif _list[0] == "server-changed":
            self.on_list_audio(_list[1], 300)
    
    def on_list_audio(self, _el, _t):
        # sink: remove - new
        if _t in [101,102]:
            # self.on_populate_amenu()
            self._set_volume(102)
        # volume changed
        elif _t == 103:
            self._set_volume("vol_change")
        # server changed
        elif _t == 300:
            self.on_populate_amenu()
    
    #
    def _set_volume(self, _type=None):
        #### 
        _default_sink_name = None
        if _type == 102:
            # the default sink stored
            try:
                _server_info = self.pulse.server_info()
                _default_sink_name = _server_info.default_sink_name
                del _server_info
            except:
                self._reload_pulse()
            #
            if _default_sink_name:
                self.default_sink_name = _default_sink_name
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
            # 
            _volume = _sink.volume.values
            _level = int(round(max(_volume), 2)*100)
            _mute = _sink.mute
            #
            if self.btn_audio.value == [int(_level), _mute]:
                return
            #
            iicon = None
            #
            if 0 <= _level < 31:
                _icon = "audio-volume-low"
                iicon = QIcon.fromTheme(_icon, QIcon("icons/audio-volume-low.svg"))
            elif 31 <= _level < 61:
                _icon = "audio-volume-medium"
                iicon = QIcon.fromTheme(_icon, QIcon("icons/audio-volume-medium.svg"))
            elif 61 <= _level < 91:
                _icon = "audio-volume-high"
                iicon = QIcon.fromTheme(_icon, QIcon("icons/audio-volume-high.svg"))
            elif _level >= 91:
                _icon = "audio-volume-overamplified"
                iicon = QIcon.fromTheme(_icon, QIcon("icons/audio-volume-overamplified.svg"))
            #
            if _mute == 1:
                _icon = "audio-volume-muted"
                iicon = QIcon.fromTheme(_icon, QIcon("icons/audio-volume-muted.svg"))
            #
            if iicon and not iicon.isNull():
                _msg = ""
                #
                self.btn_audio.setIcon(iicon)
                self.btn_audio.value = [int(_level), _mute]
                if _sink.description == "Dummy Output":
                    self.btn_audio.setToolTip("{}:{}".format("Dummy Output", _level))
                    _icon = "audio-volume-muted"
                    iicon = QIcon.fromTheme(_icon, QIcon("icons/audio-volume-muted.svg"))
                    self.btn_audio.setIcon(iicon)
                    self.btn_audio.value = [-999, -999]
                else:
                    if _mute:
                        _msg = str(_level)+"  (muted)"
                    else:
                        _msg = str(_level)
                    self.btn_audio.setToolTip(" {} ".format(_msg))
                #
                if _TRAY != None:
                    _TRAY.setIcon(iicon)
                    _TRAY.setToolTip(_msg)
            #
            if not _type == "start" and _type == "vol_change":
                if _mute == 1:
                    self.mslider.setValue(0)
                else:
                    self.mslider.setValue(_level)
            elif _type == "start":
                self.mslider.setValue(_level)
        #
        else:
            _icon = "audio-volume-muted"
            iicon = QIcon.fromTheme(_icon, QIcon("icons/audio-volume-muted.svg"))
            self.btn_audio.setIcon(iicon)
            self.btn_audio.value = [-999, -999]
            self.btn_audio.setToolTip("No audio devices")
            #
            if not _type == "start" and _type == "vol_change":
                self.mslider.setValue(0)
    #
    def on_mbtn_mixer(self):
        try:
            if MIXER_CONTROL:
                Popen([MIXER_CONTROL])
                self.window.hide()
        except Exception as E:
            MyDialog("Error", str(E),self)
    
############## audio


class audioThread(QThread):
    sig = pyqtSignal(list)
    
    def __init__(self, _pulse, parent=None):
        super(audioThread, self).__init__(parent)
        self.pulse = _pulse
    
    def run(self):
        with self.pulse.pulsectl.Pulse('event-audio') as pulse:
            #
            def audio_events(ev):
                # sink
                if ev.facility == pulse.event_facilities[6]:
                    # volume change
                    if ev.t == self.pulse.PulseEventTypeEnum.change:
                        self.sig.emit(["change-sink", ev.index])
                    elif ev.t == self.pulse.PulseEventTypeEnum.remove:
                        self.sig.emit(["remove-sink", ev.index])
                    elif ev.t == self.pulse.PulseEventTypeEnum.new:
                        self.sig.emit(["new-sink", ev.index])
                # server
                elif ev.facility == pulse.event_facilities[5]:
                    if ev.t == self.pulse.PulseEventTypeEnum.change:
                        self.sig.emit(["server-changed", ev.index])
            
            pulse.event_mask_set('sink', 'server')
            pulse.event_callback_set(audio_events)
            pulse.event_listen()



######################

app = QApplication([])

_tray = SystemTrayIcon()
_tray.show()

sys.exit(app.exec())
