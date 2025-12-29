#!/usr/bin/env python3

# V. 0.5.1

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QLabel, QWidget, QApplication, QBoxLayout, QPushButton, QSlider, QRadioButton, QCheckBox
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QSizePolicy, QScrollArea
from PyQt6.QtGui import QIcon, QCursor, QPixmap
from PyQt6.QtCore import Qt, QSize, QPoint, pyqtSignal, pyqtSlot, QThread, QEvent, QTimer

import sys, os
from subprocess import Popen

from cfg_audio import *


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
        # 1
        # layout.addLayout(self.scroll_box)
        layout.addWidget(self.scroll)
        # 1
        # self.abox = QHBoxLayout()
        # self.abox.setContentsMargins(0,0,0,0)
        # self.abox.setSpacing(0)
        # layout.addLayout(self.abox)
        #
        _audio = winAudio(self)
        # 1
        # self.abox.insertWidget(0, _audio)
        self.scroll_box.insertWidget(0, _audio)
        #########
        btn = QPushButton("Exit")
        layout.addWidget(btn)
        btn.clicked.connect(self._exit)
    
    def _exit(self):
        sys.exit(0)
    
    def sizeHint(self):
        return QSize(int(WIN_WIDTH/self.pixel_ratio),int(WIN_HEIGHT/self.pixel_ratio))
    
    def on_timer(self):
        global menu_is_shown
        if menu_is_shown == 1 and self.isHidden():
            menu_is_shown = 0

    def hideEvent(self, event):
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.on_timer)
        self._timer.start(int(reset_timer))
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
        return super().eventFilter(obj, event);
    
    def _activateMenu(self, reason):
        global menu_is_shown
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if menu_is_shown == 0:
                self._myMenu.exec(QCursor.pos())
                menu_is_shown = 1
            else:
                menu_is_shown = 0
        
       
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
        self.mslider.setTickPosition(QSlider.TickPosition.TicksBothSides)
        self.mslider.setMinimum(0)
        self.mslider.setMaximum(100)
        self.mslider.setTickInterval(10)
        self.mslider.setSingleStep(AUDIO_STEP)
        self.mslider.setPageStep(AUDIO_STEP)
        self.mslider.valueChanged.connect(self.on_vslider_changed)
        self.hbox1.addWidget(self.mslider)
        self.mbtn = QPushButton("Volume control")
        self.mbtn.clicked.connect(self.on_mbtn_mixer)
        self.audiobox.addWidget(self.mbtn)
        # sources
        audio_lbl = QLabel("Cards")
        self.audiobox.addWidget(audio_lbl)
        self.laudiobox = QVBoxLayout()
        self.laudiobox.setContentsMargins(2,2,2,2)
        self.audiobox.addLayout(self.laudiobox)
        # the stored sink in the file
        self.start_sink_name = None
        #
        import pulsectl as _pulse
        self.pulse = _pulse.Pulse()
        #
        # default sink name
        self.default_sink_name = None
        # ??
        self.AUDIO_START_LEVEL = AUDIO_START_LEVEL
        self.icon_rect = 0.75
        self._on_start_vol()
        self.on_populate_amenu()
        #
        # microphones
        if USE_MICROPHONE:
            mic_lbl = QLabel("Microphones")
            self.audiobox.addWidget(mic_lbl)
            self.micbox = QVBoxLayout()
            self.micbox.setContentsMargins(2,2,2,2)
            self.audiobox.addLayout(self.micbox)
            #
            self.on_microphone()
            self.on_populate_micmenu()
            # applications that use the mic: client_index, client_name, source_idx
            self.client_mic = []
            self.client_mic_change = None
        #
        self.athread = audioThread(_pulse)
        self.athread.sig.connect(self.athreadslot)
        self.athread.start()
    
############ microphone ##############

    # show or hide the microphone icon
    def on_microphone(self):
        # do nothing in this program
        return
        # #
        # try:
            # _source_list = self.pulse.source_list()
        # except:
            # self._reload_pulse()
            # return
        # #
        # _count = 0
        # for el in _source_list:
            # if not el.name.endswith(".monitor"):
                # _count += 1
        # # if _count > 0:
            # # self.btn_mic.show()
            # # return
        # #
        # # self.btn_mic.hide()
    
    # rebuild the mic list
    def on_populate_micmenu(self):
        try:
            _source_list = self.pulse.source_list()
        except:
            self._reload_pulse()
            return
        #
        _source_list_names = []
        for ell in _source_list:
            _source_list_names.append(ell.name)
        _source_list_listed = []
        _source_list_widget = []
        #
        for i in range(self.micbox.count()):
            if self.micbox.itemAt(i) != None:
                widget = self.micbox.itemAt(i).widget()
                if isinstance(widget, QCheckBox) and hasattr(widget, "item"):
                    _source_list_widget.append(widget)
                    if widget.item not in _source_list_names:
                        self.micbox.removeWidget(widget)
                        self.micbox.takeAt(i)
                        widget.deleteLater()
                        widget = None
                    else:
                        _source_list_listed.append(widget.item)
        #
        for el in _source_list:
            el_name = el.name
            if el_name in _source_list_listed:
                for _w in _source_list_widget:
                    if _w.item == el_name:
                        _w.setChecked(not el.mute)
                        break
                continue
            #
            # skip monitors
            if not el.name.endswith(".monitor"):
                rb1 = QCheckBox(el.description)
                rb1.setTristate(False)
                rb1.item = el_name
                rb1.setChecked(False)
                self.micbox.addWidget(rb1)
                #
                if el.mute == 0:
                    rb1.setChecked(True)
                rb1.stateChanged.connect(self.on_rb1_clicked)
        #
        del _source_list_names
        del _source_list_listed
        del _source_list_widget
        self.on_microphone()
    
    #
    def on_microphone_changed(self):
        return
        # try:
            # _source_list = self.pulse.source_list()
        # except:
            # self._reload_pulse()
            # return
        # # widgets
        # _list_chbtn = []
        # for i in range(self.micbox.count()):
            # if self.micbox.itemAt(i) != None:
                # widget = self.micbox.itemAt(i).widget()
                # if isinstance(widget, QCheckBox):
                    # _list_chbtn.append(widget)
        # #
        # for ell in _source_list:
            # if ell.name.endswith('monitor'):
                # continue
            # for ww in _list_chbtn:
                # if ww.item == ell.name:
                    # _state = ell.mute
                    # ww.setChecked(not _state)
    
    # mic
    def on_rb1_clicked(self, _bool):
        if hasattr(self.sender(), "item"):
            _item = self.sender().item
        else:
            return
        _source = None
        try:
            for el in self.pulse.source_list():
                if el.name == _item:
                    _source = el
                    break
            if _source:
                self._mute_mic(_source, self.sender().isChecked())
        except:
            self._reload_pulse()
    
    # mute mic
    def _mute_mic(self, _source, _state):
        _mute_state = not _state
        try:
            self.pulse.mute(_source, mute=_mute_state)
        except:
            self._reload_pulse()
    
    def on_get_client_source(self, _idx):
        for el in self.pulse.source_list():
            if el.index == _idx:
                self.client_mic_change = _idx
                break

############ end microphone ###########

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
        for i in range(self.laudiobox.count()):
            if self.laudiobox.itemAt(i) != None:
                widget = self.laudiobox.itemAt(i).widget()
                if isinstance(widget, QRadioButton) and hasattr(widget, "item"):
                    _sink_list_widget.append(widget)
                    if widget.item not in _sink_list_names:
                        self.laudiobox.removeWidget(widget)
                        self.laudiobox.takeAt(i)
                        widget.deleteLater()
                        widget = None
                    else:
                        _sink_list_listed.append(widget.item)
        #
        try:
            _sink_file_path = os.path.join(curr_path,"sink_default")
            if os.path.exists(_sink_file_path):
                with open(_sink_file_path, "r") as _f:
                    _sink_name = _f.readline()
                self.start_sink_name = _sink_name.strip("\n")
        except Exception as E:
            MyDialog("Error", str(E),None)
        #
        try:
            _server_info = self.pulse.server_info()
            self.default_sink_name = _server_info.default_sink_name
            del _server_info
        except:
            self._reload_pulse()
        #
        for ell in _sink_list:
            ### disable all if no audio devices found
            ell_name = ell.name
            if ell_name == "auto_null":
                return
            #
            if ell_name in _sink_list_listed:
                for _w in _sink_list_widget:
                    if _w.item == ell_name:
                        if ell_name == self.default_sink_name:
                            _w.setChecked(True)
                        else:
                            _w.setChecked(False)
                continue
            #
            rb0 = QRadioButton(ell.description)
            self.laudiobox.addWidget(rb0)
            rb0.item = ell_name
            if ell_name == self.default_sink_name:
                rb0.setChecked(True)
            #
            rb0.clicked.connect(self.on_rb0_clicked)
        #
        del _sink_list_names
        del _sink_list_listed
        del _sink_list_widget
    
    def on_rb0_clicked(self, _bool):
        _item = None
        try:
            _sink_list = self.pulse.sink_list()
        except:
            self._reload_pulse()
            return
        if hasattr(self.sender(), "item"):
            _item = self.sender().item
        if not _item:
            return
        #
        _sink = None
        for ell in _sink_list:
            if ell.name == _item:
                _sink = ell
                break
        #
        try:
            self.pulse.sink_default_set(_sink)
            self.default_sink_name = _item
        except:
            self._reload_pulse()
    
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
        try:
            _sink_file_path = os.path.join(curr_path,"sink_default")
            if os.path.exists(_sink_file_path):
                with open(_sink_file_path, "r") as _f:
                    _sink_name = _f.readline()
                self.start_sink_name = _sink_name.strip("\n")
        except Exception as E:
            MyDialog("Error", str(E),None)
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
        if self.AUDIO_START_LEVEL != -1:
            if not isinstance(self.AUDIO_START_LEVEL,int):
                self.AUDIO_START_LEVEL = 20
            if self.AUDIO_START_LEVEL > 100 or self.AUDIO_START_LEVEL < 0:
                self.AUDIO_START_LEVEL = 20
            if self.default_sink_name:
                for ell in _sink_list:
                    if ell.name == self.default_sink_name:
                        _vol = round(self.AUDIO_START_LEVEL/100, 2)
                        try:
                            self.pulse.volume_set_all_chans(ell, _vol)
                        except:
                            pass
                        break
        # set the icon and tooltip - volume
        self._set_volume("start")
    
    # mouse wheel
    def on_vslider_changed(self):
        self.on_volume_change("slider")
        
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
        elif _list[0] == "remove-source":
            self.on_list_audio(_list[1], 201)
        elif _list[0] == "new-source":
            self.on_list_audio(_list[1], 202)
        # with client
        elif USE_MICROPHONE == 2 and _list[0] == "change-source":
            self.on_list_audio(_list[1], 203)
        elif USE_MICROPHONE == 2 and _list[0] == "client-new":
            self.on_list_audio(_list[1], 301)
        elif USE_MICROPHONE == 2 and _list[0] == "client-removed":
            self.on_list_audio(_list[1], 302)
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
        # # # change on stream or output device - more info missed
        # # elif _t == 301:
            # # pass
        # # source
        elif _t in [201,202]:
            self.on_populate_amenu()
            self._set_volume(102)
            if USE_MICROPHONE:
                self.on_microphone()
                self.on_populate_micmenu()
        # source with client
        elif _t == 203:
            self.on_get_client_source(_el)
            if USE_MICROPHONE:
                self.on_populate_micmenu()
        # client new
        elif _t == 301:
            self.on_new_client(_el)
        # client removed
        elif _t == 302:
            self.on_remove_client(_el)
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
            # _description = _sink.description
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
                # os.system("{} &".format(MIXER_CONTROL))
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
                # 1 card - 3 module - 4 sample_cache - 5 server
                # sink
                if ev.facility == pulse.event_facilities[6]:
                    # volume change
                    if ev.t == self.pulse.PulseEventTypeEnum.change:
                        self.sig.emit(["change-sink", ev.index])
                    elif ev.t == self.pulse.PulseEventTypeEnum.remove:
                        self.sig.emit(["remove-sink", ev.index])
                    elif ev.t == self.pulse.PulseEventTypeEnum.new:
                        self.sig.emit(["new-sink", ev.index])
                # source
                elif ev.facility == pulse.event_facilities[8]:
                    # with client
                    if ev.t == self.pulse.PulseEventTypeEnum.change:
                        self.sig.emit(["change-source", ev.index])
                    elif ev.t == self.pulse.PulseEventTypeEnum.remove:
                        self.sig.emit(["remove-source", ev.index])
                    elif ev.t == self.pulse.PulseEventTypeEnum.new:
                        self.sig.emit(["new-source", ev.index])
                # client
                elif ev.facility == pulse.event_facilities[2]:
                    if ev.t == self.pulse.PulseEventTypeEnum.remove:
                        self.sig.emit(["client-removed", ev.index])
                    elif ev.t == self.pulse.PulseEventTypeEnum.new:
                        self.sig.emit(["client-new", ev.index])
                # server
                elif ev.facility == pulse.event_facilities[5]:
                    if ev.t == self.pulse.PulseEventTypeEnum.change:
                        self.sig.emit(["server-changed", ev.index])
            
            pulse.event_mask_set('sink', 'source', 'server')
            # pulse.event_mask_set('sink', 'source')
            # pulse.event_mask_set('sink', 'source', 'client')
            # pulse.event_mask_set('sink', 'source', 'client','server')
            # pulse.event_mask_set('all')
            pulse.event_callback_set(audio_events)
            # pulse.event_listen(timeout=10)
            pulse.event_listen()



######################

app = QApplication([])

_tray = SystemTrayIcon()
_tray.show()

sys.exit(app.exec())