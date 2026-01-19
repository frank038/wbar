#!/usr/bin/env python3

# V. 0.6

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QLabel, QWidget, QApplication, QBoxLayout, QPushButton
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QSizePolicy, QAbstractItemView
from PyQt6.QtGui import QIcon, QCursor, QPixmap
from PyQt6.QtCore import Qt, QSize, QPoint, pyqtSignal, pyqtSlot, QEvent, QTimer
from PyQt6 import QtDBus

import sys, os
from urllib.parse import urlparse, unquote
from pathlib import Path

from cfg_mpris import *

if USE_MPRIS == 2:
    try:
        import requests
    except:
        USE_MPRIS = 1

curr_path = os.getcwd()

ICON1 = os.path.join(curr_path,"icons","mpris_icons","mpris.svg")
ICON2 = os.path.join(curr_path,"icons","mpris_icons","mpris_on.svg")
ICON3 = os.path.join(curr_path,"icons","mpris_icons","mpris_off.svg")

menu_is_shown = 0

class myMenu(QMenu):
    def __init__(self):
        super(myMenu, self).__init__()
        self.setWindowTitle("qtmpris1")
        self.pixel_ratio = self.devicePixelRatio()
        layout = QBoxLayout(QBoxLayout.Direction.TopToBottom)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        self.setLayout(layout)
        #
        self.abox = QHBoxLayout()
        self.abox.setContentsMargins(0,0,0,0)
        self.abox.setSpacing(0)
        layout.addLayout(self.abox)
        #
        # {code: [player_name, player-interface, properties_manager-interface, icon]}
        self.LIST_PLAYERS = {}
        _mpris = winMpris(self)
        self.abox.insertWidget(0, _mpris)
        #########
        btn = QPushButton("Exit")
        layout.addWidget(btn)
        btn.clicked.connect(self._exit)
    
    def _exit(self):
        sys.exit(0)
    
    def sizeHint(self):
        return QSize(int(MPRIS_WIN_WIDTH/self.pixel_ratio),int(MPRIS_WIN_HEIGHT/self.pixel_ratio))

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
        self._icon.addFile(ICON1)
        self.setIcon(self._icon)
        self.setToolTip("Mpris manager")
        self.activated.connect(self._activateMenu)
        #
        self.setVisible(True)
        #
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
    
    def customMenu(self):
        self._myMenu.exec(QCursor.pos())
        self._myMenu.setFocus()
       

# mpris
class winMpris(QWidget):
    def __init__(self, parent=None):
        super(winMpris, self).__init__(parent)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint|Qt.WindowType.FramelessWindowHint)#|Qt.WindowType.Popup)
        self.window = parent
        self.pixel_ratio = self.devicePixelRatio()
        ####### main box 
        mainBox = QVBoxLayout()
        mainBox.setContentsMargins(4,4,4,4)
        self.setLayout(mainBox)
        ###
        # {code: [player_name, player-interface, properties_manager-interface, icon]}
        self.list_players = self.window.LIST_PLAYERS
        #
        self.bus = QtDBus.QDBusConnection.sessionBus()
        if not self.bus.isConnected():
            print("Not connected to dbus!")
        #
        self.bus.connect("",'/org/freedesktop/DBus','org.freedesktop.DBus',"NameOwnerChanged",None,self.on_bus_connected)
        #
        # # at start
        # OBJ = "/org/mpris/MediaPlayer2"
        # IF_PLAYER = "org.mpris.MediaPlayer2.Player"
        # mpris = self.find_first_mpris_service(self.bus)
        # if mpris:
            # iface = QtDBus.QDBusInterface(
                # mpris,
                # "/org/mpris/MediaPlayer2",
                # "org.freedesktop.DBus.Properties",
                # self.bus)
        #
        ###
        # widget for the tab widget
        self.box_widget2 = QWidget()
        mainBox.addWidget(self.box_widget2)
        ##### 
        self.lbox = QVBoxLayout()
        self.lbox.setContentsMargins(0,0,0,0)
        self.box_widget2.setLayout(self.lbox)
        #
        self.textLW = QListWidget()
        self.textLW.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.textLW.setSpacing(2)
        self.textLW.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # self.textLW.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # self.textLW.itemClicked.connect(self.on_item_clicked)
        mainBox.addWidget(self.textLW)
        ############
        # self.setGeometry(0,0,MPRIS_WIN_WIDTH,MPRIS_WIN_HEIGHT)
        # #
        # cwX = 0
        # cwY = 0
        # NW = self.width()
        # NH = self.height()
        # this_geom = self.geometry()
        
    @pyqtSlot(str, str, str)
    # name - old - new
    # if new, old is empty
    # if old, new is empty
    def on_bus_connected(self,  _name, _old, _new):
        if _name.startswith("org.mpris.MediaPlayer2.") and str(_old) == "":
            iface = QtDBus.QDBusInterface(
                _name,
                "/org/mpris/MediaPlayer2",
                "org.freedesktop.DBus.Properties",
                self.bus)
            #
            # self.list_players["{}".format(str(new))] = [player_name, player, properties_manager, icon]
            player_name = _name
            player = iface
            properties_manager = None
            icon = None
            self.list_players["{}".format(str(_new))] = [player_name, player, properties_manager, icon]
            #
            iface.connection().connect( _name, # name
                "/org/mpris/MediaPlayer2", # path
                "org.freedesktop.DBus.Properties", # iface
                "PropertiesChanged", # method
                [],
                None, 
                self.get_mpris_message # function
                )
        #
        elif str(_new) == "":
            if str(_old) in self.list_players:
                del self.list_players[str(_old)]
                self.on_list_item_remove(["item-remove", str(_old)])
    
    def get_data_player(self, iface, _d):
        _data = None
        msg = iface.call('Get', 'org.mpris.MediaPlayer2.Player', _d)
        if msg.type() == QtDBus.QDBusMessage.MessageType.ReplyMessage:
            _data = msg.arguments()[0]
        return _data
    
    def find_current_state(self, _player):
        if _player in self.list_players:
            player_data = self.list_players[_player]
            iface = player_data[1]
            ret = self.get_data_player(iface, 'PlaybackStatus')
            return ret
        return None
    
    # Play - Pause - Stop
    def set_player_action(self, _player, _action):
        # _data = None
        if _player in self.list_players:
            player_data = self.list_players[_player]
            iface = player_data[1]
            #
            zservice = player_data[0]
            zpath = '/org/mpris/MediaPlayer2'
            ziface = 'org.mpris.MediaPlayer2.Player'
            smp = QtDBus.QDBusInterface(zservice, zpath, ziface)
            smp.call(_action)
    
    @pyqtSlot(QtDBus.QDBusMessage)
    def get_mpris_message(self, msg):
        if 'Metadata' in msg.arguments()[1]:
            _metadata = msg.arguments()[1]['Metadata']
            if _metadata:
                #
                _title = "Title"
                _artist = "Artist"
                _icon = None
                if 'xesam:title' in _metadata:
                    _title = _metadata['xesam:title']
                else:
                    # if no title in the metadata do nothing
                    return
                if 'xesam:artist' in _metadata:
                    _artist = _metadata['xesam:artist'][0]
                if 'mpris:artUrl' in _metadata:
                    _icon = _metadata['mpris:artUrl']
                #
                _player = str(msg.service())
                if _player in self.list_players:
                    player_data = self.list_players[_player]
                    # add the icon
                    if player_data[3] == None:
                        if _icon != None:
                            # NEW ICON
                            try:
                                if USE_MPRIS == 2 and _icon and _icon.startswith("https://"):
                                    img_data = requests.get(_icon).content
                                    with open('/tmp/mpris_image_name.jpg', 'wb') as handler:
                                        handler.write(img_data)
                                if not os.path.exists('/tmp/mpris_image_name.jpg'):
                                    _icon = ICON3
                            except:
                                if not os.path.exists('/tmp/mpris_image_name.jpg'):
                                    _icon = ICON3
                            player_data[3] = _icon
                    else:
                        old_icon = player_data[3]
                        if old_icon != _icon:
                            # ICON CHANGED
                            if USE_MPRIS == 2 and _icon and _icon.startswith("https://"):
                                try:
                                    img_data = requests.get(_icon).content
                                    with open('/tmp/mpris_image_name.jpg', 'wb') as handler:
                                        handler.write(img_data)
                                    if not os.path.exists('/tmp/mpris_image_name.jpg'):
                                        _icon = ICON3
                                except:
                                    # if not os.path.exists('/tmp/mpris_image_name.jpg'):
                                    _icon = ICON3
                            #
                            player_data[3] = _icon
                    #
                    iface = player_data[1]
                    #
                    can_play = self.get_data_player(iface, "CanPlay")
                    can_pause = self.get_data_player(iface, "CanPause")
                    playback_status = self.get_data_player(iface, "PlaybackStatus")
                    _volume = None
                    player_instance = msg.service()
                    player_name = player_data[0]
                    #
                    _list = ["name-added", player_instance, player_name, _icon, can_play, can_pause, _title, _artist, playback_status]
                    self.on_list_item_add(_list)
        #
        elif "PlaybackStatus" in msg.arguments()[1]:
            _status = msg.arguments()[1]["PlaybackStatus"]
            #
            _player = str(msg.service())
            if _player in self.list_players:
                player_data = self.list_players[_player]
            player_instance = msg.service()
            player_name = player_data[0]
            self.on_list_item_add(["status-changed", player_instance, player_name, _status])
    
    # ["name-added", player_instance, player_name, _image, can_play, can_pause, _title, _artist, _volume]
    # ["status-changed", player_instance, player_name, _status]
    def on_list_item_add(self, _list):
        # status changed
        if _list[0] == "status-changed":
            _found = 0
            num_items = self.textLW.count()
            for i in range(num_items):
                if self.textLW.item(i).idx == _list[1]:
                    _found = 1
                    break
            #
            if _found == 1:
                _status = _list[3]
                list_widget_item = self.textLW.item(i)
                _w = self.textLW.itemWidget(list_widget_item)
                _box = _w.layout()
                num_items2 = _box.count()
                for ii in range(num_items2):
                    _wdg = _box.itemAt(ii).widget()
                    if isinstance(_wdg, QPushButton):
                        if _status == "Playing":
                            _icon = QIcon.fromTheme("media-play", QIcon(os.path.join(curr_path,"icons/mpris_icons/media-play.svg")))
                        elif _status == "Paused":
                            _icon = QIcon.fromTheme("media-pause", QIcon(os.path.join(curr_path,"icons/mpris_icons/media-pause.svg")))
                        elif _status == "Stopped":
                            _icon = QIcon.fromTheme("media-stop", QIcon(os.path.join(curr_path,"icons/mpris_icons/media-stop.svg")))
                        _wdg.setIcon(_icon)
            #
            return
        #
        _found = 0
        num_items = self.textLW.count()
        for i in range(num_items):
            if self.textLW.item(i).idx == _list[1]:
                _found = 1
                break
        #
        if _found == 1:
            list_widget_item = self.textLW.item(i)
            _w = self.textLW.itemWidget(list_widget_item)
            _box = _w.layout()
            num_items2 = _box.count()
            for ii in range(num_items2):
                _wdg = _box.itemAt(ii).widget()
                #
                if isinstance(_wdg, QPushButton):
                    _status = _list[8]
                    _icon = None
                    if _status == "Playing":
                        _icon = QIcon.fromTheme("media-play", QIcon(os.path.join(curr_path,"icons/mpris_icons/media-play.svg")))
                    elif _status == "Paused":
                        _icon = QIcon.fromTheme("media-pause", QIcon(os.path.join(curr_path,"icons/mpris_icons/media-pause.svg")))
                    elif _status == "Stopped":
                        _icon = QIcon.fromTheme("media-stop", QIcon(os.path.join(curr_path,"icons/mpris_icons/media-stop.svg")))
                    if _icon:
                        _wdg.setIcon(_icon)
                elif isinstance(_wdg, QLabel):
                    # if hasattr(_wdg, "title"):
                        # _wdg.setText(_list[6])
                    # elif hasattr(_wdg, "artist"):
                        # _wdg.setText(_list[7])
                    #
                    if hasattr(_wdg, "title"):
                        _text = "{}\n{}".format(_list[6],_list[7])
                        _wdg.setText(_text)
                    elif hasattr(_wdg, "icon"):
                        _iicon_tmp = _list[3]
                        #
                        if USE_MPRIS == 2 and _iicon_tmp and _iicon_tmp.startswith("https://"):
                            _iicon = '/tmp/mpris_image_name.jpg'
                        else:
                            if _iicon_tmp == None:# or not os.path.exists(_iicon):
                                _iicon = ICON3
                            else:
                                _iicon = str(Path(unquote(urlparse(_iicon_tmp).path)))
                        if not os.path.exists(_iicon):
                            _iicon = ICON3
                        #
                        try:
                            if os.path.exists(_iicon):
                                pix = QPixmap(_iicon)
                                pix = pix.scaled(MPRIS_IMAGE_SIZE,MPRIS_IMAGE_SIZE)#, aspectRatioMode=Qt.KeepAspectRatio)
                                if not pix.isNull():
                                    _wdg.setPixmap(pix)
                        except:
                            pass
        #
        elif _found == 0:
            lw = QListWidgetItem()
            widgetItem = QWidget()
            widgetItemL = QHBoxLayout()
            ### play/pause button
            _play = QPushButton()
            widgetItemL.addWidget(_play)
            #
            # image
            _iicon_tmp = _list[3]
            if USE_MPRIS == 2 and _iicon_tmp and _iicon_tmp.startswith("https://"):
                _iicon = '/tmp/mpris_image_name.jpg'
            else:
                if _iicon_tmp == None:# or not os.path.exists(_iicon):
                    _iicon = ICON3
                else:
                    _iicon = str(Path(unquote(urlparse(_iicon_tmp).path)))
            if not os.path.exists(_iicon):
                _iicon = ICON3
            #
            try:
                if os.path.exists(_iicon):
                    pix = QPixmap(_iicon)
                    pix = pix.scaled(MPRIS_IMAGE_SIZE,MPRIS_IMAGE_SIZE)#, aspectRatioMode=Qt.KeepAspectRatio)
                    if not pix.isNull():
                        img_lbl = QLabel()
                        img_lbl.icon = 1
                        img_lbl.setPixmap(pix)
                        img_lbl.setMaximumSize(MPRIS_IMAGE_SIZE,MPRIS_IMAGE_SIZE)
                        img_lbl.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
                        widgetItemL.addWidget(img_lbl)
            except:
                pass
            #
            # player name
            # text1 = _list[6]
            text1 = "{}\n{}".format(_list[6],_list[7])
            widgetTXT =  QLabel()
            widgetTXT.setText(text1)
            widgetTXT.title = 1
            widgetItemL.addWidget(widgetTXT)
            #
            # text2 = _list[7]
            # widgetTXT2 = QLabel()#text=text2)
            # widgetTXT2.setText(text2)
            # widgetTXT2.artist = 1
            # widgetItemL.addWidget(widgetTXT2)
            #
            widgetItemL.addStretch()
            #
            #### play/pause button
            # _play = QPushButton()
            _play.idx = _list[1]
            _play.setFlat(True)
            _play.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
            #
            _code = _list[1]
            if _code in self.list_players:
                _iface = self.list_players[_code][1]
            _playback_status = self.get_data_player(_iface, "PlaybackStatus")
            #
            if _playback_status == "Playing":
                _icon = QIcon.fromTheme("media-play", QIcon(os.path.join(curr_path,"icons/mpris_icons/media-play.svg")))
            elif _playback_status == "Paused":
                _icon = QIcon.fromTheme("media-pause", QIcon(os.path.join(curr_path,"icons/mpris_icons/media-pause.svg")))
            # elif _playback_status == "Stopped":
            else:
                _icon = QIcon.fromTheme("media-stop", QIcon(os.path.join(curr_path,"icons/mpris_icons/media-stop.svg")))
            _play.setIcon(_icon)
            _play.setIconSize(QSize(button_size, button_size))
            _play.clicked.connect(self.on_play)
            #
            widgetItem.setLayout(widgetItemL)  
            lw.setSizeHint(widgetItem.sizeHint())
            #
            lw.idx = _list[1]
            #
            self.textLW.addItem(lw)
            self.textLW.setItemWidget(lw, widgetItem)
    
    def on_play(self):
        ret = self.find_current_state(self.sender().idx)
        if ret in ["Paused", "Stopped"]:
            # set to playing
            self.set_player_action(self.sender().idx, "Play")
            # self.set_player_action(self.sender().idx, "PlayPause")
            # # verify
            # ret = self.find_current_state(self.sender().idx)
        elif ret == "Playing":
            # set to pause
            self.set_player_action(self.sender().idx, "Pause")
            # self.set_player_action(self.sender().idx, "PlayPause")
            # # verify
            # ret = self.find_current_state(self.sender().idx)
    
    def on_list_item_remove(self, _list):
        num_items = self.textLW.count()
        for i in range(num_items):
            if self.textLW.item(i).idx == _list[1]:
                itemW = self.textLW.item(i)
                self.textLW.takeItem(self.textLW.row(itemW))
                del itemW
                break
    

######################

app = QApplication([])

_tray = SystemTrayIcon()
_tray.show()

sys.exit(app.exec())