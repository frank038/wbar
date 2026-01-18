#!/usr/bin/env python3

# V. 0.9.12

import os,sys,shutil,stat
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import Gtk, Gdk, Gio, GLib, GtkLayerShell, GObject, Pango
from gi.repository import GdkPixbuf
from pathlib import Path
import json
from threading import Thread
from threading import Event
import queue
from subprocess import check_output, Popen, PIPE, CalledProcessError
import signal
import psutil
import time, datetime
import dbus
import dbus.service as Service
from lang import *

# 0 use the Gio method - 1 use PIL
_USE_PIL = 0
if _USE_PIL == 1:
    try:
        from PIL import Image
    except:
        _USE_PIL = 0
    import io


_curr_dir = os.getcwd()

def _error_log(_error):
    print(_error)
    # _now = datetime.datetime.now().strftime("%Y-%m-%d %H:%m")
    # _ff = open(os.path.join(_curr_dir, "error.log"), "a")
    # _ff.write(_now+": "+_error+"\n\n")
    # _ff.close()

_HOME = Path.home()

_display = Gdk.Display.get_default()
display_type = GObject.type_name(_display.__gtype__)

is_wayland = display_type=="GdkWaylandDisplay"
if not is_wayland:
    _error_log("Wayland required.")
    print("Wayland required.")
    sys.exit()

is_x11 = display_type=="GdkX11Display"
if is_x11:
    _error_log("Wayland required.")
    print("Wayland required.")
    sys.exit()

if is_wayland:
    ret = GtkLayerShell.is_supported()
    if ret == False:
        _error_log("Gtk layer shell support required.")
        sys.exit()

# sticky notes folder
if not os.path.exists(os.path.join(_curr_dir,"notes")):
    try:
        os.makedirs(os.path.join(_curr_dir,"notes"))
    except:
        _error_log("Cannot create the folder notes.")
        sys.exit()
        

# other options
_other_settings_conf = None
_other_settings_config_file = os.path.join(_curr_dir,"configs","other_settings.json")
_starting_other_settings_conf = {"pad-value":4,"use-tray":0,"double-click":0,"use-taskbar":0}
if not os.path.exists(_other_settings_config_file):
    try:
        _ff = open(_other_settings_config_file,"w")
        _data_json = _starting_other_settings_conf
        json.dump(_data_json, _ff, indent = 4)
        _ff.close()
        _other_settings_conf = _starting_other_settings_conf
    except:
        _error_log("Service config file error.")
        sys.exit()
else:
    _ff = open(_other_settings_config_file, "r")
    _other_settings_conf = json.load(_ff)
    _ff.close()


_pad = _other_settings_conf["pad-value"]
USE_TRAY = _other_settings_conf["use-tray"]
DOUBLE_CLICK = _other_settings_conf["double-click"]
USE_TASKBAR = _other_settings_conf["use-taskbar"]
USE_CSS = _other_settings_conf["use-css"]

if USE_CSS:
    screen = Gdk.Screen.get_default()
    provider = Gtk.CssProvider()
    provider.load_from_path(os.path.join(_curr_dir,"configs/panelstyle.css"))
    Gtk.StyleContext.add_provider_for_screen(screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)


_context = None
if USE_TASKBAR:
    from wl_framework.loop_integrations import GLibIntegration
    from wl_framework.network.connection import WaylandConnection
    from wl_framework.protocols.foreign_toplevel import ForeignTopLevel

# default configuration
_starting_conf = {"panel":{"height":30,"width":0,"corner-top":30,\
    "corner-bottom":0,"position":1,"clipboard":1,\
    "label1":0,"label2":0,"tasklist":1,"clock":1,"time_format":0,\
    "volume_command":""} }

if is_wayland:
    if not shutil.which("wl-paste"):
        _starting_conf["panel"]["clipboard"] = 0

_panelconf = os.path.join(_curr_dir, "configs/panelconfg.json")


_menu_conf = None
_menu_config_file = os.path.join(_curr_dir,"configs","menu.json")
# live_search: num. of chars to perform a seeking; win_position: 0 left - 1 center
_starting_menu_conf = {"wwidth":880,"wheight":600,"terminal":"xfce4-terminal",\
"cat_icon_size":64,"item_icon_size":64,"item_width":0,"live_search":3,"win_position":0,"menu_editor":""}

if not os.path.exists(_menu_config_file):
    try:
        _ff = open(_menu_config_file,"w")
        _data_json = _starting_menu_conf
        json.dump(_data_json, _ff, indent = 4)
        _ff.close()
        _menu_conf = _starting_menu_conf
    except:
        _error_log("Menu config file error.")
        sys.exit()
else:
    _ff = open(_menu_config_file, "r")
    _menu_conf = json.load(_ff)
    _ff.close()


_service_conf = None
_service_config_file = os.path.join(_curr_dir,"configs","service.json")
_starting_service_conf = {"wwidth":800,"wheight":600,"logout":"","reboot":"","shutdown":"","note-width":300,"note-height":300}
if not os.path.exists(_service_config_file):
    try:
        _ff = open(_service_config_file,"w")
        _data_json = _starting_service_conf
        json.dump(_data_json, _ff, indent = 4)
        _ff.close()
        _service_conf = _starting_service_conf
    except:
        _error_log("Service config file error.")
        sys.exit()
else:
    _ff = open(_service_config_file, "r")
    _service_conf = json.load(_ff)
    _ff.close()


_menu_favorites = os.path.join(_curr_dir,"favorites")
if not os.path.exists(_menu_favorites):
    _f = open(_menu_favorites,"w")
    _f.write("\n")
    _f.close()

# the language files
_lang_list = os.listdir(os.path.join(_curr_dir,"langs"))

qq = queue.Queue(maxsize=1)
USER_THEME=0

# add a monitor after adding a new path
app_dirs_user = [os.path.join(os.path.expanduser("~"), ".local/share/applications")]
app_dirs_system = ["/usr/share/applications", "/usr/local/share/applications"]
#### main application categories
# Bookmarks = []
Development = []
Education = []
Game = []
Graphics = []
Multimedia = []
Network = []
Office = []
Settings = []
System = []
Utility = []
Other = []

USE_NOTIFICATIONS = 0
_notification_conf = None
_notification_config_file = os.path.join(_curr_dir,"configs", "notifications.json")
# use_this: 1 yes - 0 no
# do not disturb (dnd): 0 not active - 1 except urgent - 2 always active
# sound_play: 0 no sounds - 1 use gsound - 2 string: audio player
_starting_notification_conf = {"use_this":1,"nwidth":500,"nheight":200,"icon_size":64,"dnd":0,"sound_play":1,"bottom_limit":200,"skip_apps":""}
if not os.path.exists(_notification_config_file):
    try:
        _ff = open(_notification_config_file,"w")
        _data_json = _starting_notification_conf
        json.dump(_data_json, _ff, indent = 4)
        _ff.close()
        _notification_conf = _starting_notification_conf
    except:
        _error_log("Notification config file error.")
        sys.exit()
else:
    _ff = open(_notification_config_file, "r")
    _notification_conf = json.load(_ff)
    _ff.close()

if _notification_conf:
    try:
        USE_NOTIFICATIONS = _notification_conf["use_this"]
    except:
        _error_log("Error with the notification config file: key error: use_this. Notifications disabled.")
        USE_NOTIFICATIONS = 0

if USE_NOTIFICATIONS:
    from dbus.mainloop.glib import DBusGMainLoop
    mainloop = DBusGMainLoop(set_as_default=True)
    STORE_NOTIFICATIONS = 1
    SOUND_PLAYER = 1
    if SOUND_PLAYER == 1:
        gi.require_version('GSound', '1.0')
        from gi.repository import GSound
    
# clipboard
USE_CLIPBOARD = 1
CLIP_STORAGE = {}
clipboardpid = None
CLIP_CHAR_PREVIEW = 499
if USE_CLIPBOARD:
    SKIP_FILES = 1
    CLIPS_PATH = os.path.join(_curr_dir, "clips")
    _starting_clipboard_conf = {"wwidth":600,"wheight":600, "max_chars":500, "max_clips":100, "chars_preview": 50}
    _clipboard_config_file = os.path.join(_curr_dir,"configs", "clipboard.json")
    _clipboard_conf = None
    if not os.path.exists(_clipboard_config_file):
        try:
            _ff = open(_clipboard_config_file,"w")
            _data_json = _starting_clipboard_conf
            json.dump(_data_json, _ff, indent = 4)
            _ff.close()
            _clipboard_conf = _starting_clipboard_conf
        except:
            _error_log("Clipborad config file error.")
            sys.exit()
    else:
        _ff = open(_clipboard_config_file, "r")
        _clipboard_conf = json.load(_ff)
        _ff.close()
    
    CLIP_MAX_SIZE = _clipboard_conf["max_chars"]
    _tmp_text = None

    # the latest data
    _list_clips_tmp = sorted(os.listdir(CLIPS_PATH), reverse=False)
    _clip = None
    if _list_clips_tmp:
        _list_clips = _list_clips_tmp
        del _list_clips_tmp
        _clip = _list_clips[-1]

    if _clip:
        with open(os.path.join(CLIPS_PATH, _clip) , "r") as _f:
            _tmp_text = "".join(_f.readlines())
    
# populate the clipboard list
def on_load_clips():
    _clips = sorted(os.listdir(CLIPS_PATH), reverse=False)
    for _clip in _clips:
        with open(os.path.join(CLIPS_PATH, _clip)) as _f:
            _ctext_tmp = _f.readlines()
            _ctext = "".join(_ctext_tmp)
            if _ctext.strip("\n"):
                if not _clip in CLIP_STORAGE:
                    CLIP_STORAGE[_clip] = _ctext[0:CLIP_MAX_SIZE].encode()

if USE_CLIPBOARD and is_wayland:
    if shutil.which("wl-copy"):
        os.system("wl-copy --clear")

class Bus:
    def __init__(self, conn, name, path):
        self.conn = conn
        self.name = name
        self.path = path

    def call_sync(self, interface, method, params, params_type, return_type):
        try:
            return self.conn.call_sync(
                self.name,
                self.path,
                interface,
                method,
                GLib.Variant(params_type, params),
                GLib.VariantType(return_type),
                Gio.DBusCallFlags.NONE,
                -1,
                None,
            )
        except:
            pass

    def get_menu_layout(self, *args):
        return self.call_sync(
            'com.canonical.dbusmenu',
            'GetLayout',
            args,
            '(iias)',
            '(u(ia{sv}av))',
        )
    
    
    def menu_event(self, *args):
        self.call_sync('com.canonical.dbusmenu', 'Event', args, '(isvu)', '()')
        
    def _user_activate(self):
        self.call_sync('org.kde.StatusNotifierItem', 'Activate', GLib.Variant("(ii)", (0, 0)), '(ii)', '()')
    
    def _user_secondary_activate(self):
        self.call_sync('org.kde.StatusNotifierItem', 'SecondaryActivate', GLib.Variant("(ii)", (0, 0)), '(ii)', '()')

if USE_TRAY:
    conn = Gio.bus_get_sync(Gio.BusType.SESSION)

class MyButton(Gtk.Image):
    @GObject.Property
    def property_one(self):
        return self._property_one

    @property_one.setter
    def property_one(self, value):
        self._property_one = value

_MENU = []
menu = None
_bus = None
icon_theme = Gtk.IconTheme.get_default()

NODE_INFO = Gio.DBusNodeInfo.new_for_xml("""

<?xml version="1.0" encoding="UTF-8"?>
<node>
    <interface name="org.kde.StatusNotifierWatcher">
        <method name="RegisterStatusNotifierItem">
            <arg type="s" direction="in"/>
        </method>
        <property name="RegisteredStatusNotifierItems" type="as" access="read">
        </property>
        <property name="IsStatusNotifierHostRegistered" type="b" access="read">
        </property>
    </interface>
</node>""")

items = {}
old_items = {}


main_categories = ["Multimedia","Development","Education","Game","Graphics","Network","Office","Settings","System","Utility"]
    
# removed "Audio" e "Video" main categories
freedesktop_main_categories = ["AudioVideo","Development", 
                            "Education","Game","Graphics","Network",
                            "Office","Settings","System","Utility"]
# additional categories
development_extended_categories = ["Building","Debugger","IDE","GUIDesigner",
                            "Profiling","RevisionControl","Translation",
                            "Database","WebDevelopment"]

office_extended_categories = ["Calendar","ContanctManagement","Office",
                            "Dictionary","Chart","Email","Finance","FlowChart",
                            "PDA","ProjectManagement","Presentation","Spreadsheet",
                            "WordProcessor","Engineering"]

graphics_extended_categories = ["2DGraphics","VectorGraphics","RasterGraphics",
                            "3DGraphics","Scanning","OCR","Photography",
                            "Publishing","Viewer"]

utility_extended_categories = ["TextTools","TelephonyTools","Compression",
                            "FileTools","Calculator","Clock","TextEditor",
                            "Documentation"]

settings_extended_categories = ["DesktopSettings","HardwareSettings",
                            "Printing","PackageManager","Security",
                            "Accessibility"]

network_extended_categories = ["Dialup","InstantMessaging","Chat","IIRCClient",
                            "FileTransfer","HamRadio","News","P2P","RemoteAccess",
                            "Telephony","VideoConference","WebBrowser"]

# added "Audio" and "Video" main categories
audiovideo_extended_categories = ["Audio","Video","Midi","Mixer","Sequencer","Tuner","TV",
                            "AudioVideoEditing","Player","Recorder",
                            "DiscBurning"]

game_extended_categories = ["ActionGame","AdventureGame","ArcadeGame",
                            "BoardGame","BlockGame","CardGame","KidsGame",
                            "LogicGame","RolePlaying","Simulation","SportGame",
                            "StrategyGame","Amusement","Emulator"]

education_extended_categories = ["Art","Construction","Music","Languages",
                            "Science","ArtificialIntelligence","Astronomy",
                            "Biology","Chemistry","ComputerScience","DataVisualization",
                            "Economy","Electricity","Geography","Geology","Geoscience",
                            "History","ImageProcessing","Literature","Math","NumericAnalysis",
                            "MedicalSoftware","Physics","Robots","Sports","ParallelComputing",
                            "Electronics"]

system_extended_categories = ["FileManager","TerminalEmulator","FileSystem",
                            "Monitor","Core"]

# _categories = [freedesktop_main_categories,development_extended_categories,office_extended_categories,graphics_extended_categories,utility_extended_categories,settings_extended_categories,network_extended_categories,audiovideo_extended_categories,game_extended_categories,education_extended_categories,system_extended_categories]

def _on_find_cat(_cat):
    if not _cat:
        return "Other"
    
    ccat = _cat.split(";")
    for cccat in ccat:
        # search in the main categories first
        if cccat in freedesktop_main_categories:
            # from AudioVideo to Multimedia
            if cccat == "AudioVideo":
                return "Multimedia"
            return cccat
        elif cccat in development_extended_categories:
            return "Development"
        elif cccat in office_extended_categories:
            return "Office"
        elif cccat in graphics_extended_categories:
            return "Graphics"
        elif cccat in utility_extended_categories:
            return "Utility"
        elif cccat in settings_extended_categories:
            return "Settings"
        elif cccat in network_extended_categories:
            return "Network"
        elif cccat in audiovideo_extended_categories:
            #return "AudioVideo"
            return "Multimedia"
        elif cccat in game_extended_categories:
            return "Game"
        elif cccat in education_extended_categories:
            return "Education"
        elif cccat in system_extended_categories:
            return "System"
    
    return "Other"

the_menu = []

def _f_populate_menu():
    global the_menu
    the_menu = []
    _ap = Gio.AppInfo
    _list_apps = _ap.get_all()
    for _el in _list_apps:
        # no display
        if _el.get_nodisplay():
            continue
        # display name
        _el_name = _el.get_display_name()
        # category
        _cat_tmp = _el.get_categories()
        _el_cat = _on_find_cat(_cat_tmp)
        # executable
        _el_exec = _el.get_executable()
        # icon
        # <Gio.ThemedIcon object at 0x7f5e9421e980 (GThemedIcon at 0x1ebff190)>
        _el_icon = _el.get_icon()
        if _el_icon:
            if isinstance(_el_icon,Gio.ThemedIcon):
                _el_icon = _el_icon.to_string()
            elif isinstance(_el_icon,Gio.FileIcon):
                _el_icon = _el_icon.get_file().get_path()
        else:
            _el_icon = None
        # comment
        _el_comment = _el.get_description() or None
        _el_path = _el.get_filename()
        
        if not _el_name or not _el_exec or not _el_path:
            continue
        else:
            the_menu.append([_el_name,_el_cat,_el_exec,_el_icon,_el_comment,_el_path,_el])

# build the menu at start
_f_populate_menu()


class SignalObject(GObject.Object):
    
    def __init__(self):
        GObject.Object.__init__(self)
        self._name = ""
        self.value = -99
        self._list = []
    
    @GObject.Property(type=str)
    def propName(self):
        'Read-write integer property.'
        return self._name

    @propName.setter
    def propName(self, name):
        self._name = name
    
    @GObject.Property(type=int)
    def propInt(self):
        'Read-write integer property.'
        return self.value

    @propInt.setter
    def propInt(self, value):
        self.value = value
    
    @GObject.Property(type=object)
    def propList(self):
        'Read-write integer property.'
        return self._list

    @propList.setter
    def propList(self, data):
        self._list = [data]


class MyWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="mypanel")
        
        self.connect("destroy", self._to_close)
        
        # for menu rebuild
        self.q = queue.Queue(maxsize=1)
        
        if USE_CLIPBOARD:
            self.clipboard_conf = _clipboard_conf
            self.clips_path = os.path.join(_curr_dir, "clips")
            if not os.path.exists(self.clips_path):
                _error_log("The clips folder do not exists.")
                sys.exit()
            #
            self.clip_width_tmp = 0
            self.clip_width = self.clipboard_conf["wwidth"]
            self.clip_height_tmp = 0
            self.clip_height = self.clipboard_conf["wheight"]
            self.clip_max_chars = 500
            self.clip_max_chars_tmp = 0
            self.clip_max_clips = 100
            self.clip_max_clips_tmp = 0
            self.chars_preview = self.clipboard_conf["chars_preview"]
            self.chars_preview_tmp = 0
            self.ClipDaemon = None
            self.clip_do_not_track = 0
            if os.path.exists(os.path.join(_curr_dir,"donotdisturb.mode")):
                self.clip_do_not_track = True
            #
        self._display = _display
        # self._display.connect('', self.on_monitor_connected)
        
        self.menu_conf = _menu_conf
        self.menu_width = self.menu_conf["wwidth"]
        self.menu_width_tmp = 0
        self.menu_height = self.menu_conf["wheight"]
        self.menu_height_tmp = 0
        self.menu_terminal = self.menu_conf["terminal"]
        self.menu_terminal_tmp = None
        self.menu_cat_icon_size = self.menu_conf["cat_icon_size"]
        self.menu_cat_icon_size_tmp = 0
        self.menu_item_icon_size = self.menu_conf["item_icon_size"]
        self.menu_item_icon_size_tmp = 0
        self.menu_item_width = self.menu_conf["item_width"]
        self.menu_item_width_tmp = None
        self.menu_live_search = self.menu_conf["live_search"]
        self.menu_live_search_tmp = None
        self.menu_win_position = self.menu_conf["win_position"]
        self.menu_win_position_tmp = None
        self.menu_editor = self.menu_conf["menu_editor"]
        self.menu_editor_tmp = None
        
        self.service_conf = _service_conf
        self.service_width = self.service_conf["wwidth"]
        self.service_width_tmp = 0
        self.service_height = self.service_conf["wheight"]
        self.service_height_tmp = 0
        # self.service_sound_player = self.service_conf["sound-player"]
        # self.service_sound_player_tmp = None
        # self.service_player = self.service_conf["player"]
        # self.service_player_tmp = ""
        self._is_timer_set = 0
        self.timer_id = None
        self._logout = self.service_conf["logout"]
        self._logout_tmp = None
        self._reboot = self.service_conf["reboot"]
        self._reboot_tmp = None
        self._shutdown = self.service_conf["shutdown"]
        self._shutdown_tmp = None
        self.note_width = self.service_conf["note-width"]
        self.note_width_tmp = None
        self.note_height = self.service_conf["note-height"]
        self.note_height_tmp = None
        
        # json configuration
        self._configuration = None
        self.load_conf()
        
        _panel_conf = self._configuration["panel"]
        
        if is_wayland:
            if not shutil.which("wl-paste"):
                _panel_conf["panel"]["clipboard"] = 0
        
        self.win_width = _panel_conf["width"]
        self.win_height = _panel_conf["height"]
        self._corner_top = _panel_conf["corner-top"]
        self._corner_bottom = _panel_conf["corner-bottom"]
        self.win_position = _panel_conf["position"]
        self.clipboard_use = _panel_conf["clipboard"]
        self.label1_use = _panel_conf["label1"]
        self.label2_use = _panel_conf["label2"]
        self.task_use = _panel_conf["tasklist"]
        self.clock_use = _panel_conf["clock"]
        global USE_TASKBAR
        if USE_TASKBAR:
            self.clock_use = 2
        self.time_format = _panel_conf["time_format"]
        self.volume_command = _panel_conf["volume_command"]
        self.volume_command_tmp = None
        
        if is_wayland and self.clipboard_use:
            _ret = self.clipboard_ready()
            if _ret:
                self.ClipDaemon = daemonClipW(self.clips_path, self)
                self.ClipDaemon._start()
            else:
                _error_log("Something wrong with wl-paste or wclipboard.py or something else.")
        
        self.script1_id = None
        self.script2_id = None
        
        self.style_provider = Gtk.CssProvider()
        self.SC = Gtk.StyleContext.new()
        
        num_monitor = self._display.get_n_monitors()
        if num_monitor:
            self._monitor = Gdk.Display.get_default().get_monitor(0)
            screen_width = self._monitor.get_geometry().width
            self.screen_height = self._monitor.get_geometry().height
            self.set_size_request(screen_width-self.win_width,self.win_height)
            #
            self.self_style_context = self.get_style_context()
            self.self_style_context.add_class("mywindow")
            
            css = ".mywindow { border-radius: "+str(self._corner_top)+"px "+str(self._corner_top)+"px "+str(self._corner_bottom)+"px "+str(self._corner_bottom)+"px; }"
            self.style_provider.load_from_data(css.encode('utf-8'))
            self.SC.add_provider_for_screen(
            Gdk.Screen.get_default(),
            self.style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        else:
            if self.ClipDaemon:
                self.ClipDaemon._stop()
            Gtk.main_quit()
        
        # notification config
        self.notification_conf = _notification_conf
        try:
            self.not_use = self.notification_conf["use_this"]
            self.not_width = self.notification_conf["nwidth"]
            self.not_width_tmp = 0
            self.not_height = self.notification_conf["nheight"]
            self.not_height_tmp = 0
            self.not_icon_size = self.notification_conf["icon_size"]
            self.not_icon_size_tmp = 0
            self.not_dnd = self.notification_conf["dnd"]
            self.not_dnd_tmp = -1
            self.not_sounds = self.notification_conf["sound_play"]
            self.not_sounds_tmp = -1
            self.entry_sound_text = ""
            self.not_bottom_limit = self.notification_conf["bottom_limit"]
            self.not_bottom_limit_tmp = -1
            self.skip_apps = self.notification_conf["skip_apps"]
            self._SKIP_APPS = []
            if self.skip_apps != "":
                self._SKIP_APPS = self.skip_apps.split(",")
        except:
            global USE_NOTIFICATIONS
            _error_log("Notification config file error 2.")
            USE_NOTIFICATIONS = 0
        if USE_NOTIFICATIONS:
            conn = dbus.SessionBus(mainloop = mainloop)
            Notifier(conn, "org.freedesktop.Notifications", self)
        
        # the menu window
        self.MW = None
        # the other menu
        self.OW = None
        # the clipboard window
        self.CW = None
        
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.auto_exclusive_zone_enable(self)
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.NONE)
        self.on_set_win_position(self.win_position)
        
        # 0 horizontal 1 vertical - spacing
        self.main_box = Gtk.Box.new(0, 0)
        #
        _pad1 = max(self._corner_top,self._corner_bottom)
        self.main_box.set_margin_start(_pad1)
        self.main_box.set_margin_end(_pad1)
        self.add(self.main_box)
        
        self.left_box = Gtk.Box.new(0,0)
        self.main_box.pack_start(self.left_box, False, False, 0)
        self.left_box.set_halign(1)
        
        self.menubutton = Gtk.EventBox()
        _icon_path = os.path.join(_curr_dir,"icons","menu.svg")
        _pixbf = GdkPixbuf.Pixbuf.new_from_file_at_size(_icon_path, self.win_height,self.win_height)
        _img = Gtk.Image.new_from_pixbuf(_pixbf)
        self.menubutton.add(_img)
        self.menubutton.connect('button-press-event', self.on_button1_clicked)
        self.left_box.pack_start(self.menubutton,False,False,10)
        # output1
        self.temp_out1 = None
        self.label1button = Gtk.EventBox()
        self.label1button.connect('button-press-event', self.on_label1)
        self.label1 = Gtk.Label(label="")
        self.label1.set_use_markup(True)
        self.label1button.add(self.label1)
        self.lbl1_style_context = self.label1.get_style_context()
        self.lbl1_style_context.add_class("label1")
        self.left_box.pack_end(self.label1button,False,False,4)
        
        self.q1 = None
        self.set_timer_label1()
        
        self.center_box = Gtk.Box.new(0,0)
        
        if USE_TASKBAR != 3 and USE_TASKBAR != 0:
            self.main_box.pack_start(self.center_box, True, True, 0)
        else:
            self.main_box.set_center_widget(self.center_box)
        
        if USE_TASKBAR == 0:
            self.center_box.set_halign(3)
        elif USE_TASKBAR == 1:
            self.center_box.set_halign(1)
        elif USE_TASKBAR == 2:
            self.center_box.set_halign(2)
            
        self.clock_lbl = Gtk.Label(label="")
        self.clock_lbl_style_context = self.clock_lbl.get_style_context()
        self.clock_lbl_style_context.add_class("clocklabel")
        # clock at center
        if self.clock_use == 1:
            self._t_id = None
            self.center_box.pack_start(self.clock_lbl,False,False,10)
            self.on_set_clock2(self.clock_use)
        
        # tasklist
        global _context
        if USE_TASKBAR:
            try:
                _context = taskbarContext()
            except RuntimeError as e:
                USE_TASKBAR = 0
        if USE_TASKBAR:
            self.context = _context
            self.manager = self.context.manager
            self.on_set_tasklist()
        
        self.right_box = Gtk.Box.new(0,0)
        self.main_box.pack_end(self.right_box, False, False, 0)
        self.right_box.set_halign(2)
        
        self.otherbutton = Gtk.EventBox()
        _icon_path = os.path.join(_curr_dir,"icons","other_menu.svg")
        _pixbf = GdkPixbuf.Pixbuf.new_from_file_at_size(_icon_path, self.win_height,self.win_height)
        _img = Gtk.Image.new_from_pixbuf(_pixbf)
        self.otherbutton.add(_img)
        self.otherbutton.connect('button-press-event', self.on_other_button)
        self.right_box.pack_end(self.otherbutton,False,False,10)
        
        # sticky notes list
        self.list_notes = []
        #
        try:
            _list_notes = os.listdir(os.path.join(_curr_dir,"notes"))
            if _list_notes:
                for el in _list_notes:
                    with open(os.path.join(_curr_dir,"notes",el)) as ffile:
                        _note = ffile.read()
                        _notedialog = noteDialog(self, _note, el)
                        self.list_notes.append(_notedialog)
        except:
            pass
        
        # clock at right
        if self.clock_use == 2:
            self._t_id = None
            self.right_box.pack_end(self.clock_lbl,False,False,10)
            self.on_set_clock2(self.clock_use)
        
        # tray
        if USE_TRAY:
            self.tray_box = Gtk.Box.new(0,0)
            self.right_box.pack_end(self.tray_box,False,False,0)
            self._app_icon_size = self.win_height-2
        
        # notifications
        if USE_NOTIFICATIONS:
            self.notification_box = Gtk.Box.new(0,0)
            self.right_box.pack_end(self.notification_box,False,False,0)
        
        # clipboard
        self.temp_clip = None
        if self.clipboard_use and USE_CLIPBOARD:
            self.on_set_clipboard(None)
        
        # output2
        self.temp_out2 = None
        self.label2button = Gtk.EventBox()
        self.label2 = Gtk.Label(label="")
        self.label2.set_use_markup(True)
        self.label2button.add(self.label2)
        self.lbl2_style_context = self.label2.get_style_context()
        self.lbl2_style_context.add_class("label2")
        self.label2button.connect('button-press-event', self.on_label2)
        self.right_box.pack_start(self.label2button,False,False,4)
        
        gdir1 = Gio.File.new_for_path(os.path.join(_HOME, ".local/share/applications"))
        self.monitor1 = gdir1.monitor_directory(Gio.FileMonitorFlags.SEND_MOVED, None)
        self.monitor1.connect("changed", self.directory_changed)
        gdir2 = Gio.File.new_for_path("/usr/share/applications")
        self.monitor2 = gdir2.monitor_directory(Gio.FileMonitorFlags.SEND_MOVED, None)
        self.monitor2.connect("changed", self.directory_changed)
        gdir3 = Gio.File.new_for_path("/usr/local/share/applications")
        self.monitor3 = gdir3.monitor_directory(Gio.FileMonitorFlags.SEND_MOVED, None)
        self.monitor3.connect("changed", self.directory_changed)
        
        self.show_all()
        
        if self.clock_use == 0:
            self.clock_lbl.hide()
        
        self.q2 = None
        self.set_timer_label2()
        
        
    
    def on_set_tasklist(self):
        self.box_taskbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.center_box.add(self.box_taskbar)
        # self.center_box.pack_start(self.box_taskbar, True, True, 0)
        # self.center_box.set_center_widget(self.box_taskbar)
        #
        self.center_box.set_hexpand(True)
        self.tbox = Gtk.Box.new(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.tbox.set_name("tasklist")
        self._scroll = Gtk.ScrolledWindow()
        self.box_taskbar.pack_start(self._scroll, True, True, 0)
        self._scroll.connect('scroll-event', self.handle_scroll)
        self._scroll.set_hexpand(True)
        self._scroll.set_property("propagate-natural-width", True)
        #
        self._scroll.set_policy(
            Gtk.PolicyType.EXTERNAL,
            Gtk.PolicyType.NEVER
        )
        self._scroll.add(self.tbox)
        self._scroll.show_all()
        
        self.active_button = None
        self.context.connect('toplevel_new', self.on_toplevel_new)
        self.context.connect('toplevel_synced', self.on_toplevel_synced)
        self.context.connect('toplevel_closed', self.on_toplevel_closed)
        #
        self._create_tasklist_menu()
        #
        self.box_taskbar.show_all()
        
    # def find_label(self,widget):
        # children = widget.get_children()
        # for el in children:
            # if isinstance(el, Gtk.Label):
                # return el
        # return None
                    
    # def set_text_and_ellipsize(self, button, text):
        # b = self.find_label(button)
        # # In case we fail...
        # if b is None:
            # return
        # # setting ellipsize
        # b.set_ellipsize(Pango.EllipsizeMode.END)
    
    def on_toplevel_new(self, context, toplevel):
        self.tbutton = Gtk.ToggleButton()
        self.tbutton.set_name("btn-taskbar")
        self.tbutton.set_relief(Gtk.ReliefStyle.NONE)
        self.tbutton.set_hexpand(False)
        self.tbutton.set_vexpand(False)
        #
        # # self.tbutton.set_name("tba")
        # self.self_style_context2 = self.tbutton.get_style_context()
        # self.self_style_context2.add_class("tba")
        # css = '#btn-taskbar { padding-top: 0px; padding-bottom: 0px; margin-bottom: 0px;}'
        # self.style_provider.load_from_data(css.encode('utf-8'))
        # self.SC.add_provider_for_screen(
        # Gdk.Screen.get_default(),
        # self.style_provider,
        # Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            # )
        #
        # self.tbutton.set_property("width-request", 25)
        # self.tbutton.set_property("height-request", 25)
        #
        self.tbutton.connect('clicked', self.manager.app_toggle, toplevel)
        self.tbutton.connect('button-press-event', self.handle_context_menu, toplevel)
        # self.set_text_and_ellipsize(button, None)
        #
        self.tbutton.hide()
        toplevel.button = self.tbutton
        if not hasattr(self.tbutton, "_icon"):
            self.tbutton._icon = None
        self.tbox.pack_start(self.tbutton, True, True, 0)
    
    def on_toplevel_synced(self, context, toplevel):
        # # Obviously this should do a proper diff and only update if required
        # toplevel.button.set_label(toplevel.title)
        if toplevel.button._icon == None:
            ICON_SIZE = self.win_height-4
            ret_icon = self._on_desktop_entry(os.path.basename(toplevel.app_id))
            _img = None
            if ret_icon:
                try:
                    _img = Gtk.Image.new_from_icon_name(ret_icon, ICON_SIZE)
                except:
                    pass
                #
                if _img:
                    # _img.set_pixel_size(self.win_height)
                    _img.set_pixel_size(ICON_SIZE)
                    toplevel.button.set_image(_img)
                    toplevel.button._icon = 1
                    # _img.set_halign(3)
                    # _img.set_valign(3)
            if not ret_icon or not _img:
                try:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(os.path.join(_curr_dir,"icons","unknown2.svg"), ICON_SIZE, ICON_SIZE, 1)
                    _img = Gtk.Image.new_from_pixbuf(pixbuf)
                    toplevel.button.set_image(_img)
                    toplevel.button._icon = 1
                except Exception as E:
                    toplevel.button.set_label(" A ")
                    toplevel.button._icon = 1
        #
        # toplevel.button.set_size_request(toplevel.button.get_allocated_height(),self.win_height)
        # toplevel.button.set_size_request(self.win_height,self.win_height)
        toplevel.button.show()
        toplevel.button.set_tooltip_text(toplevel.title)
        #
        if 'activated' in toplevel.states:
            if toplevel.button != self.active_button:
                if isinstance(self.active_button, Gtk.ToggleButton):
                    # self.active_button.set_active(False)
                    self.active_button.set_state_flags(Gtk.StateFlags.NORMAL,True)
                self.active_button = toplevel.button
                toplevel.button.set_state_flags(Gtk.StateFlags.CHECKED,True)
        # USELESS or find a better solution
        # elif toplevel.button == self.active_button:
            # toplevel.button.set_state_flags(Gtk.StateFlags.NORMAL,True)
        # 
        # self.set_default_size(-1, self.win_height)
    
    def on_toplevel_closed(self, context, toplevel):
        self.tbox.remove(toplevel.button)
        # 
        # self.set_default_size(-1,self.win_height)
        
    # find the icon from the desktop file
    def _on_desktop_entry(self, _desktop):
        app_dirs_user = [os.path.join(os.path.expanduser("~"), ".local/share/applications")]
        app_dirs_system = ["/usr/share/applications", "/usr/local/share/applications"]
        _ddir = app_dirs_user+app_dirs_system
        _icon = None
        for dd in _ddir:
            if os.path.exists(dd):
                for ff in os.listdir(dd):
                    if os.path.basename(ff) == _desktop+".desktop":
                        try:
                            _ap = Gio.DesktopAppInfo.new_from_filename(os.path.join(dd,ff))
                            _icon = _ap.get_icon()
                            if _icon:
                                if isinstance(_icon,Gio.ThemedIcon):
                                    _icon = _icon.to_string()
                                elif isinstance(_icon,Gio.FileIcon):
                                    _icon = _icon.get_file().get_path()
                                return _icon
                            else:
                                return None
                        except:
                            return None
        
        return None
    
    def handle_scroll(self, scroll, event):
        adj = scroll.get_hadjustment()
        if adj.get_upper() <= adj.get_page_size():
            return
        val = adj.get_value()
        if event.direction == Gdk.ScrollDirection.UP or event.delta_y < 0:
            if val > adj.get_lower():
                adj.set_value(val - adj.get_minimum_increment())
        elif event.direction == Gdk.ScrollDirection.DOWN or event.delta_y > 0:
            if val + adj.get_page_size() < adj.get_upper():
                adj.set_value(val + adj.get_minimum_increment())
    
    def handle_context_menu(self, button, event, toplevel):
        if event.button != Gdk.BUTTON_SECONDARY:
            return False
        for menu, func in (
            (self._menu_maximize, self.manager.app_toggle_maximize),
            (self._menu_minimize, self.manager.app_toggle_minimize),
            # (self._menu_fullscreen, self.manager.app_toggle_fullscreen),
            (self._menu_close, self.manager.app_close)
        ):
            try:
                menu.disconnect_by_func(func)
            except TypeError:
                pass
            menu.connect('activate', func, toplevel)
        self._menu_maximize.set_label(
            'UnMaximize' if 'maximized' in toplevel.states else 'Maximize')
        self._menu_minimize.set_label(
            'UnMinimize' if 'minimized' in toplevel.states else 'Minimize')
        # self._menu_fullscreen.set_label(
            # 'UnFullscreen' if 'fullscreen' in toplevel.states else 'Fullscreen')
        self.menu.popup_at_widget(button, Gdk.Gravity.NORTH, Gdk.Gravity.SOUTH, event)
        return True
    
    def _create_tasklist_menu(self):
        menu = Gtk.Menu.new()
        menu.set_name('panel_menu')
        self._menu_maximize = Gtk.MenuItem.new_with_label('Maximize')
        self._menu_minimize = Gtk.MenuItem.new_with_label('Minimize')
        # self._menu_fullscreen = Gtk.MenuItem.new_with_label('Fullscreen')
        self._menu_close = Gtk.MenuItem.new_with_label('Close')

        menu.append(self._menu_maximize)
        menu.append(self._menu_minimize)
        # menu.append(self._menu_fullscreen)
        menu.append(Gtk.SeparatorMenuItem())
        menu.append(self._menu_close)

        menu.show_all()
        self.menu = menu
        return menu
    
    def on_label1(self, btn, event):
        if event.button == 1:
            _script1 = os.path.join(_curr_dir,"scripts","label1.script")
            if os.path.exists(_script1):
                if not os.access(_script1, os.X_OK):
                    os.chmod(_script1, 0o740)
                try:
                    os.system(f"{_script1} &")
                except:
                    pass
    
    def on_label2(self, btn, event):
        if event.button == 1:
            _script2 = os.path.join(_curr_dir,"scripts","label2.script")
            if os.path.exists(_script2):
                if not os.access(_script2, os.X_OK):
                    os.chmod(_script2, 0o740)
                try:
                    os.system(f"{_script2} &")
                except:
                    pass
    
    def clipboard_ready(self):
        _ret = 1
        if is_wayland:
            if not shutil.which("wl-paste"):
                _ret = 0
            _wclip_file = os.path.join(_curr_dir, "wclipboard.py")
            if not os.path.exists(_wclip_file):
                _ret = 0
        return _ret
        
    def rebuild_menu(self):
        if self.MW:
            self.MW.close()
            self.MW = None
        _f_populate_menu()
    
    def directory_changed(self, monitor, file1, file2, event):
        if (event == Gio.FileMonitorEvent.CREATED):
            self.on_directory_changed(file1.get_path(), "created")
        elif (event == Gio.FileMonitorEvent.DELETED):
            self.on_directory_changed(file1.get_path(), "deleted")

    def on_directory_changed(self, _path, _type):
        try:
            if self.q.empty():
                self.q.put("new", timeout=0.001)
        except:
            pass
        
        if not self.q.empty():
            if self.MW:
                self.MW.close()
                self.MW = None
            
            _bookmarks = None
            with open(os.path.join(_curr_dir, "favorites"), "r") as _f:
                _bookmarks = _f.readlines()
            
            if _type == "deleted":
                for el in _bookmarks[:]:
                    if el.strip("\n") == _path:
                        _bookmarks.remove(el)
                        break
            
            with open(os.path.join(_curr_dir, "favorites"), "w") as _f:
                for el in _bookmarks:
                    _f.write(el)
            
            self.rebuild_menu()
    
    def _item_event(self, widget, event, args):
        # left button
        if event.button == 1:
            name = args[0]
            path = args[1]
            menu = args[2]
            #
            try:
                bus = Bus(conn, name, path)
                bus._user_activate()
            except:
                pass
        # center button
        elif event.button == 2:
            name = args[0]
            path = args[1]
            menu = args[2]
            name = args[0]
            path = args[1]
            menu = args[2]
            #
            try:
                bus = Bus(conn, name, path)
                bus._user_secondary_activate()
            except:
                pass
        # right button
        elif event.button == 3:
            name = args[0]
            path = args[1]
            menu = args[2]
            self._create_menu(name,menu,widget,event)
        
    def build_menu(self, conn, name, path):
        global _MENU
        del _MENU
        _MENU = []
        global _bus
        _bus = None
        _bus = Bus(conn, name, path)
        item = _bus.get_menu_layout(0, -1, [])[1]
        if item:
            _MENU = item[2]
    
    def _activate_item(self, widget, id):
        try:
            _bus.menu_event(id, 'clicked', GLib.Variant('s', ''), time.time())
        except:
            pass
    
    def on_create_menu(self, menu, _data):
        id = _data[0]
        _dict = _data[1]
        #
        if 'toggle-type' in _dict:
            # 'checkmark'
            _toggle_type = _dict['toggle-type']
            _toggle_state = _dict['toggle-state']
            _label_name = _dict['label']
            if _toggle_type == 'checkmark':
                ckb = Gtk.CheckMenuItem.new_with_label(_label_name.replace("_",""))
                ckb.set_active(_toggle_state)
                ckb.connect('activate', self._activate_item, id)
                menu.append(ckb)
        elif 'label' in _dict or 'accessible-desc' in _dict:
            _label_name = ""
            if 'accessible-desc' in _dict:
                if 'label' in _dict:
                    _label_name = _dict['label'].replace("_","")
                else:
                    return
            elif 'label' in _dict:
                _label_name = _dict['label'].replace("_","")
            #
            if 'icon-data' in _dict:
                _icon_data = _dict['icon-data']
                pb = None
                #
                if _USE_PIL:
                    with Image.open(io.BytesIO(bytes(_icon_data))) as im:
                        data = im.tobytes()
                        w, h = im.size
                        data = GLib.Bytes.new(data)
                        pb = GdkPixbuf.Pixbuf.new_from_bytes(data, GdkPixbuf.Colorspace.RGB,
                                True, 8, w, h, w * 4)
                else:
                    input_stream = Gio.MemoryInputStream.new_from_data(_icon_data, None)
                    pb = GdkPixbuf.Pixbuf.new_from_stream(input_stream, None)
                    # ret should be None
                    # ret = input_stream.close_async(2)
                    # ret should be True if closed properly
                    ret = input_stream.close(None)
                #
                img = Gtk.Image.new_from_pixbuf(pb)
                menu_item = Gtk.ImageMenuItem.new_with_label(_label_name)
                menu_item.set_image(img)
            elif 'icon-name' in _dict:
                _icon_name = _dict['icon-name']
                img = Gtk.Image.new_from_icon_name(_icon_name,Gtk.IconSize.MENU)
                menu_item = Gtk.ImageMenuItem.new_with_label(_label_name)
                menu_item.set_image(img)
            else:
                menu_item = Gtk.MenuItem.new_with_label(_label_name)
            _enabled = True
            if 'enabled' in _dict:
                _enabled = bool(_dict['enabled'])
            if _enabled:
                menu_item.connect('activate', self._activate_item, id)
            else:
                menu_item.set_sensitive(_enabled)
            menu.append(menu_item)
            #
            if 'children-display' in _dict:
                _type = _dict['children-display']
                if _type == 'submenu':
                    _submenu_data = _data[2]
                    sub_menu = Gtk.Menu()
                    for el in _submenu_data:
                        self.on_create_menu(sub_menu, el)
                    menu_item.set_submenu(sub_menu)
        elif 'type' in _dict:
            _type = _dict['type']
            _enabled = True
            if 'enabled' in _dict:
                _enabled = bool(_dict['enabled'])
            if _type == 'separator':
                menu.append(Gtk.SeparatorMenuItem())
    
    def _create_menu(self, name,_menu,widget,event):
        self.build_menu(conn, name, _menu)
        global menu
        #
        if menu:
            def _rec_remove(w):
                for child in menu.get_children():
                    if isinstance(child, Gtk.Box):
                        _rec_remove(child)
                        child.destroy()
                        del child
                    else:
                        w.remove(child)
            _rec_remove(menu)
            menu.destroy()
            del menu
            menu = None
        #
        menu = Gtk.Menu()
        #
        if _MENU == []:
            return
        for _data in _MENU:
            self.on_create_menu(menu, _data)
        #
        menu.show_all()
        menu.popup_at_pointer(None)
        # menu.popup_at_widget(self, Gdk.Gravity.SOUTH, Gdk.Gravity.NORTH, None)
        # # menu.popup(None,None,None,None,3, Gtk.get_current_event_time())
        # _geom = widget.get_window().get_geometry()
        # _rect = Gdk.Rectangle(_geom.width, _geom.width, _geom.x, _geom.y+_geom.width)
        # menu.popup_at_rect(widget.get_window(), _rect, Gdk.Gravity.SOUTH, Gdk.Gravity.NORTH, None)
        
    def add_btn(self, _label, name=None, path=None, menu=None):
        btn_i = MyButton()
        btn = Gtk.EventBox()
        btn.add(btn_i)
        btn_i.set_tooltip_text(_label)
        btn_i.set_property('property_one',name)
        if menu != None:
            btn.connect('button-press-event', self._item_event,[name,path,menu])
        self.tray_box.add(btn)
        btn.show_all()
        
    # remove button
    def remove_btn(self, sender):
        for item1 in self.tray_box.get_children():
            if isinstance(item1, Gtk.EventBox):
                item = item1.get_children()[0]
                if sender == item.get_property('property_one'):
                    self.tray_box.remove(item1)
                    item1.destroy()
                    break 
    
    def _set_icon(self, icon_name, path):
        btn = None
        #
        for item1 in self.tray_box.get_children():
            if isinstance(item1, Gtk.EventBox):
                item = item1.get_children()[0]
                if item.get_property('property_one') == path:
                    btn = item
                    break
        if btn != None:
            try:
                _pb = icon_theme.load_icon_for_scale(icon_name, self._app_icon_size, 1, Gtk.IconLookupFlags.FORCE_SIZE)
                btn.set_from_pixbuf(_pb)
            except Exception as E:
                print("error icon: ", str(E))
    
    def _set_tooltip(self, _tooltip, path):
        btn = None
        #
        for item1 in self.tray_box.get_children():
            if isinstance(item1, Gtk.EventBox):
                item = item1.get_children()[0]
                if item.get_property('property_one') == path:
                    btn = item
                    break
        #
        if btn != None:
            btn.set_tooltip_text(_tooltip)
    
    def _item_changed(self, sender, path):
        global items
        global old_items
        # 
        if len(items) > len(old_items):
            _path = sender+path
            _found = [_path, items[_path]]
            #
            old_items = items.copy()
            #
            if _found:
                if 'Status' in _found[1]:
                    _status = _found[1]['Status']
                    if _status == 'Passive':
                        return
                #
                _icon = _found[1]['IconName']
                #
                if 'ToolTip' in _found[1]:
                    _label = _found[1]['ToolTip'][2]
                elif 'Title' in _found[1]:
                    _label = _found[1]['Title']
                else:
                    _label = ""
                #
                _name = _found[0].split("/")[0]
                _path =  "/"+"/".join(_found[0].split("/")[1:])
                if 'Menu' in _found[1]:
                    _menu = _found[1]['Menu']
                else:
                    _menu = None
                #
                self.add_btn(_label, _name, _path, _menu)
                # 
                self._set_icon(_icon, _name)
            #
            return
        # 
        elif len(items) < len(old_items):
            _found = []
            for k,v in old_items.items():
                if items == {}:
                    _found = [k,v]
                    break
                else:
                    if k not in items:
                        _found = [k,v]
                        break
            #
            if _found:
                # remove button
                sender = k.split("/")[0]
                self.remove_btn(sender)
                #
                old_items = items.copy()
                return
        #
        else:
            _path = sender+path
            if _path in items:
                item = items[_path]
                #
                old_item = None
                if _path in old_items:
                    old_item = old_items[_path]
                if old_item:
                    if item != old_item:
                        for key,v in item.items():
                            for kk,vv in old_item.items():
                                if key == kk:
                                    if v != vv:
                                        if key == 'IconName':
                                            _icon = item['IconName']
                                            self._set_icon(_icon, sender)
                                        elif key == 'ToolTip':
                                            _tooltip = item['ToolTip'][2]
                                            self._set_tooltip(_tooltip, sender)
                                        elif key == 'Title':
                                            pass
                                        elif key == 'Status':
                                            _status = item['Status']
                                            if _status in ['Active', 'Attention']:
                                                # create a button
                                                if 'ToolTip' in item:
                                                    _label = item['ToolTip'][2]
                                                elif 'Title' in item:
                                                    _label = item['Title']
                                                else:
                                                    _label = ""
                                                if 'Menu' in item:
                                                    _menu = item['Menu']
                                                else:
                                                    _menu = None
                                                #
                                                self.add_btn(_label, sender, path, _menu)
                                                # set the icon and tooltip
                                                self._set_icon(_icon, sender)
                                            #
                                            else:
                                                self.remove_btn(sender)
                                        elif key == 'AttentionIconName':
                                            pass
                                        elif key == 'OverlayIconName':
                                            pass
                                        # elif key == 'IconThemePath':
                                            # pass
                                    #
                old_items = items.copy()
                return
    
    def render(self, sender, path):
        self._item_changed(sender, path)

    def get_item_data(self, conn, sender, path):
        def callback(conn, red, user_data=None):
            args = conn.call_finish(red)
            items[sender + path] = args[0]
            self.render(sender, path)

        conn.call(
            sender,
            path,
            'org.freedesktop.DBus.Properties',
            'GetAll',
            GLib.Variant('(s)', ['org.kde.StatusNotifierItem']),
            GLib.VariantType('(a{sv})'),
            Gio.DBusCallFlags.NONE,
            -1,
            None,
            callback,
            None,
        )
    
    def on_call( self, 
        conn, sender, path, interface, method, params, invocation, user_data=None
        ):
        props = {
            'RegisteredStatusNotifierItems': GLib.Variant('as', items.keys()),
            'IsStatusNotifierHostRegistered': GLib.Variant('b', True),
        }

        if method == 'Get' and params[1] in props:
            invocation.return_value(GLib.Variant('(v)', [props[params[1]]]))
            conn.flush()
        if method == 'GetAll':
            invocation.return_value(GLib.Variant('(a{sv})', [props]))
            conn.flush()
        elif method == 'RegisterStatusNotifierItem':
            if params[0].startswith('/'):
                path = params[0]
            else:
                path = '/StatusNotifierItem'
            self.get_item_data(conn, sender, path)
            invocation.return_value(None)
            conn.flush()


    def on_signal(self, 
        conn, sender, path, interface, signal, params, invocation, user_data=None
        ):
        if signal == 'NameOwnerChanged':
            if params[2] != '':
                return
            keys = [key for key in items if key.startswith(params[0] + '/')]
            if not keys:
                return
            for key in keys:
                del items[key]
            self.render(sender, path)
        elif sender + path in items:
            self.get_item_data(conn, sender, path)
    
    def on_bus_acquired(self, conn, name, user_data=None):
        for interface in NODE_INFO.interfaces:
            if interface.name == name:
                conn.register_object('/StatusNotifierWatcher', interface, self.on_call)

        def signal_subscribe(interface, signal):
            conn.signal_subscribe(
                None,  # sender
                interface,
                signal,
                None,  # path
                None,
                Gio.DBusSignalFlags.NONE,
                self.on_signal,
                None,  # user_data
            )

        signal_subscribe('org.freedesktop.DBus', 'NameOwnerChanged')
        for signal in [
            'NewAttentionIcon',
            'NewIcon',
            'NewStatus',
            'NewTitle',
            'NewOverlayIcon',
            'NewToolTip',
        ]:
            signal_subscribe('org.kde.StatusNotifierItem', signal)


    def on_name_lost(conn, name, user_data=None):
        _error_log(f'Could not aquire name {name}. Is some other service blocking it?')
        # sys.exit(
            # f'Could not aquire name {name}. '
            # f'Is some other service blocking it?'
        # )
    
    def _message_dialog_yesno(self, _msg):
        messagedialog = Gtk.MessageDialog(parent=self,
                                          modal=True,
                                          message_type=Gtk.MessageType.INFO,
                                          buttons=Gtk.ButtonsType.OK_CANCEL,
                                          text=_msg)
        messagedialog.connect("response", self.dialog_yn_response)
        messagedialog.show()

    def dialog_yn_response(self, messagedialog, response_id):
        if response_id == Gtk.ResponseType.OK:
            messagedialog.destroy()
        elif response_id == Gtk.ResponseType.CANCEL:
            messagedialog.destroy()
        elif response_id == Gtk.ResponseType.DELETE_EVENT:
            messagedialog.destroy()
    
    def _message_dialog_yes(self, _msg):
        messagedialog = Gtk.MessageDialog(parent=self,
                                          modal=True,
                                          message_type=Gtk.MessageType.INFO,
                                          buttons=Gtk.ButtonsType.OK,
                                          text=_msg)
        messagedialog.connect("response", self.dialog_y_response)
        messagedialog.show()

    def dialog_y_response(self, messagedialog, response_id):
        if response_id == Gtk.ResponseType.OK:
            messagedialog.destroy()
        elif response_id == Gtk.ResponseType.DELETE_EVENT:
            messagedialog.destroy()
    
    def set_timer_label1(self):
        self.event1 = None
        self.thread_label1 = None
        if self.label1_use == 1:
            _script1 = None
            self._script1_return = True
            _files = os.listdir(_curr_dir+"/scripts")
            tmp_file = None
            _time = None
            for _f in _files:
                _ff,_ext = os.path.splitext(_f)
                if _ff == "output1":
                    if _ext == '':
                        continue
                    elif _ext == ".sh":
                        tmp_file = _f
                        break
                    else:
                        if _ext[-1] == 's':
                            tmp_file = _f
                            _time = int(_ext[1:-1])*1000
                            break
                        elif _ext[-1] == 'm':
                            tmp_file = _f
                            _time = int(_ext[1:-1])*60000
                            break
            
            if _time != None:
                _script1 = os.path.join(_curr_dir,"scripts",tmp_file)
                _type = 0
                if _script1 and os.access(_script1,os.X_OK):
                    ret = check_output(_script1, shell=False, universal_newlines=True)
                    self.label1.set_text(ret.strip("\n"))
                    self.script1_id = GLib.timeout_add(_time, self.on_script1, _script1)
            elif _time == None:
                _script1 = os.path.join(_curr_dir,"scripts","output1.sh")
                _type = 2
                if _script1 and os.access(_script1,os.X_OK):
                    self.event1 = Event()
                    self.q1 = queue.Queue(maxsize=1)
                    self.thread_label1 = Thread(target=labelThread, args=(self.label1,_script1,self.q1,self.event1,_type))
                    self.thread_label1.start()
    
    def on_script1(self, _script1):
        ret = check_output(_script1, shell=False, universal_newlines=True)
        self.label1.set_text(ret.strip("\n"))
        if self._script1_return == False:
            self.label1.set_text('')
        return self._script1_return
    
    def set_timer_label2(self):
        self.event2 = None
        self.thread_label2 = None
        if self.label2_use == 1:
            _script2 = None
            self._script2_return = True
            _files = os.listdir(_curr_dir+"/scripts")
            tmp_file = None
            _time = None
            for _f in _files:
                _ff,_ext = os.path.splitext(_f)
                if _ff == "output2":
                    if _ext == '':
                        continue
                    elif _ext == ".sh":
                        tmp_file = _f
                        break
                    else:
                        if _ext[-1] == 's':
                            tmp_file = _f
                            _time = int(_ext[1:-1])*1000
                            break
                        elif _ext[-1] == 'm':
                            tmp_file = _f
                            _time = int(_ext[1:-1])*60000
                            break
            if _time != None:
                _script2 = os.path.join(_curr_dir,"scripts",tmp_file)
                _type = 0
                if _script2 and os.access(_script2,os.X_OK):
                    ret = check_output(_script2, shell=False, universal_newlines=True)
                    self.label2.set_text(ret.strip("\n"))
                    self.script2_id = GLib.timeout_add(_time, self.on_script2, _script2)
            elif _time == None:
                _script2 = os.path.join(_curr_dir,"scripts","output2.sh")
                _type = 2
                if _script2 and os.access(_script2,os.X_OK):
                    self.event2 = Event()
                    self.q2 = queue.Queue(maxsize=1)
                    self.thread_label2 = Thread(target=labelThread, args=(self.label2,_script2,self.q2,self.event2,_type))
                    self.thread_label2.start()
    
    def on_script2(self, _script2):
        ret = check_output(_script2, shell=False, universal_newlines=True)
        self.label2.set_text(ret.strip("\n"))
        if self._script2_return == False:
            self.label2.set_text('')
        return self._script2_return
    
    def _close_prog_by_pid(self, _pid):
        try:
            process = psutil.Process(_pid)
            for ps_proc in process.children(recursive=True):
                # ps_proc.kill()
                ps_proc.terminate()
            process.kill()
        except:
            pass
            
    # def _close_prog_by_pid1(self, _pid):
        # try:
            # list_pid = check_output("pstree -p {} | grep -oP '\(\K[^\)]+'".format(_pid), shell=True, universal_newlines=True).split("\n")
            # list_pid.remove('')
        # except:
            # return
        # for _p in list_pid:
            # try:
                # os.system(f"kill -9 {_p}")
            # except:
                # continue
    
    def terminate_thread(self,_t):
        if _t == 1 or _t == None:
            if self.script1_id:
                self.label1.set_text('')
                GLib.source_remove(self.script1_id)
            self._script1_return = False
            if self.q1 != None:
                if not self.q1.empty():
                    _p1 = self.q1.get()
                    self._close_prog_by_pid(_p1.pid)
                    # fork()
                    if self.thread_label1 != None:
                        del self.thread_label1
                        self.thread_label1 = None
                    if self.event1 != None and not self.event1.is_set():
                        self.event1.set()
        if _t == 2 or _t == None:
            if self.script2_id:
                self.label2.set_text('')
                GLib.source_remove(self.script2_id)
            self._script2_return = False
            if self.q2 != None:
                if not self.q2.empty():
                    _p2 = self.q2.get()
                    self._close_prog_by_pid(_p2.pid)
                    if self.thread_label2 != None:
                        del self.thread_label2
                        self.thread_label2 = None
                    if self.event2 != None and not self.event2.is_set():
                        self.event2.set()
    
    def _to_close(self, w=None, e=None):
        self.terminate_thread(None)
        if self.ClipDaemon:
            self.ClipDaemon._stop()
        Gtk.main_quit()
        
    def on_clock(self):
        if self._timer:
            self.set_on_clock()
        return self._timer
    
    def set_on_clock(self):
        if self.time_format == 0:
            self.clock_lbl.set_label(time.strftime('%H:%M'))
        else:
        # elif self.time_format == 1:
            # self.clock_lbl.set_label(time.strftime('%I:%M%p'))
            _am_pm = ""
            try:
                ____what = int(time.strftime('%H'))
                if self.time_format == 1:
                    if 11 < ____what < 23:
                        _am_pm = " pm"
                    else:
                        _am_pm = " am"
                elif self.time_format == 2:
                    if ____what > 12:
                        _am_pm = " pm"
                    else:
                        _am_pm = " am"
            except:
                _am_pm = ""
            self.clock_lbl.set_label(time.strftime('%I:%M')+_am_pm)
    
    def on_set_clipboard(self, _pos):
        self.clipbutton = Gtk.EventBox()
        _icon_path = os.path.join(_curr_dir,"icons","clipboard.svg")
        _pixbf = GdkPixbuf.Pixbuf.new_from_file_at_size(_icon_path, self.win_height,self.win_height)
        _img = Gtk.Image.new_from_pixbuf(_pixbf)
        self.clipbutton.add(_img)
        self.clipbutton.connect('button-press-event', self.on_clipboard_button)
        self.right_box.pack_end(self.clipbutton,False,False,4)
        # reorder
        if _pos != None:
            self.right_box.reorder_child(self.clipbutton, _pos)
            self.right_box.show_all()
        
    
    def on_set_clock2(self, _pos):
        self.temp_clock = None
        self._timer = True
        # self.clock_lbl = Gtk.Label(label="")
        self.clock_lbl.show()
        self.set_on_clock()
        # self.clock_lbl_style_context = self.clock_lbl.get_style_context()
        # self.clock_lbl_style_context.add_class("clocklabel")
        # if _pos == 1:
            # self.center_box.pack_start(self.clock_lbl,False,False,10)
        # elif _pos == 2:
            # self.right_box.pack_end(self.clock_lbl,False,False,10)
        self._t_id = GLib.timeout_add(60000, self.on_clock)
        # # reorder
        # if _pos != None:
            # self.center_box.reorder_child(self.clock_lbl, _pos)
            # self.center_box.show_all()
    
    def load_conf(self):
        if not os.path.exists(_panelconf):
            _data_json = _starting_conf
            _ff = open(_panelconf, "w")  
            json.dump(_data_json, _ff, indent = 4)  
            _ff.close()
        _ff = open(_panelconf, "r")
        self._configuration = json.load(_ff)
        _ff.close()
    
    def on_save_optional_widget_state(self):
        if self.temp_clock != None:
            self._configuration["panel"]["clock"] = int(self.temp_clock)
            self.clock_use = self.temp_clock
            self.temp_clock = None
            if self.clock_use == 0:
                self._timer = False
                # self.center_box.remove(self.clock_lbl)
                self.clock_lbl.set_label("")
                self.clock_lbl.hide()
                if self._t_id:
                    GLib.source_remove(self._t_id)
                    self._t_id = None
            elif self.clock_use == 1:
                self.on_set_clock2(0)
        
        if self.temp_clip != None:
            self._configuration["panel"]["clipboard"] = int(self.temp_clip)
            self.clipboard_use = self.temp_clip
            self.temp_clip = None
            if self.clipboard_use == 0:
                self.right_box.remove(self.clipbutton)
                del self.clipbutton
                if is_wayland:
                    try:
                        os.system("killall wl-paste")
                    except:
                        pass
            elif self.clipboard_use == 1:
                self.on_set_clipboard(5)
        
        if self.temp_out1 != None:
            self._configuration["panel"]["label1"] = int(self.temp_out1)
            self.label1_use = self.temp_out1
            self.temp_out1 = None
            if self.label1_use == 0:
                self.label1.set_label("")
            elif self.label1_use == 1:
                self.label1.set_label("label1")
        
        if self.temp_out2 != None:
            self._configuration["panel"]["label2"] = int(self.temp_out2)
            self.label2_use = self.temp_out2
            self.temp_out2 = None
            if self.label2_use == 0:
                self.label2.set_label("")
            elif self.label2_use == 1:
                self.label2.set_label("label2")
        
    def save_conf(self):
        # panel
        _ff = open(_panelconf, "w")  
        json.dump(self._configuration, _ff, indent = 4)  
        _ff.close()
        # menu
        _ff = open(_menu_config_file, "w")  
        json.dump(self.menu_conf, _ff, indent = 4)  
        _ff.close()
        # service
        _ff = open(_service_config_file, "w")  
        json.dump(self.service_conf, _ff, indent = 4)  
        _ff.close()
        # clipboard
        _ff = open(_clipboard_config_file, "w")  
        json.dump(self.clipboard_conf, _ff, indent = 4)  
        _ff.close()
        # notificaitions
        _ff = open(_notification_config_file, "w")  
        json.dump(self.notification_conf, _ff, indent = 4)  
        _ff.close()
    
    ### menu w h ci ii ls
    def set_menu_cp(self, _type, _value):
        if _type == "w":
            self.menu_width_tmp = _value
        elif _type == "h":
            self.menu_height_tmp = _value
        elif _type == "ci":
           self.menu_cat_icon_size_tmp  = _value
        elif _type == "ii":
            self.menu_item_icon_size_tmp = _value
        elif _type == "iw":
            self.menu_item_width_tmp = _value
        elif _type == "ls":
            self.menu_live_search_tmp = _value
        
    def entry_menu(self, _type, _value):
        if _type == "t":
            self.menu_terminal_tmp = _value
        elif _type == "me":
            self.menu_editor_tmp = _value
        
    def on_menu_win_position(self, _type, _value):
        if _type == "pos":
            self.menu_win_position_tmp = _value
    
    def set_width_size(self, panel_width):
        self.win_width = int(panel_width)
        self._configuration["panel"]["width"] = self.win_width
        screen_width = self._monitor.get_geometry().width
        self.set_size_request(screen_width-self.win_width,self.win_height)
    
    def set_self_size(self, panel_height):
        self.win_height = int(panel_height)
        self._configuration["panel"]["height"] = self.win_height
        screen_width = self._monitor.get_geometry().width
        self.set_size_request(screen_width-self.win_width,self.win_height)
    
    def set_self_corners(self, _pos, _r):
        # corner-top
        if _pos == 0:
            self._corner_top = int(_r)
            self._configuration["panel"]["corner-top"] = self._corner_top
        # corner-bottom
        elif _pos == 1:
            self._corner_bottom = int(_r)
            self._configuration["panel"]["corner-bottom"] = self._corner_bottom
        css = ".mywindow { border-radius: "+str(self._corner_top)+"px "+str(self._corner_top)+"px "+str(self._corner_bottom)+"px "+str(self._corner_bottom)+"px; }"
        self.style_provider.load_from_data(css.encode('utf-8'))
        
    def on_set_win_position(self, _pos):
        if _pos == 1:
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, 0)
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.BOTTOM, 1)
        elif _pos == 0:
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.BOTTOM, 0)
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, 1)
    
    def set_win_position(self, _pos):
        if _pos != self.win_position:
            self.win_position = int(_pos)
            self.on_set_win_position(self.win_position)
    
    def on_time_combo(self, _type):
        if self.clock_use:
            self.time_format = _type
    
    def set_volume_entry(self, _text):
        self.volume_command_tmp = _text
    
    def on_switch_btn(self, _n, _state):
        if _n == "clipboard":
            self.temp_clip = _state
        elif _n == "clock":
            self.temp_clock = _state
        elif _n == "out1":
            self.temp_out1 = _state
        elif _n == "out2":
            self.temp_out2 = _state
        elif _n == "task":
            self.temp_task = _state
        elif _n == "notification":
            self.notification_conf["use_this"] = int(_state)
            self.not_use = int(_state)
    
    def set_not_window_size(self, _type, _value):
        if _type == "w":
            self.not_width_tmp = int(_value)
        elif _type == "h":
            self.not_height_tmp = int(_value)
        elif _type == "i":
            self.not_icon_size_tmp = int(_value)
        elif _type == "l":
            self.not_bottom_limit_tmp = int(_value)
    
    def set_service_window_size(self, _type, _value):
        if _type == "w":
            self.service_width_tmp = int(_value)
        elif _type == "h":
            self.service_height_tmp = int(_value)
            
    # def set_timer_combo(self, _type):
        # self.service_sound_player_tmp = _type
    
    # def entry_timer_text(self, _text):
        # self.service_player_tmp = _text
    
    def entry_commands(self, _text, _type):
        if _type == "l":
            self._logout_tmp = _text
        elif _type == "r":
            self._reboot_tmp = _text
        elif _type == "s":
            self._shutdown_tmp = _text
    
    def set_note_window_size(self, _type, _value):
        if _type == "w":
            self.note_width_tmp = int(_value)
        elif _type == "h":
            self.note_height_tmp = int(_value)
    
    def set_clip_window_size(self, _type, _value):
        if _type == "w":
            self.clip_width_tmp = int(_value)
        elif _type == "h":
            self.clip_height_tmp = int(_value)
    
    def set_clip_type(self, _type, _value):
        if _type == "chars":
            self.clip_max_chars_tmp = _value
        elif _type == "clips":
            self.clip_max_clips_tmp = _value
        elif _type == "cp":
            self.chars_preview_tmp = _value
    
    def onclip_do_not_disturb(self, _state):
        self.clip_do_not_track = _state
        if self.clip_do_not_track:
            try:
                _file = os.path.join(_curr_dir,"donotdisturb.mode")
                f = open(_file, "w")
                f.close()
            except:
                pass
        else:
            try:
                _file = os.path.join(_curr_dir,"donotdisturb.mode")
                os.remove(_file)
            except:
                pass
    
    # 0 not active - 1 not active for urgent - 2 always active
    def set_dnd_combo(self, _type):
        self.not_dnd_tmp = _type
    
    def set_sound_combo(self, _id):
        if _id == 2:
            self.not_sounds_tmp = _id
        else:
            self.not_sounds_tmp = _id
    
    # the menu window
    def on_button1_clicked(self, widget, event):
        if self.menu_win_position in [0,1]:
            self.open_menu_win()
        elif self.menu_win_position == 2:
            self.open_service_win()
    
    def open_menu_win(self):
        # close the service window
        if self.OW:
            self.OW.close()
            self.OW = None
        
        if self.MW:
            isVisible = self.MW.get_property("visible")
            if self.MW.get_realized() and not self.MW.get_property("visible"):
                self.MW.show()
            elif self.MW.get_realized() and self.MW.get_property("visible"):
                self.MW.hide()
        else:
            self.MW = menuWin(self)
    
    def f_on_set_timer(self,_play_sound,_dialog):
        if _play_sound:
            _sound = os.path.join(_curr_dir,"sounds","timer.wav")
            if not self.entry_sound_text:
                try:
                    ctx = GSound.Context()
                    ctx.init()
                    ret = ctx.play_full({GSound.ATTR_EVENT_ID: _sound})
                    if ret == None:
                        ret = ctx.play_full({GSound.ATTR_MEDIA_FILENAME: _sound})
                except:
                    pass
            else:
                _player = self.entry_sound_text
                try:
                    os.system("{0} {1} &".format(_player, _sound))
                except:
                    pass
                    
        if _dialog:
            self._message_dialog_yes("Timer!")
        
        self._is_timer_set = 0
        self.timer_id = None
        return False
    
    def on_set_timer(self, _value):
        if self.OW:
            self.OW.close()
            self.OW = None
        dialog = timerDialog(self)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            (_min,_sound,_dialog) = dialog._values
            self.timer_id = GLib.timeout_add_seconds(_min*60, self.f_on_set_timer, _sound, _dialog)
            self._is_timer_set = 1
        elif response == Gtk.ResponseType.CANCEL:
            pass
        dialog.destroy()
    
    def on_button_conf_clicked(self, widget):
        dialog = DialogConfiguration(self)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            old_pos = self._configuration["panel"]["position"]
            if old_pos != self.win_position:
                self._configuration["panel"]["position"] = self.win_position
            # menu
            if self.MW:
                self.MW.close()
                self.MW = None
            # service
            if self.OW:
                self.OW.close()
                self.OW = None
            # clipboard
            if self.CW:
                self.CW.close()
                self.CW = None
            
            ## MENU
            if self.menu_width_tmp != 0:
                self.menu_width = self.menu_width_tmp
                self.menu_conf["wwidth"] = self.menu_width
                self.menu_width_tmp = 0
            if self.menu_height_tmp != 0:
                self.menu_height = self.menu_height_tmp
                self.menu_conf["wheight"] = self.menu_height
                self.menu_height_tmp = 0
            if self.menu_terminal_tmp != None:
                self.menu_terminal = self.menu_terminal_tmp
                self.menu_conf["terminal"] = self.menu_terminal
                self.menu_terminal_tmp = None
            if self.menu_cat_icon_size_tmp != 0:
                self.menu_cat_icon_size = self.menu_cat_icon_size_tmp
                self.menu_conf["cat_icon_size"] = self.menu_cat_icon_size
                self.menu_cat_icon_size_tmp = 0
            if self.menu_item_icon_size_tmp != 0:
                self.menu_item_icon_size = self.menu_item_icon_size_tmp
                self.menu_conf["item_icon_size"] = self.menu_item_icon_size
                self.menu_item_icon_size_tmp = 0
            if self.menu_item_width_tmp != None:
                self.menu_item_width = self.menu_item_width_tmp
                self.menu_conf["item_width"] = self.menu_item_width
                self.menu_item_width_tmp = None
            if self.menu_live_search_tmp != None:
                self.menu_live_search = self.menu_live_search_tmp
                self.menu_conf["live_search"] = self.menu_live_search
                self.menu_live_search_tmp = None
            if self.menu_win_position_tmp != None:
                self.menu_win_position = self.menu_win_position_tmp
                self.menu_conf["win_position"] = self.menu_win_position
                self.menu_win_position_tmp = None
            if self.menu_editor_tmp != None:
                self.menu_editor = self.menu_editor_tmp
                self.menu_conf["menu_editor"] = self.menu_editor
                self.menu_editor_tmp = None
            
            ## SERVICE
            if self.service_width_tmp != self.service_width:
                self.service_width = self.service_width_tmp
                self.service_conf["wwidth"] = self.service_width
                self.service_width_tmp = 0
            if self.service_height_tmp != self.service_height:
                self.service_height = self.service_height_tmp
                self.service_conf["wheight"] = self.service_height
                self.service_height_tmp = 0
            # if self.service_sound_player_tmp != self.service_sound_player:
                # self.service_sound_player = self.service_sound_player_tmp
                # self.service_conf["sound-player"] = self.service_sound_player
                # self.service_sound_player_tmp = None
            # if self.service_player_tmp != self.service_player:
                # self.service_player = self.service_player_tmp
                # self.service_conf["player"] = self.service_player
                # self.service_player_tmp = ""
            if self._logout_tmp != None:
                self._logout = self._logout_tmp
                self.service_conf["logout"] = self._logout
                self._logout_tmp = None
            if self._reboot_tmp != None:
                self._reboot = self._reboot_tmp
                self.service_conf["reboot"] = self._reboot
                self._reboot_tmp = None
            if self._shutdown_tmp != None:
                self._shutdown = self._shutdown_tmp
                self.service_conf["shutdown"] = self._shutdown
                self._shutdown_tmp = None
            if self.note_width_tmp != None:
                self.note_width = self.note_width_tmp
                self.service_conf["note-width"] = self.note_width
                self.note_width_tmp = None
            if self.note_height_tmp != None:
                self.note_height = self.note_height_tmp
                self.service_conf["note-height"] = self.note_height
                self.note_height_tmp = None
            
            ## PANEL
            if self.temp_clip == False:
                if self.ClipDaemon:
                    self.ClipDaemon._stop()
                    self.ClipDaemon = None
                try:
                    os.system("killall wl-paste")
                except:
                    pass
            elif self.temp_clip == True:
                if self.ClipDaemon == None:
                    _ret = self.clipboard_ready()
                    if _ret:
                        self.ClipDaemon = daemonClipW(self.clips_path, self)
                        self.ClipDaemon._start()
                    else:
                        _error_log("Something wrong with wl-paste or wclipboard.py or something else.")
            if self.temp_out1 != None and self.temp_out1 != self.label1_use:
                self.label1_use = int(self.temp_out1)
                self.temp_out1 = None
                self._configuration["panel"]["label1"] = self.label1_use
                self.terminate_thread(1)
                self.set_timer_label1()
            if self.temp_out2 != None and self.temp_out2 != self.label2_use:
                self.label2_use = int(self.temp_out2)
                self.temp_out2 = None
                self._configuration["panel"]["label2"] = self.label2_use
                self.terminate_thread(2)
                self.set_timer_label2()
            # time format
            if self.clock_use:
                self._configuration["panel"]["time_format"] = self.time_format
                self._timer = False
                if self._t_id:
                    GLib.source_remove(self._t_id)
                    self._t_id = None
                # # self._t_id is True when starts again
                # self.set_on_clock()
                # self._t_id = GLib.timeout_add(60000, self.on_clock)
            # volume application
            if self.volume_command_tmp != self.volume_command:
                if self.volume_command_tmp == None:
                    pass
                else:
                    self.volume_command = self.volume_command_tmp
                self._configuration["panel"]["volume_command"] = self.volume_command
                self.volume_command_tmp = None
            
            ## CLIPBOARD
            if self.clip_width_tmp != 0:
                if self.CW:
                    self.CW.close()
                    self.CW = None
                self.clipboard_conf["wwidth"] = self.clip_width_tmp
                self.clip_width = self.clip_width_tmp
                self.clip_width_tmp = 0
            if self.clip_height_tmp != 0:
                if self.CW:
                    self.CW.close()
                    self.CW = None
                self.clipboard_conf["wheight"] = self.clip_height_tmp
                self.clip_height = self.clip_height_tmp
                self.clip_height_tmp = 0
            if self.clip_max_chars_tmp != 0:
                if self.CW:
                    self.CW.close()
                    self.CW = None
                self.clipboard_conf["max_chars"] = self.clip_max_chars_tmp
                self.clip_max_chars = self.clip_max_chars_tmp
                self.clip_max_chars_tmp = 0
            if self.clip_max_clips_tmp != 0:
                if self.CW:
                    self.CW.close()
                    self.CW = None
                self.clipboard_conf["max_clips"] = self.clip_max_clips_tmp
                self.clip_max_clips = self.clip_max_clips_tmp
                self.clip_max_clips_tmp = 0
            if self.chars_preview_tmp != 0:
                if self.CW:
                    self.CW.close()
                    self.CW = None
                self.clipboard_conf["chars_preview"] = self.chars_preview_tmp
                self.chars_preview = self.chars_preview_tmp
                self.chars_preview_tmp = 0
            
            ## NOTIFICATIONS
            if self.not_width_tmp != 0:
                self.notification_conf["nwidth"] = self.not_width_tmp
                self.not_width = self.not_width_tmp
                self.not_width_tmp = 0
            if self.not_height_tmp != 0:
                self.notification_conf["nheight"] = self.not_height_tmp
                self.not_height = self.not_height_tmp
                self.not_height_tmp = 0
            if self.not_icon_size_tmp != 0:
                self.notification_conf["icon_size"] = self.not_icon_size_tmp
                self.not_icon_size = self.not_icon_size_tmp
                self.not_icon_size_tmp = 0
            if self.not_bottom_limit_tmp > -1:
                self.notification_conf["bottom_limit"] = self.not_bottom_limit_tmp
                self.not_bottom_limit = self.not_bottom_limit_tmp
                self.not_bottom_limit_tmp = -1
            if self.not_dnd_tmp != -1:
                self.notification_conf["dnd"] = self.not_dnd_tmp
                self.not_dnd = self.not_dnd_tmp
                self.not_dnd_tmp = -1
            if self.not_sounds_tmp != -1:
                if self.not_sounds_tmp in [0,1]:
                    _type = self.not_sounds_tmp
                elif self.not_sounds_tmp == 2 and self.entry_sound_text != "":
                    _type = self.entry_sound_text
                else:
                     _type = 0
                self.notification_conf["sound_play"] = _type
                self.not_sounds = _type
                self.not_sounds_tmp = -1
            #
            self.notification_conf["skip_apps"] = self.skip_apps
            if self.skip_apps != "":
                self._SKIP_APPS = self.skip_apps.split(",")
            else:
                self._SKIP_APPS = []
            
            self.on_save_optional_widget_state()
            self.save_conf()
        elif response == Gtk.ResponseType.CANCEL:
            self.on_close_dialog_conf()
        dialog.destroy()
    
    def on_close_dialog_conf(self):
        old_pos = self._configuration["panel"]["position"]
        if old_pos != self.win_position:
            self.win_position = old_pos
            self.on_set_win_position(self.win_position)
            self.temp_clip = None
            self.temp_clock = None
            self.temp_out1 = None
            self.temp_out2 = None
            self.temp_task = None
            if self.clock_use:
                self.time_format = self._configuration["panel"]["time_format"]
            
            self.volume_command_tmp = None
            
            self.menu_width_tmp = 0
            self.menu_height_tmp = 0
            self.menu_terminal_tmp = None
            self.menu_cat_icon_size_tmp = 0
            self.menu_item_icon_size_tmp = 0
            self.menu_item_width_tmp = None
            self.menu_live_search_tmp = None
            self.menu_win_position_tmp = None
            self.menu_editor_tmp = None
            
            self.service_width_tmp = 0
            self.service_height_tmp = 0
            # self.service_sound_player_tmp = None
            # self.service_player_tmp = ""
            self._logout_tmp = None
            self._reboot_tmp = None
            self._shutdown_tmp = None
            self.note_width_tmp = None
            self.note_height_tmp = None
            
            self.clip_width_tmp = 0
            self.clip_height_tmp = 0
            self.clip_max_chars_tmp = 0
            self.clip_max_clips_tmp = 0
            self.chars_preview_tmp = 0
            self.not_width_tmp = 0
            self.not_height_tmp = 0
            self.not_icon_size_tmp = 0
            self.not_bottom_limit_tmp = -1
            self.not_dnd_tmp = -1
            self.not_sounds_tmp = -1
            #
            self.skip_apps = self.notification_conf["skip_apps"]
    
    def on_other_button(self, btn, event):
        if self.menu_win_position in [0,1]:
            self.open_service_win()
        elif self.menu_win_position == 2:
            self.open_menu_win()
    
    def open_service_win(self):
        if self.OW:
            isVisible = self.OW.get_property("visible")
            if self.OW.get_realized() and not self.OW.get_property("visible"):
                self.OW.show()
            elif self.OW.get_realized() and self.OW.get_property("visible"):
                # self.OW.hide()
                self.OW.close()
                self.OW = None
        else:
            self.OW = otherWin(self)
            
    def on_clipboard_button(self, btn, event):
        # close the service window
        if self.OW:
            self.OW.close()
            self.OW = None
        
        if self.CW:
            isVisible = self.CW.get_property("visible")
            if self.CW.get_realized() and not self.CW.get_property("visible"):
                self.CW.show()
            elif self.CW.get_realized() and self.CW.get_property("visible"):
                if is_wayland:
                    self.CW.close()
                    self.CW = None
        else:
            self.CW = clipboardWin(self)

# logout/reboot/shutdonw window
class commandWin(Gtk.Window):
    def __init__(self, _parent, _command):
        super().__init__()
        
        self._parent = _parent
        self._command = _command
        
        self.set_transient_for(self._parent._parent)
        self.set_modal(True)
        
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_namespace(self, "commandwin")
        
        # self.connect('focus-out-event', self.on_focus_out)
        
        self.self_style_context = self.get_style_context()
        self.self_style_context.add_class("commandwin")
        
        _pad1 = 10
        self.main_box = Gtk.Box.new(orientation=Gtk.Orientation.VERTICAL,spacing=_pad1)
        self.main_box.set_margin_start(_pad1)
        self.main_box.set_margin_end(_pad1)
        self.add(self.main_box)
        
        # button box
        self.bbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.bbox.set_homogeneous(homogeneous=True)
        self.main_box.pack_start(self.bbox, True, False, _pad1)
        #
        
        c_btn = Gtk.Button.new()
        c_btn.set_relief(Gtk.ReliefStyle.NONE)
        self.bbox.add(c_btn)
        
        if self._command == "logout":
            c_btn.set_label(LOGOUTQ)
            c_btn.connect('clicked',self.on_c_btn, "logout")
        elif self._command == "restart":
            c_btn.set_label(RESTARTQ)
            c_btn.connect('clicked',self.on_c_btn, "restart")
        elif self._command == "shutdown":
            c_btn.set_label(SHUTDOWNQ)
            c_btn.connect('clicked',self.on_c_btn, "shutdown")
        # close this program
        elif self._command == "exit":
            c_btn.set_label(EXITQ)
            c_btn.connect('clicked',self.on_c_btn, "exit")
        
        _cancel_btn = Gtk.Button(label="Cancel")
        _cancel_btn.set_relief(Gtk.ReliefStyle.NONE)
        _cancel_btn.connect('clicked', self.on_cancel)
        self.bbox.add(_cancel_btn)
        
        self.show_all()
        self._parent.hide()
        
    def on_c_btn(self, btn, _type):
        try:
            _f = None
            if _type == "logout":
                _f = self._parent._parent._logout
            elif _type == "restart":
                _f = self._parent._parent._reboot
            elif _type == "shutdown":
                _f = self._parent._parent._shutdown
            elif _type == "exit":
                self._parent._parent._to_close()
            #
            
            if _f:
                os.system(f"{_f} &")
            
        except:
            pass
        self.close()
    
    def on_cancel(self, btn):
        self.close()
    
    # def on_focus_out(self, win, event):
        # # self.close()


class menuWin(Gtk.Window):
    def __init__(self, parent):
        super().__init__()
        
        self._parent = parent
        
        self.set_transient_for(self._parent)
        # self.set_modal(True)
        
        _win_pos = self._parent.win_position
        
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_namespace(self, "menuwin")
        
        if _win_pos == 1:
            if self._parent.menu_win_position == 0:
                GtkLayerShell.set_margin(self, GtkLayerShell.Edge.LEFT, 10)
                GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.LEFT, 1)
            elif self._parent.menu_win_position == 2:
                GtkLayerShell.set_margin(self, GtkLayerShell.Edge.RIGHT, 10)
                GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, 1)
            GtkLayerShell.set_margin(self, GtkLayerShell.Edge.BOTTOM, 10)
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.BOTTOM, 1)
        else:
            if self._parent.menu_win_position == 0:
                GtkLayerShell.set_margin(self, GtkLayerShell.Edge.LEFT, 10)
                GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.LEFT, 1)
            elif self._parent.menu_win_position == 2:
                GtkLayerShell.set_margin(self, GtkLayerShell.Edge.RIGHT, 10)
                GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, 1)
            GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, 10)
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, 1)
        
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.ON_DEMAND)
        
        self.connect('focus-out-event', self.on_focus_out)
        # self.connect('show', self.on_show)
        
        self.set_size_request(self._parent.menu_width, self._parent.menu_height)
        
        # 
        self.MM = None
        
        self.main_box = Gtk.Box.new(1,0)
        self.main_box.set_margin_start(_pad)
        self.main_box.set_margin_end(_pad)
        self.add(self.main_box)
        
        self.self_style_context = self.get_style_context()
        self.self_style_context.add_class("menuwin")
        
        ###############
        self.q = qq
        self.q.queue.clear()
        
        self.BTN_ICON_SIZE = self._parent.menu_cat_icon_size
        self.ICON_SIZE = self._parent.menu_item_icon_size
        
        # category box
        self.cbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.cbox.set_homogeneous(True)
        self.main_box.pack_start(self.cbox, False, False, 4)
        
        # # separator
        # separator = Gtk.Separator()
        # separator.set_orientation(Gtk.Orientation.HORIZONTAL)
        # self.main_box.pack_start(separator, False, False, 4)
        
        # iconview
        self.ivbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.ivbox.set_homogeneous(True)
        self.ivbox.set_hexpand(True)
        self.ivbox.set_vexpand(True)
        self.main_box.pack_start(self.ivbox, True, True, 0)
        
        # scrolled window
        self.scrolledwindow = Gtk.ScrolledWindow()
        self.scrolledwindow.set_hexpand(True)
        self.scrolledwindow.set_vexpand(True)
        self.scrolledwindow.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scrolledwindow.set_placement(Gtk.CornerType.TOP_LEFT)
        self.ivbox.pack_start(self.scrolledwindow, True, True, 0)
        
        # icon name comment exec path appinfo
        self.liststore = Gtk.ListStore(GdkPixbuf.Pixbuf, str, str, str, str, object)
        
        self.iconview = Gtk.IconView.new()
        self.iconview.set_model(self.liststore)
        self.iconview.set_pixbuf_column(0)
        self.iconview.set_text_column(1)
        self.iconview.set_tooltip_column(2)
        # self.iconview.set_hexpand(True)
        # self.iconview.set_vexpand(True)
        self.iconview.set_selection_mode(Gtk.SelectionMode.SINGLE)
        # each column size
        if self._parent.menu_item_width > 0:
            self.iconview.set_item_width(self._parent.menu_item_width)
        
        if DOUBLE_CLICK == 0:
            self.iconview.set_activate_on_single_click(True)
        self.iconview.set_name("myiconview")
        #
        target_entry = Gtk.TargetEntry.new('calculon', 1, 999)
        # self.DRAG_ACTION = Gdk.DragAction.MOVE
        self.DRAG_ACTION = Gdk.DragAction.COPY
        self._start_path = None
        self.iconview.enable_model_drag_source(Gdk.ModifierType.BUTTON1_MASK, [target_entry], self.DRAG_ACTION)
        self.iconview.enable_model_drag_dest([target_entry], self.DRAG_ACTION)
        self.iconview.connect("drag-data-get", self.on_drag_data_get)
        self.iconview.connect("drag-data-received", self.on_drag_data_received)
        #
        self.iconview.connect("item-activated", self.on_iv_item_activated)
        self.iconview.connect("button_press_event", self.mouse_event)
        self.scrolledwindow.add(self.iconview)
        # separator
        separator = Gtk.Separator()
        separator.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.main_box.pack_start(separator, False, False, 4)
        # search box
        self.scbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.scbox.set_homogeneous(True)
        #
        self.search_bar = Gtk.SearchBar()
        self.search_bar.set_search_mode(True)
        self.searchentry = Gtk.SearchEntry()
        self.searchentry.connect('icon-press', self.on_icon_press)
        self.searchentry.connect('activate', self.on_search_return)
        self.searchentry.set_name("mysearchentry")
        if self._parent.menu_live_search > 0 :
            self.searchentry.connect('changed', self.on_search)
        self.search_bar.connect_entry(self.searchentry)
        # Get the correct children into the right variables
        _search_main_box = self.search_bar.get_children()[0].get_children()[0]
        box1, box2, box3 = _search_main_box.get_children()
        # 
        box2.props.hexpand = True
        box2.props.halign = Gtk.Align.FILL
        _search_main_box.remove(box1)
        box3.props.hexpand = False
        ###########
        self.search_bar.add(self.searchentry)
        self.search_bar.set_show_close_button(False)
        self.search_bar.set_visible(True)
        self.search_bar.set_search_mode(True)
        self.scbox.pack_start(self.search_bar, False, True, 0)
        self.main_box.pack_start(self.scbox, False, True, 0)
        
        # # separator
        # separator = Gtk.Separator()
        # separator.set_orientation(Gtk.Orientation.HORIZONTAL)
        # self.main_box.pack_start(separator, False, False, 4)
        
        # service buttons
        self.btn_box = Gtk.Box.new(0,0)
        self.main_box.pack_start(self.btn_box,False,False,0)
        self.btn_box.set_halign(2)
        
        # self.prog_modify_menu = None
        # _prog_modify_menu_path = os.path.join(_curr_dir,"menu_editor")
        # if os.path.exists(_prog_modify_menu_path):
            # self.prog_modify_menu = _prog_modify_menu_path
        # menu editor button
        self.modify_menu = Gtk.Button()
        pix = GdkPixbuf.Pixbuf.new_from_file_at_size(os.path.join(_curr_dir,"icons","modify_menu.svg"), int(self.BTN_ICON_SIZE/2), int(self.BTN_ICON_SIZE/2))
        _image = Gtk.Image.new_from_pixbuf(pix)
        self.modify_menu.set_image(_image)
        self.modify_menu.set_relief(Gtk.ReliefStyle.NONE)
        self.modify_menu.set_tooltip_text(MODIFY_MENU)
        self.modify_menu.connect('clicked', self.on_modify_menu)
        self.btn_box.pack_start(self.modify_menu,True,False,4)
        
        self.logout_btn = Gtk.Button()
        pix = GdkPixbuf.Pixbuf.new_from_file_at_size(os.path.join(_curr_dir,"icons","system-logout.svg"), int(self.BTN_ICON_SIZE/2), int(self.BTN_ICON_SIZE/2))
        _image = Gtk.Image.new_from_pixbuf(pix)
        self.logout_btn.set_image(_image)
        self.logout_btn.set_relief(Gtk.ReliefStyle.NONE)
        self.logout_btn.set_tooltip_text(LOGOUT)
        self.logout_btn.connect('clicked', self.on_service_btn, "logout")
        self.btn_box.pack_start(self.logout_btn,True,False,4)
        
        self.reboot_btn = Gtk.Button()
        pix = GdkPixbuf.Pixbuf.new_from_file_at_size(os.path.join(_curr_dir,"icons","system-restart.svg"), int(self.BTN_ICON_SIZE/2), int(self.BTN_ICON_SIZE/2))
        _image = Gtk.Image.new_from_pixbuf(pix)
        self.reboot_btn.set_image(_image)
        self.reboot_btn.set_relief(Gtk.ReliefStyle.NONE)
        self.reboot_btn.set_tooltip_text(RESTART)
        self.reboot_btn.connect('clicked', self.on_service_btn, "restart")
        self.btn_box.pack_start(self.reboot_btn,True,False,4)
        
        self.shutdown_btn = Gtk.Button()
        pix = GdkPixbuf.Pixbuf.new_from_file_at_size(os.path.join(_curr_dir,"icons","system-shutdown.svg"), int(self.BTN_ICON_SIZE/2), int(self.BTN_ICON_SIZE/2))
        _image = Gtk.Image.new_from_pixbuf(pix)
        self.shutdown_btn.set_image(_image)
        self.shutdown_btn.set_tooltip_text(SHUTDOWN)
        self.shutdown_btn.set_relief(Gtk.ReliefStyle.NONE)
        self.shutdown_btn.connect('clicked', self.on_service_btn, "shutdown")
        self.btn_box.pack_start(self.shutdown_btn,True,False,4)
        
        # the bookmark button
        self.btn_bookmark = None
        # the last category button pressed
        self._btn_toggled = None
        # populate the menu
        self.q.put_nowait("new")
        # self.on_populate_menu()
        # populate categories
        self.bookmarks = []
        self.set_categories()
        
        ###########
        
        self.show_all()
        
        if self._parent.menu_editor != "_internal_" and (self._parent.menu_editor == "" or not shutil.which(self._parent.menu_editor)):
            self.modify_menu.hide()
    
    def on_modify_menu(self, btn):
        _l = self.iconview.get_selected_items()
        if _l == []:
            try:
                if self._parent.menu_editor == "_internal_":
                    _cmd = [os.path.join(_curr_dir,"appmenu.py")]
                    Popen(_cmd, shell=False)
                else:
                    Popen(f"{self._parent.menu_editor}",shell=False)
            except:
                pass
            return
        # _category_selected = self.get_cat_btn_name(self._btn_toggled)
        _category_selected = btn.icat
        if _category_selected == "Bookmarks":
            return
        # if _l:
            # _path = _l[0]
            # # icon name comment exec path appinfo
            # _item = self.liststore[_path][4]
            # if os.path.exists(_item):
                # try:
                    # Popen(f"{self.prog_modify_menu} {_item}",shell=True)
                # except:
                    # pass
        
    
    def on_service_btn(self, btn, _type):
        try:
            commandWin(self,_type)
        except:
            pass
    
    def on_drag_data_get(self, widget, drag_context, data, info, time):
        if self._btn_toggled.icat == "Bookmarks":
            selected_path = widget.get_selected_items()[0]
            self._start_path = selected_path
    
    def on_drag_data_received(self, widget, drag_context, x, y, data, info, time):
        _dest_path = widget.get_path_at_pos(x,y)
        if _dest_path == None or self._start_path == None:
            return
        if _dest_path != self._start_path:
            _l = list(range(len(self.liststore)))
            _l.insert(_dest_path.get_indices()[0], _l.pop(self._start_path.get_indices()[0]))
            self.liststore.reorder(_l)
            # reset
            self.bookmarks = []
            # rewrite the favorites file
            _f = open(os.path.join(_curr_dir, "favorites"), "w")
            for row in self.liststore:
                _item = row[4]
                _f.write(_item)
                _f.write("\n")
                self.bookmarks.append(_item)
            _f.close()
        #
        self._start_path = None
        #
        return True
    
    def on_search_return(self, widget):
        self.on_button_search(widget)
    
    # def on_populate_menu(self):
        # _f_populate_menu()
    
    def rebuild_menu(self):
        if self._parent.MW:
            self._parent.MW.close()
            self._parent.MW = None
        _f_populate_menu()
        
    # on iconview
    def mouse_event(self, iv, event):
        # bookmarks
        # right mouse button
        if event.button == 3:
            _path = iv.get_path_at_pos(event.x, event.y)
            if _path != None:
                _item = self.liststore[_path][4]
                if self.MM == None:
                    self.MM = menuModify(self, _item)
                # # remove from bookmarks
                # if _item in self.bookmarks:
                    # if self._btn_toggled.icat != "Bookmarks":
                        # return
                    # dialog = ynDialog(self, "Delete from Bookmarks?", "Question")
                    # response = dialog.run()
                    # if response == Gtk.ResponseType.OK:
                        # _content = None
                        # try:
                            # self.bookmarks.remove(_item)
                            # with open(_menu_favorites, "w") as _f:
                                # for el in self.bookmarks:
                                    # _f.write(el+"\n")
                            # # rebuild bookmarks
                            # self.populate_bookmarks_at_start()
                            # self.populate_category("Bookmarks")
                        # except Exception as E:
                            # self.msg_simple("Error\n"+str(E))
                    # #
                    # dialog.destroy()
                    # self._parent.MW = None
                    # self.close()
                # # add to bookmarks
                # else:
                    # dialog = ynDialog(self, "Add to Bookmarks?", "Question")
                    # response = dialog.run()
                    # if response == Gtk.ResponseType.OK:
                        # _content = None
                        # try:
                            # with open(_menu_favorites, "a") as _f:
                                # _f.write(_item)
                                # _f.write("\n")
                            # # rebuild bookmarks
                            # self.populate_bookmarks_at_start()
                        # except Exception as E:
                            # self.msg_simple("Error\n"+str(E))
                    # dialog.destroy()
                    # self._parent.MW = None
                    # self.close()
        # central mouse button
        elif event.button == 2:
            dialog = ynDialog(self, "Rebuild the menu?", "Question")
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                self.rebuild_menu()
            dialog.destroy()
            self._parent.MW = None
            self.close()
    
    # clear icon pressed in the search entry
    def on_icon_press(self, w, p, e):
        if self._btn_toggled.icat == "Bookmarks":
            self.liststore.clear()
            self.populate_bookmarks()
    
    # application searching by pressing enter in the search entry
    def on_button_search(self, button=None):
        if len(self.searchentry.get_text()) < self._parent.menu_live_search:
            return
        else:
            if self._btn_toggled:
                if USER_THEME == 0:
                    self._btn_toggled.set_active(False)
                self._btn_toggled = None
            self.perform_searching(self.searchentry.get_text().lower())
        
    # application live searching in the search entry
    def on_search(self, _):
        if len(self.searchentry.get_text()) >= self._parent.menu_live_search:
            self.perform_searching(self.searchentry.get_text().lower())
        elif len(self.searchentry.get_text()) == 0:
            if self._btn_toggled.icat != None and self._btn_toggled.icat == "Bookmarks":
                self.liststore.clear()
                self.populate_bookmarks()
    
    def perform_searching(self, _text):
        if USER_THEME == 1 and USE_LABEL_CATEGORY == 1:
            self.clabel.set_label("Searching...")
        _cat = ["Development", "Game", "Education", "Graphics", "Multimedia", "Network", "Office", "Utility", "Settings", "System", "Other"]
        _list = []
        # [_el_name,_el_cat,_el_exec,_el_icon,_el_comment,_el_path,_el])
        for _el in the_menu:
            if _el[4]:
                if _text in _el[4].lower():
                    _list.append(_el[5])
                    continue
            if _el[0]:
                if _text in _el[0].lower():
                    if not _text in _list:
                        _list.append(_el[5])
                        continue
            if _el[2]:
                if _text in _el[2].lower():
                    if not _text in _list:
                        _list.append(_el[5])
                        continue
        
        if _list:
            self.f_on_pop_iv(_list)
    
    def f_on_pop_iv(self, _list):
        self.liststore.clear()
        for _item in _list:
            self.f_menu_item(_item)
        
    # populate the main categories at start
    def set_categories(self):
        self._btn_toggled = None
        #
        _cat = ["Bookmarks", "Development", "Game", "Education", "Graphics", "Multimedia", "Network", "Office", "Utility", "Settings", "System", "Other"]
        _icon = ["Bookmark.svg", "Development.svg", "Game.svg", "Education.svg", "Graphics.svg", "Multimedia.svg", "Network.svg", "Office.svg", "Utility.svg", "Settings.svg", "System.svg", "Other.svg",]
        for i,el in enumerate(_cat):
            if USER_THEME == 1:
                _btn = Gtk.Button()
                _btn.connect('clicked', self.on_toggle_toggled)
                _btn.connect('focus-in-event', self.on_toggle_toggled)
            elif USER_THEME == 0:
                _btn = Gtk.ToggleButton()
                _btn.set_can_focus(False)
                _btn.connect('button-release-event', self.on_toggle_toggled)
            _btn.set_name("mybutton")
            _btn.icat = el
            _btn.set_tooltip_text(el)
            pix = GdkPixbuf.Pixbuf.new_from_file_at_size("icons"+"/"+_icon[i], self.BTN_ICON_SIZE, self.BTN_ICON_SIZE)
            _image = Gtk.Image.new_from_pixbuf(pix)
            _btn.set_image(_image)
            _btn.set_image_position(Gtk.PositionType.TOP)
            _btn.set_always_show_image(True)
            _btn.set_events(Gdk.EventMask.BUTTON_RELEASE_MASK)
            self.cbox.add(_btn)
            #
            if i == 0:
                if USER_THEME == 0:
                    _btn.set_active(True)
                self._btn_toggled = _btn
                self.btn_bookmark = _btn
                self.populate_bookmarks_at_start()
                self.populate_category(el)
                if USER_THEME == 1 and USE_LABEL_CATEGORY == 1:
                    self.clabel.set_label("Bookmarks")
    
    def on_toggle_toggled(self, btn, e=None):
        self.searchentry.delete_text(0,-1)
        if btn.icat != "Bookmarks":
            self.search_bar.hide()
        else:
            self.search_bar.show()
        
        self.scrolledwindow.get_vadjustment().set_value(0)
        if USER_THEME == 1:
            self.populate_category(btn.icat)
            self._btn_toggled = btn
            if USE_LABEL_CATEGORY == 1:
                self.clabel.set_label(btn.icat)
            return
        if self._btn_toggled:
            if btn == self._btn_toggled:
                if e:
                    if e.button == 1:
                        btn.clicked()
                    else:
                        btn.set_active(True)
                return
            else:
                self._btn_toggled.set_active(False)
                if e and e.button != 1:
                    btn.set_active(True)
        #
        self.populate_category(btn.icat)
        self._btn_toggled = btn
    
    def populate_bookmarks_at_start(self):
        _content = None
        with open(_menu_favorites, "r") as _f:
            _content = _f.readlines()
        #
        self.bookmarks = []
        for el in _content:
            if el == "\n" or el == "" or el == None:
                continue
            self.bookmarks.append(el.strip("\n"))
        #
        self.populate_bookmarks()
    
    def populate_bookmarks(self):
        for eel in self.bookmarks:
            self.f_menu_item(eel)
    
    def f_menu_item(self, _item):
        try:
            _ap = Gio.DesktopAppInfo.new_from_filename(_item)
            _name = _ap.get_display_name()
            # executable
            _exec = _ap.get_executable()
            # comment
            _description = _ap.get_description() or None
            _path = _ap.get_filename()
            
            if not _name or not _exec or not _path:
                return
            
            _icon = _ap.get_icon()
            if _icon:
                if isinstance(_icon,Gio.ThemedIcon):
                    _icon = _icon.to_string()
                elif isinstance(_icon,Gio.FileIcon):
                    _icon = _icon.get_file().get_path()
            else:
                _icon = None
            
            if _icon != None:
                pixbuf = self._find_the_icon(_icon)
            # icon name comment exec path appinfo
            self.liststore.append([ pixbuf, _name, _description, _exec, _path, _ap ])
        except:
            return
        
    def populate_category(self, cat_name):
        self.liststore.clear()
        self.on_populate_category_main(cat_name)
    
    # [_name,_el_cat,_el_exec,_el_icon,_el_comment,_el_path,_el]
    def on_populate_category_main(self, cat_name):
        if cat_name == "Bookmarks":
            for _item in self.bookmarks:
                self.f_menu_item(_item)
            return
        for el in the_menu:
            if el[1] == cat_name:
                pixbuf = self._find_the_icon(el[3])
                # icon name comment exec path appinfo
                self.liststore.append([ pixbuf, el[0], el[4], el[2], el[5], el[6] ])
        
    def _find_the_icon(self,_item):
        pixbuf = None
        try:
            pixbuf = Gtk.IconTheme().load_icon(_item, self.ICON_SIZE, Gtk.IconLookupFlags.FORCE_SVG)
            pixbuf = pixbuf.scale_simple(self.ICON_SIZE,self.ICON_SIZE,GdkPixbuf.InterpType.BILINEAR)
        except:
            pass
        if pixbuf == None:
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(_item, self.ICON_SIZE, self.ICON_SIZE, True)
            except:
                pass
        if pixbuf == None:
            try:
                pixbuf = Gtk.IconTheme().load_icon("binary", self.ICON_SIZE, Gtk.IconLookupFlags.FORCE_SVG)
                pixbuf = pixbuf.scale_simple(self.ICON_SIZE,self.ICON_SIZE,GdkPixbuf.InterpType.BILINEAR)
            except:
                pass
        if pixbuf == None:
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(os.path.join(_curr_dir,"icons"+"/none.svg"), self.ICON_SIZE, self.ICON_SIZE, 1)
            except:
                pass
        return pixbuf
    
    # launch a program
    def on_iv_item_activated(self, iconview, widget):
        if self.iconview.get_selected_items() != None:
            rrow = self.iconview.get_selected_items()[0]
        
        # _ctx = Gio.AppLaunchContext.new()
        # _ctx.setenv("PWD",f"{_HOME}".encode())
        app_to_exec = self.liststore[rrow][5]
        #
        # _app_env = Gio.AppLaunchContext.new()
        # _app_env.setenv("TERMINAL","xterm")
        #
        os.chdir(_HOME)
        # ret=app_to_exec.launch(None,_app_env)
        ret=app_to_exec.launch(None,None)
        os.chdir(_curr_dir)
        if ret == False:
            _exec_name = self.liststore[rrow][3]
            self.msg_simple(f"{_exec_name} not found or not setted.")
        self.on_focus_out(None, None)
    
    def sigtype_handler(self, sig, frame):
        if sig == signal.SIGINT or sig == signal.SIGTERM:
            self._to_close()
    
    # only yes message dialog
    def msg_simple(self, mmessage):
        messagedialog2 = Gtk.MessageDialog(parent=self,
                              modal=True,
                              message_type=Gtk.MessageType.WARNING,
                              buttons=Gtk.ButtonsType.OK,
                              text=mmessage)
        messagedialog2.connect("response", self.dialog_response2)
        messagedialog2.show()
    
    def dialog_response2(self, messagedialog2, response_id):
        if response_id == Gtk.ResponseType.OK:
            messagedialog2.destroy()
        elif response_id == Gtk.ResponseType.DELETE_EVENT:
            messagedialog2.destroy()
    
    # def on_conf_btn(self, btn):
        # pass
    
    def on_focus_out(self, win, event):
        self.iconview.unselect_all()
        self.searchentry.delete_text(0,-1)
        # open bookmarks next time
        if USER_THEME == 0:
            if self._btn_toggled == self.btn_bookmark:
                self.hide()
                return
            self.btn_bookmark.set_active(True)
            self.on_toggle_toggled(self.btn_bookmark, None)
        elif USER_THEME == 1:
            self._btn_toggled = self.btn_bookmark
            self.btn_bookmark.clicked()
            self.btn_bookmark.grab_focus()
            if USE_LABEL_CATEGORY == 1:
                self.clabel.set_label("Bookmarks")
        #
        self.hide()
        
    # def on_show(self, widget):
        # pass

class ynDialog(Gtk.Dialog):
    def __init__(self, parent, _title1, _type):
        super().__init__(title=_type, transient_for=parent, flags=0)
        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        
        self.set_default_size(150, 100)
        label = Gtk.Label(label=_title1)
        box = self.get_content_area()
        box.add(label)
        self.show_all()


class clipboardWin(Gtk.Window):
    def __init__(self, parent):
        super().__init__()
        
        if is_wayland:
            CLIP_STORAGE = {}
            on_load_clips()
        
        self._parent = parent
        
        self.wwidth = self._parent.clip_width
        self.wheight = self._parent.clip_height
        
        self.set_transient_for(self._parent)
        # self.set_modal(True)
        
        _win_pos = self._parent.win_position
        
        # 0 left - 1 right
        self._position = 1
        
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_namespace(self, "clipboardwin")
        if self._position == 0:
            GtkLayerShell.set_margin(self, GtkLayerShell.Edge.LEFT, 10)
        elif self._position == 1:
            GtkLayerShell.set_margin(self, GtkLayerShell.Edge.RIGHT, 10)
        
        if _win_pos == 1:
            GtkLayerShell.set_margin(self, GtkLayerShell.Edge.BOTTOM, 10)
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.BOTTOM, 1)
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, 1)
        else:
            GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, 10)
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, 1)
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, 1)
        
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.ON_DEMAND)
        
        self.connect('focus-out-event', self.on_focus_out)
        # self.connect('show', self.on_show)
        
        self.set_size_request(self.wwidth, self.wheight)
        self.main_box = Gtk.Box.new(1,0)
        self.add(self.main_box)
        
        self.main_box.set_margin_start(_pad)
        self.main_box.set_margin_end(_pad)
        
        scroll_win = Gtk.ScrolledWindow.new()
        self.main_box.pack_start(scroll_win, True, True, _pad)
        # scroll_win.set_overlay_scrolling(True)
        scroll_win.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.list_box = Gtk.ListBox.new()
        self.list_box.set_activate_on_single_click(True)
        self.list_box.connect('row-activated', self.on_list_box)
        scroll_win.add(self.list_box)
        
        self.self_style_context = self.get_style_context()
        self.self_style_context.add_class("clipboardwin")
        
        self.populate_clips()
        
        donotdisturb_btn = Gtk.ToggleButton(label=DO_NOT_TRACK)
        donotdisturb_btn.set_active(self._parent.clip_do_not_track)
        donotdisturb_btn.connect("clicked",self.on_donotdisturb)
        self.main_box.pack_start(donotdisturb_btn,False,True,0)
        
        empty_btn = Gtk.Button(label=REMOVE_ALL)
        empty_btn.set_relief(Gtk.ReliefStyle.NONE)
        empty_btn.connect('clicked', self.on_empty_btn)
        self.main_box.pack_start(empty_btn,False,True,_pad)
        
        self.show_all()
    
    def on_donotdisturb(self, btn):
        # btn.set_active(btn.get_active())
        self._parent.onclip_do_not_disturb(btn.get_active())
    
    def on_empty_btn(self, btn):
        global CLIP_STORAGE
        CLIP_STORAGE = {}
        _l = self.list_box.get_children()
        for el in _l:
            self.list_box.remove(el)
            del el
        del _l
        _ll= os.listdir(self._parent.clips_path)
        for el in _ll:
            try:
                os.remove(os.path.join(self._parent.clips_path,el))
            except:
                pass
    
    def populate_clips(self):
        if CLIP_STORAGE:
            for _clip,_ctext in CLIP_STORAGE.items():
                __row = Gtk.ListBoxRow()
                __row.set_name("cliprow")
                __row.iid = _clip
                _tmp_box = Gtk.Box.new(0,0)
                __row.add(_tmp_box)
                _tmp_lbl = Gtk.Label(label=_ctext.decode().replace("\n"," "))
                # _tmp_box.set_halign(0)
                # _tmp_lbl.set_halign(1)
                _tmp_lbl.set_xalign(0)
                # _tmp_lbl.set_hexpand(True)
                
                if is_wayland:
                    _PREV = ""
                    if len(_ctext.decode()) > CLIP_CHAR_PREVIEW:
                        _PREV = _ctext.decode()[0:CLIP_CHAR_PREVIEW]+"..."
                    else:
                        _PREV = _ctext.decode()
                    _tmp_lbl.set_tooltip_text(_PREV)
                _tmp_lbl.set_ellipsize(Pango.EllipsizeMode.END)
                _tmp_box.pack_start(_tmp_lbl,True,True,2)
                _tmp_btn = Gtk.Button()
                # _tmp_btn.set_halign(2)
                try:
                    pixbuf = Gtk.IconTheme().load_icon("gtk-delete", 24, Gtk.IconLookupFlags.FORCE_SVG)
                    _img = Gtk.Image.new_from_pixbuf(pixbuf)
                    _tmp_btn.set_image(_img)
                except:
                    _tmp_btn.set_label("X")
                _tmp_btn.iid = _clip
                _tmp_btn.connect('clicked', self.on_tmp_btn, __row)
                _tmp_box.pack_start(_tmp_btn,False,False,0)
                self.list_box.insert(__row, 0)
    
    # remove the clip
    def on_tmp_btn(self, btn, __row):
        _clip = btn.iid
        if _clip in CLIP_STORAGE:
            del CLIP_STORAGE[_clip]
        ii = __row.get_index()
        try:
            os.remove(os.path.join(self._parent.clips_path, _clip))
            self.list_box.remove(__row)
        except:
            pass
    
    def on_list_box(self, _lb, _row):
        try:
            _clip = _row.iid
            _text = None
            with open(os.path.join(self._parent.clips_path,str(_clip)), "r") as _f:
                _text = "".join(_f.readlines())
            # remove the selected clip
            if _clip in CLIP_STORAGE:
                del CLIP_STORAGE[_clip]
            try:
                _clip_file = os.path.join(_curr_dir, "clips", _clip)
                if os.path.exists(_clip_file):
                    os.remove(_clip_file)
                # clipboard.set_text(_text, -1)
                #
                Popen("wl-copy --clear",shell=True)
                # Popen(f"wl-copy {_text}",shell=True)
                Popen("wl-copy '{}'".format(_text),shell=True)
                # Popen("echo '{}' | wl-copy -t text".format(_text),shell=True)
            except:
                pass
            if self._parent.CW:
                self._parent.CW = None
            self.close()
        except:
            pass
    
    def on_focus_out(self, win, event):
        if self._parent.CW:
            self._parent.CW = None
        self.close()
        
    # def on_show(self, widget):
        # pass


# bookmark or modify the desktop file
class menuModify(Gtk.Window):
    def __init__(self, parent, _item):
        super().__init__()
    
        self._parent = parent
        self._item = _item
        
        self.set_transient_for(self._parent)
        # self.set_modal(True)
        
        self.set_title(CHOOSE_OPTION)
        
        self.main_box = Gtk.Box.new(0,0)
        self.main_box.set_margin_start(_pad)
        self.main_box.set_margin_end(_pad)
        self.add(self.main_box)
        
        self._bookm = Gtk.Button(label=BOOKMARK1)
        self._bookm.connect('clicked', self._choose, 1)
        self.main_box.add(self._bookm)
        
        if self._parent._parent.menu_editor == "_internal_":
            self._modify = Gtk.Button(label=MODIFY1)
            self._modify.connect('clicked', self._choose, 2)
            self.main_box.add(self._modify)
        
        self._cancel = Gtk.Button(label=CLOSE1)
        self._cancel.connect('clicked', self.on_close)
        self.main_box.add(self._cancel)
        
        self.connect('delete-event', self.on_close)
        self.connect('destroy-event', self.on_close)
        
        ###########
        self._value = 0
        self.show_all()
    
    
    def _choose(self, w, _type):
        self._value = _type
        self.close()
    
    def on_close(self, w, e=None):
        #
        if self._value == 1:
            # remove from bookmarks
            if self._item in self._parent.bookmarks:
                if self._parent._btn_toggled.icat != "Bookmarks":
                    return
                dialog = ynDialog(self, DELETE_FROM_BOOKMARKS, "Question")
                response = dialog.run()
                if response == Gtk.ResponseType.OK:
                    _content = None
                    try:
                        self._parent.bookmarks.remove(self._item)
                        with open(_menu_favorites, "w") as _f:
                            for el in self._parent.bookmarks:
                                _f.write(el+"\n")
                        # rebuild bookmarks
                        self._parent.populate_bookmarks_at_start()
                        self._parent.populate_category("Bookmarks")
                    except Exception as E:
                        self._parent.msg_simple("Error\n"+str(E))
                #
                dialog.destroy()
                self._parent._parent.MW = None
            # add to bookmarks
            else:
                dialog = ynDialog(self, ADD_TO_BOOKMARKS, "Question")
                response = dialog.run()
                if response == Gtk.ResponseType.OK:
                    _content = None
                    try:
                        with open(_menu_favorites, "a") as _f:
                            _f.write(self._item)
                            _f.write("\n")
                        # rebuild bookmarks
                        self._parent.populate_bookmarks_at_start()
                    except Exception as E:
                        self._parent.msg_simple("Error\n"+str(E))
                dialog.destroy()
                self._parent._parent.MW = None
        elif self._value == 2:
            if os.path.exists(self._item):
                if self._parent._parent.menu_editor == "_internal_":
                    try:
                        _cmd = [os.path.join(_curr_dir,"appmenu.py"), self._item]
                        Popen(_cmd, shell=False)
                    except Exception as E:
                        self._parent.msg_simple("Error\n"+str(E))
                else:
                    pass
        #
        self._parent.MM = None
        self.close()



class otherWin(Gtk.Window):
    def __init__(self, parent):
        super().__init__()
        
        self._parent = parent
        
        self.set_transient_for(self._parent)
        # self.set_modal(True)
        
        _win_pos = self._parent.win_position
        
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_namespace(self, "servicewin")
        
        if _win_pos == 1:
            GtkLayerShell.set_margin(self, GtkLayerShell.Edge.BOTTOM, 10)
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.BOTTOM, 1)
            if self._parent.menu_win_position in [0,1]:
                GtkLayerShell.set_margin(self, GtkLayerShell.Edge.RIGHT, 10)
                GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, 1)
            elif self._parent.menu_win_position == 2:
                GtkLayerShell.set_margin(self, GtkLayerShell.Edge.LEFT, 10)
                GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.LEFT, 1)
        else:
            GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, 10)
            GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, 1)
            if self._parent.menu_win_position in [0,1]:
                GtkLayerShell.set_margin(self, GtkLayerShell.Edge.RIGHT, 10)
                GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, 1)
            elif self._parent.menu_win_position == 2:
                GtkLayerShell.set_margin(self, GtkLayerShell.Edge.LEFT, 10)
                GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.LEFT, 1)
        
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.ON_DEMAND)
        
        self.connect('focus-out-event', self.on_focus_out)
        # self.connect('show', self.on_show)
        
        self.set_size_request(self._parent.service_width, self._parent.service_height)
        
        self.self_style_context = self.get_style_context()
        self.self_style_context.add_class("servicewin")
        
        self.main_box = Gtk.Box.new(orientation=Gtk.Orientation.VERTICAL,spacing=0)
        self.main_box.set_margin_start(_pad)
        self.main_box.set_margin_end(_pad)
        self.add(self.main_box)
        
        self._stack = Gtk.Stack()
        _stack_vbox1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=0)
        self._stack.add_titled(_stack_vbox1,"Calendar",CALENDAR)
        
        _stack_vbox2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=0)
        # _stack_vbox2.set_homogeneous(True)
        self._stack.add_titled(_stack_vbox2,"Notifications",NOTIFICATIONS)
        
        _stack_vbox3 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=0)
        self._stack.add_titled(_stack_vbox3,"Notes",NOTES)
        
        self._stacksw = Gtk.StackSwitcher()
        self._stacksw.set_stack(self._stack)
        
        self.main_box.pack_start(self._stacksw, False, True, _pad)
        self.main_box.pack_start(self._stack, True, True, 0)
        
        # Calendar
        self._calendar = Gtk.Calendar()
        # self._calendar.connect('day-selected',self.on_selected_day)
        # self._calendar.connect('day-selected-double-click',self.on_activated_day)
        # self._calendar.mark_day(30)
        # self._calendar.props.show_details = True
        # self._calendar.set_detail_func(self.on_cal_events, None)
        _stack_vbox1.pack_start(self._calendar, True, True, 0)
        
        ## NOTIFICATIONS
        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.list_box.connect('row-activated', self.on_row_activated)
        _scrolledwin0 = Gtk.ScrolledWindow()
        # _scrolledwin0.set_property("propagate-natural-width", True)
        _scrolledwin0.set_overlay_scrolling(True)
        _scrolledwin0.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        _stack_vbox2.pack_start(_scrolledwin0, True, True, 6)
        _scrolledwin0.add(self.list_box)
        # separator
        separator = Gtk.Separator()
        separator.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.main_box.pack_start(separator, False, False, 0)
        # body
        _scrolledwin = Gtk.ScrolledWindow()
        _scrolledwin.set_overlay_scrolling(True)
        _scrolledwin.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        _stack_vbox2.pack_start(_scrolledwin, False, True, 0)
        self.body_lbl = Gtk.Label()
        self.body_lbl.set_use_markup(True)
        self.body_lbl.set_markup(" ")
        self.body_lbl.set_selectable(True)
        self.body_lbl.set_xalign(0)
        self.body_lbl.set_line_wrap(True)
        self.body_lbl.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        _scrolledwin.set_size_request(-1,max(int(self._parent.service_height/2),150))
        _scrolledwin.add(self.body_lbl)
        
        _clip_dir = os.path.join(_curr_dir,"mynots")
        _not_list = sorted(os.listdir(_clip_dir), reverse=True)
        
        self._my_nots = {}
        
        for el in _not_list:
            row = Gtk.ListBoxRow()
            row.set_name("notrow")
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
            row.add(hbox)
            
            row.iid = el
            
            _image_path = os.path.join(_clip_dir,el,"image.png")
            if os.path.exists(_image_path):
                _pix = GdkPixbuf.Pixbuf.new_from_file_at_scale(_image_path,64,64,True)
                _img = Gtk.Image.new_from_pixbuf(_pix)
                hbox.pack_start(_img,False,False,0)
            
            _not_text = ""
            with open(os.path.join(_clip_dir,el,"notification"),"r") as _f:
                _not_text = _f.read()
            
            try:
                (_app,_summ,_body) = _not_text.split("\n\n\n@\n\n\n")
            except:
                _app = ""
                _summ = ""
                _body = ""
            if _app == "" and _summ == "" and _body == "":
                continue
            
            self._my_nots[el] = _body.encode()
            
            _summ_lbl = Gtk.Label()
            _summ_lbl.set_single_line_mode(False)
            _summ_lbl.set_line_wrap(True)
            _summ_lbl.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
            _summ_lbl.set_use_markup(True)
            _summ_lbl.set_markup(_app+"\n"+f"<b>{_summ}</b>")
            _summ_lbl.set_xalign(0)
            hbox.pack_start(_summ_lbl,True,True,4)
            
            _remove_btn = Gtk.Button()
            try:
                pixbuf = Gtk.IconTheme().load_icon("gtk-delete", 24, Gtk.IconLookupFlags.FORCE_SVG)
                _img = Gtk.Image.new_from_pixbuf(pixbuf)
                _remove_btn.set_image(_img)
            except:
                _remove_btn.set_label("X")
            
            _remove_btn.connect('clicked', self.on_remove_btn, el, row)
            hbox.pack_start(_remove_btn,False,False,0)
            
            self.list_box.add(row)
        
        ## STICKY NOTES
        self.path_notes = os.path.join(_curr_dir,"notes")
        self.add_note = Gtk.Button(label=NEW_NOTE)
        self.add_note.set_relief(Gtk.ReliefStyle.NONE)
        self.add_note.connect('clicked', self.on_add_note)
        _stack_vbox3.add(self.add_note)
        
        self.show_hide_notes = Gtk.Button(label=SHOW_HIDE_NOTES)
        self.show_hide_notes.set_relief(Gtk.ReliefStyle.NONE)
        self.show_hide_notes.connect('clicked', self.on_show_hide_notes)
        _stack_vbox3.add(self.show_hide_notes)
        
        ##############
        
        self.timer_btn = Gtk.Button.new()
        if self._parent._is_timer_set == 0:
            self.timer_btn.set_label(SET_TIMER)
        elif self._parent._is_timer_set == 1:
            self.timer_btn.set_label(TIMER_SETTED)
        self.timer_btn.set_relief(Gtk.ReliefStyle.NONE)
        self.timer_btn.connect('clicked', self.on_timer_btn)
        self.main_box.pack_start(self.timer_btn,False,True,4)
        
        separator = Gtk.Separator()
        separator.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.main_box.pack_start(separator, False, False, 0)
        
        self.btn_box = Gtk.Box.new(0,0)
        self.btn_box.set_margin_bottom(_pad)
        self.main_box.pack_start(self.btn_box,False,False,0)
        
        conf_btn = Gtk.Button(label=CONFIGURATOR)
        conf_btn.set_relief(Gtk.ReliefStyle.NONE)
        conf_btn.connect('clicked', self.on_conf_btn)
        self.btn_box.pack_start(conf_btn,False,False,0)
        
        self.dnd_btn = Gtk.Button(label=DO_NOT_DISTURB)
        _dnd_file = os.path.join(_curr_dir,"do_not_disturb_mode")
        if os.path.exists(_dnd_file):
            self.dnd_btn.set_label(DO_NOT_DISTURB_ON)
        self.dnd_btn.set_relief(Gtk.ReliefStyle.NONE)
        self.dnd_btn.connect('clicked', self.on_dnd_btn)
        self.btn_box.pack_start(self.dnd_btn,True,False,0)
        
        exit_btn = Gtk.Button(label=EXIT2)
        exit_btn.set_relief(Gtk.ReliefStyle.NONE)
        exit_btn.connect('clicked', self.on_exit_btn)
        self.btn_box.pack_start(exit_btn,False,False,0)
        
        self.show_all()
        
    def on_add_note(self, btn):
        if self._parent.OW:
            self._parent.OW.close()
            self._parent.OW = None
        
        time_now = str(int(time.time()))
        while os.path.exists(os.path.join(self.path_notes, time_now)):
            sleep(0.1)
            time_now = str(int(time.time()))
            i += 1
            if i == 10:
                break
            return
        
        for el in self._parent.list_notes:
            el.show_all()
        
        # _notedialog = noteDialog(self, "", time_now)
        _notedialog = noteDialog(self, "", str(time_now)+"_0_0")
        _notedialog.show_all()
    
    def on_show_hide_notes(self, btn):
        is_visible = 0
        for el in self._parent.list_notes:
            if el.get_property("visible"):
                is_visible = 1
        for el in self._parent.list_notes:
            if is_visible == 1:
            # if el.get_realized():
            # if el.get_property("visible"):
                el.hide()
            else:
            # elif not el.get_property("visible"):
                el.show_all()
        
    def on_remove_btn(self, btn, el, row):
        try:
            _path = os.path.join(_curr_dir,"mynots",el)
            shutil.rmtree(_path)
            del self._my_nots[el]
            _selected_row = self.list_box.get_selected_row()
            self.list_box.remove(row)
            if _selected_row == row:
                self.body_lbl.set_markup(" ")
        except:
            pass
    
    def on_row_activated(self, box, row):
        try:
            _body = self._my_nots[row.iid].decode()
            self.body_lbl.set_markup(" ")
            self.body_lbl.set_markup(_body)
        except:
            pass
    
    def on_timer_btn(self, btn):
        if self._parent._is_timer_set == 1:
            self.timer_btn.set_label(SET_TIMER)
            self._parent._is_timer_set = 0
            try:
                GLib.source_remove(self._parent.timer_id)
            except:
                pass
            return
        
        _value = 1
        if self._parent.OW:
            _this = self._parent.OW
            self._parent.OW = None
            _this.destroy()
        self._parent.on_set_timer(_value)
    
    def on_conf_btn(self, btn):
        if self._parent.OW:
            _this = self._parent.OW
            self._parent.OW = None
            _this.destroy()
        self._parent.on_button_conf_clicked(btn)
    
    def on_dnd_btn(self, btn):
        _dnd_file = os.path.join(_curr_dir,"do_not_disturb_mode")
        if not os.path.exists(_dnd_file):
            try:
                _f =  open(_dnd_file,"w")
                _f.close()
                self.dnd_btn.set_label(DO_NOT_DISTURB_ON)
            except:
                pass
        else:
            try:
                os.remove(_dnd_file)
                self.dnd_btn.set_label(DO_NOT_DISTURB)
            except:
                pass
    
    def on_exit_btn(self, btn):
        commandWin(self, "exit")
    
    def on_selected_day(self, _calendar):
        pass
    
    def on_activated_day(self, _calendar):
        pass
    
    def on_cal_events(self, _cal, _y,_m,_d, data):
        if _y == 2024 and _m == 10 and _d == 29:
            return "10.15"
    
    def on_focus_out(self, win, event):
        # self.close()
        if self._parent.OW:
            self._parent.OW.close()
            self._parent.OW = None
        
    # def on_show(self, widget):
        # pass

class noteDialog(Gtk.Window):
    def __init__(self, _parent, _text, _id):
        super().__init__()
        
        self._parent = _parent
        self._text = _text
        self._id_tmp = _id
        self.path_notes = os.path.join(_curr_dir,"notes")
        
        # GtkLayerShell.init_for_window(self)
        # GtkLayerShell.set_namespace(self, "notewin")
        # GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.ON_DEMAND)
        # # GtkLayerShell.set_layer(self, GtkLayerShell.Layer.TOP)
        
        self.set_title("Note1")
        self.set_decorated(False)
        # self.set_transient_for(self._parent)
        
        self.connect('delete-event', self.delete_event)
        self.connect('destroy-event', self.delete_event)
        self.connect('destroy', self.delete_event)
        self.connect('unmap-event', self.on_unmap_event)
        self.connect('hide', self.on_unmap_event)
        
        self.self_style_context = self.get_style_context()
        self.self_style_context.add_class("notewin")
        
        # self.set_default_size(300, 300)
        # self.set_size_request(300, 300)
        self.set_size_request(self._parent._parent.note_width, self._parent._parent.note_height)
        
        # # do not use
        # _bc = red
        # _cc = white
        # css = ".notewin textview text { "+"background-color: {};".format(_bc)+"color: {};".format(_cc)+"}"
        # self._parent._parent.style_provider.load_from_data(css.encode('utf-8'))
        # self._parent._parent.SC.add_provider_for_screen(
        # Gdk.Screen.get_default(),
            # self._parent._parent.style_provider,
            # Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            # )
        
        box = Gtk.Box.new(orientation=Gtk.Orientation.VERTICAL,spacing=0)
        self.add(box)
        
        _scrolledwin = Gtk.ScrolledWindow()
        _scrolledwin.set_overlay_scrolling(True)
        _scrolledwin.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        box.pack_start(_scrolledwin, True, True, 0)
        
        self.text_view = Gtk.TextView()
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        
        # # use the css
        # self.text_view.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(10, 8, 0, 1))
        # self.text_view.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0, 10, 0, 1))
        
        _scrolledwin.add(self.text_view)
        
        # button box
        btn_box = Gtk.Box.new(orientation=Gtk.Orientation.HORIZONTAL,spacing=0)
        box.add(btn_box)
        
        # delete the entire note
        delete_btn = Gtk.Button(label=DELETE)
        delete_btn.set_relief(Gtk.ReliefStyle.NONE)
        delete_btn.connect('clicked', self.on_delete)
        btn_box.pack_start(delete_btn,True,True,0)
        
        accept_btn = Gtk.Button(label=ACCEPT)
        accept_btn.set_relief(Gtk.ReliefStyle.NONE)
        accept_btn.connect('clicked', self.on_accept)
        btn_box.pack_start(accept_btn,True,True,0)
        
        self.text_buffer = self.text_view.get_buffer()
        self.text_buffer.set_text(_text)
        
        # _data = self._id.split("_")
        # if _data and len(_data) == 2:
            # _x,_y = _data[1].split("-")
            # self.move(_x,_y)
        
        self._id,self._id_x,self._id_y = self._id_tmp.split("_")
        
        # self.connect('hide', self.on_hide)
        
        # self.get_window().set_events(Gdk.EventMask.PROPERTY_CHANGE_MASK)
        # # Gtk.Widget.signals.property_notify_event(self, Gdk.EventType.CONFIGURE)
        # self.connect('property-notify-event', self.on_move)
        
        # self.connect('show', self.on_show)
        
        # self.show_all()
        
    # def on_move(self,widget,event):
        # pass
    
    # def on_show(self, widget):
        # print("on show")
        # print(self.get_window().get_geometry())
        
    # def on_hide(self, widget):
        # _position = self.get_position()
    
    def on_unmap_event(self, widget, event=None):
        if self.get_property("visible"):
            return False
    
    def delete_event(self, widget, event=None):
        return True
        
    def get_textview_text(self):
        text_view_text = self.text_buffer.get_text(self.text_buffer.get_start_iter(),self.text_buffer.get_end_iter(),False)
        return text_view_text
    
    # print - find the x and y
    def on_accept(self, btn=None):
        textview_text = self.get_textview_text()
        if textview_text == None or textview_text == "":
            self.close()
        else:
            _x = 0
            _y = 0
            # print - to do position
            # (x=0, y=0, width=300, height=300)
            # print(self.get_window().get_geometry())
            try:
                with open(os.path.join(self.path_notes,self._id+"_"+str(_x)+"_"+str(_y)),"w") as ffile:
                    ffile.write(textview_text)
                if not self._id in self._parent._parent.list_notes:
                    self._parent._parent.list_notes.append(self)
            except:
                pass
    
    def on_delete(self, btn=None):
        if os.path.exists(os.path.join(self.path_notes,self._id_tmp)):
            try:
                os.remove(os.path.join(self.path_notes,self._id_tmp))
                self._parent.list_notes.remove(self)
            except:
                pass
        self.destroy()


class timerDialog(Gtk.Dialog):
    def __init__(self, parent):
        super().__init__(title=SET_TIMER1, transient_for=parent, flags=0)
        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        
        self._parent = parent
        
        self.self_style_context = self.get_style_context()
        self.self_style_context.add_class("timerwin")
        
        self.set_default_size(100, 100)
        box = self.get_content_area()
        self.set_decorated(False)
        
        for el in box.get_children()[0].get_children()[0].get_children():
            if isinstance(el, Gtk.Button):
                el.set_relief(Gtk.ReliefStyle.NONE)
        
        _lbl = Gtk.Label(label=MINUTES)
        box.add(_lbl)
        _spinbtn = Gtk.SpinButton.new_with_range(3,3000,1)
        box.add(_spinbtn)
        _spinbtn.connect('value-changed', self.on_spinbtn)
        _spinbtn.set_input_purpose(Gtk.InputPurpose.DIGITS)
        
        self.chk_sound = Gtk.CheckButton(label=USE_SOUND)
        self.chk_sound.set_active(True)
        self.chk_sound.connect('toggled', self.on_toggle_toggled, "sound")
        box.add(self.chk_sound)
        
        self.chk_dialog = Gtk.CheckButton(label=USE_DIALOG)
        self.chk_dialog.connect('toggled', self.on_toggle_toggled, "dialog")
        box.add(self.chk_dialog)
        # minutes - sound - dialog
        self._values = [3,True,False]
        
        self.show_all()
        
    def on_spinbtn(self, btn):
        self._values[0] = btn.get_value_as_int()
        
    def on_toggle_toggled(self, btn, _type):
        if _type == "sound":
            self._values[1] = btn.get_active()
        elif _type == "dialog":
            self._values[2] = btn.get_active()
        if self._values[1] == False and self._values[2] == False:
            self._values[2] = True
        

class DialogConfiguration(Gtk.Dialog):
    def __init__(self, parent):
        super().__init__(title=SETTINGS2, transient_for=parent, flags=0)
        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        
        self._parent = parent
        
        self.set_title(CONFIGURATOR)
        
        self.set_default_size(100, 100)
        box = self.get_content_area()
        
        self.set_modal(True)
        self.set_transient_for(None)
        self.set_decorated(False)
        
        self.connect('delete-event', self.delete_event)
        self.connect('destroy-event', self.delete_event)
        
        self.notebook = Gtk.Notebook.new()
        self.notebook.set_show_border(True)
        box.add(self.notebook)
        
        self.page1_box = Gtk.Grid.new()
        self.page1_box.set_column_homogeneous(True)
        page1_label = Gtk.Label(label=PANEL)
        self.notebook.append_page(self.page1_box, page1_label)
        #
        self.page2_box = Gtk.Grid.new()
        self.page2_box.set_column_homogeneous(True)
        page2_label = Gtk.Label(label=MENU)
        self.notebook.append_page(self.page2_box, page2_label)
        #
        self.page3_box = Gtk.Grid.new()
        self.page3_box.set_column_homogeneous(True)
        page3_label = Gtk.Label(label=SERVICE)
        self.notebook.append_page(self.page3_box, page3_label)
        #
        if self._parent.clipboard_use and USE_CLIPBOARD:
            self.page4_box = Gtk.Grid.new()
            self.page4_box.set_column_homogeneous(True)
            page4_label = Gtk.Label(label=CLIPBOARD)
            self.notebook.append_page(self.page4_box, page4_label)
        #
        self.page5_box = Gtk.Grid.new()
        self.page5_box.set_column_homogeneous(True)
        page5_label = Gtk.Label(label=NOTIFICATIONS2)
        self.notebook.append_page(self.page5_box, page5_label)
        
        # other settings
        self.page6_box = Gtk.Grid.new()
        self.page6_box.set_column_homogeneous(True)
        page6_label = Gtk.Label(label=OTHER_SETTINGS)
        self.notebook.append_page(self.page6_box, page6_label)
        
        ##### PANEL
        # width - pixels to substract
        width_lbl = Gtk.Label(label=WIDTH_1)
        self.page1_box.attach(width_lbl,0,0,1,1)
        width_lbl.set_halign(1)
        width_spinbtn = Gtk.SpinButton.new_with_range(0,4000,1)
        width_spinbtn.set_value(self._parent.win_width)
        self.page1_box.attach_next_to(width_spinbtn,width_lbl,1,1,1)
        width_spinbtn.connect('value-changed', self.on_width_spinbtn)
        width_spinbtn.set_input_purpose(Gtk.InputPurpose.DIGITS)
        # height
        size_lbl = Gtk.Label(label=HEIGHT)
        self.page1_box.attach(size_lbl,0,1,1,1)
        size_lbl.set_halign(1)
        size_spinbtn = Gtk.SpinButton.new_with_range(10,400,1)
        size_spinbtn.set_value(self._parent.win_height)
        self.page1_box.attach_next_to(size_spinbtn,size_lbl,1,1,1)
        size_spinbtn.connect('value-changed', self.on_size_spinbtn)
        size_spinbtn.set_input_purpose(Gtk.InputPurpose.DIGITS)
        # # corners top
        # corner_lbl = Gtk.Label(label="Corners: top")
        # self.page1_box.attach(corner_lbl,0,2,1,1)
        # corner_lbl.set_halign(1)
        # corner_spinbtn = Gtk.SpinButton.new_with_range(0,60,1)
        # corner_spinbtn.set_value(self._parent._corner_top)
        # self.page1_box.attach_next_to(corner_spinbtn,corner_lbl,1,1,1)
        # corner_spinbtn.connect('value-changed', self.on_corner_spinbtn)
        # corner_spinbtn.set_input_purpose(Gtk.InputPurpose.DIGITS)
        # # corners bottom
        # corner_lbl2 = Gtk.Label(label="Corners: bottom")
        # self.page1_box.attach(corner_lbl2,0,3,1,1)
        # corner_lbl2.set_halign(1)
        # corner_spinbtn2 = Gtk.SpinButton.new_with_range(0,60,1)
        # corner_spinbtn2.set_value(self._parent._corner_bottom)
        # self.page1_box.attach_next_to(corner_spinbtn2,corner_lbl2,1,1,1)
        # corner_spinbtn2.connect('value-changed', self.on_corner_spinbtn2)
        # corner_spinbtn2.set_input_purpose(Gtk.InputPurpose.DIGITS)
        # position
        pos_lbl = Gtk.Label(label=POSITION)
        self.page1_box.attach(pos_lbl,0,4,1,1)
        pos_lbl.set_halign(1)
        pos_combo = Gtk.ComboBoxText.new()
        pos_combo.append_text(TOP)
        pos_combo.append_text(BOTTOM)
        pos_combo.set_active(self._parent.win_position)
        self.page1_box.attach_next_to(pos_combo,pos_lbl,1,1,1)
        pos_combo.connect('changed', self.on_pos_combo)
        # clipboard
        if USE_CLIPBOARD:
            clip_lbl = Gtk.Label(label=CLIPBOARD2)
            clip_lbl.set_tooltip_text(USE_INTERNAL_WIDGET)
            self.page1_box.attach(clip_lbl,0,5,1,1)
            clip_lbl.set_halign(1)
            clip_sw = Gtk.Switch.new()
            clip_sw.set_halign(1)
            clip_sw.set_active(self._parent.clipboard_use)
            # clip_sw.set_halign(1)
            clip_sw.connect('notify::active', self.on_switch, "clipboard")
            self.page1_box.attach_next_to(clip_sw,clip_lbl,1,1,1)
        # label1
        label1_lbl = Gtk.Label(label=OUTPUT_LEFT)
        self.page1_box.attach(label1_lbl,0,6,1,1)
        label1_lbl.set_halign(1)
        out1_sw = Gtk.Switch.new()
        out1_sw.set_halign(1)
        out1_sw.set_active(self._parent.label1_use)
        # out1_sw.set_halign(1)
        out1_sw.connect('notify::active', self.on_switch, "out1")
        self.page1_box.attach_next_to(out1_sw,label1_lbl,1,1,1)
        # label2
        # label2_lbl = Gtk.Label(label="Output Right")
        label2_lbl = Gtk.Label(label=OUTPUT_CENTER_RIGHT)
        label2_lbl.set_tooltip_text(OUTPUT_C_R_MSG)
        self.page1_box.attach(label2_lbl,0,7,1,1)
        label2_lbl.set_halign(1)
        out2_sw = Gtk.Switch.new()
        out2_sw.set_halign(1)
        out2_sw.set_active(self._parent.label2_use)
        # out2_sw.set_halign(1)
        out2_sw.connect('notify::active', self.on_switch, "out2")
        self.page1_box.attach_next_to(out2_sw,label2_lbl,1,1,1)
        # # taskmanager
        # task_lbl = Gtk.Label(label="Task manager")
        # self.page1_box.attach(task_lbl,0,8,1,1)
        # task_lbl.set_halign(1)
        # task_sw = Gtk.Switch.new()
        # task_sw.set_active(self._parent.task_use)
        # # task_sw.set_halign(1)
        # task_sw.connect('notify::active', self.on_switch, "task")
        # self.page1_box.attach_next_to(task_sw,task_lbl,1,1,1)
        # clock
        clock_lbl = Gtk.Label(label=CLOCK)
        clock_lbl.set_tooltip_text(USE_INTERNAL_CLOCK_WIDGET)
        self.page1_box.attach(clock_lbl,0,9,1,1)
        clock_lbl.set_halign(1)
        clock_sw = Gtk.Switch.new()
        clock_sw.set_halign(1)
        clock_sw.set_active(self._parent.clock_use)
        # clock_sw.set_halign(1)
        clock_sw.connect('notify::active', self.on_switch, "clock")
        self.page1_box.attach_next_to(clock_sw,clock_lbl,1,1,1)
        # 
        _time_format = Gtk.ComboBoxText.new()
        _time_format.append_text(H24)
        _time_format.append_text(AMPM_M)
        _time_format.append_text(AMPM_N)
        _time_format.set_active(self._parent.time_format)
        _time_format.connect('changed', self.on_time_combo)
        # self.page1_box.attach_next_to(_time_format,clock_sw,1,1,1)
        self.page1_box.attach(_time_format,1,10,1,1)
        # if USE_TASKBAR > 0:
            # clock_sw.set_sensitive(False)
            # _time_format.set_sensitive(False)
        
        ## MENU
        menu_lbl_w = Gtk.Label(label=WIDTH)
        self.page2_box.attach(menu_lbl_w,0,0,1,1)
        menu_lbl_w.set_halign(1)
        menu_w_spinbtn = Gtk.SpinButton.new_with_range(0,4000,1)
        menu_w_spinbtn.set_value(self._parent.menu_width)
        self.page2_box.attach_next_to(menu_w_spinbtn,menu_lbl_w,1,1,1)
        menu_w_spinbtn.connect('value-changed', self.on_menu_wh_spinbtn, "w")
        menu_w_spinbtn.set_input_purpose(Gtk.InputPurpose.DIGITS)
        
        menu_lbl_h = Gtk.Label(label=HEIGHT)
        self.page2_box.attach(menu_lbl_h,0,1,1,1)
        menu_lbl_h.set_halign(1)
        menu_h_spinbtn = Gtk.SpinButton.new_with_range(0,4000,1)
        menu_h_spinbtn.set_value(self._parent.menu_height)
        self.page2_box.attach_next_to(menu_h_spinbtn,menu_lbl_h,1,1,1)
        menu_h_spinbtn.connect('value-changed', self.on_menu_wh_spinbtn, "h")
        menu_h_spinbtn.set_input_purpose(Gtk.InputPurpose.DIGITS)
        
        menu_lbl_ci = Gtk.Label(label=CAT_ICON_SIZE)
        self.page2_box.attach(menu_lbl_ci,0,2,1,1)
        menu_lbl_ci.set_halign(1)
        menu_ci_spinbtn = Gtk.SpinButton.new_with_range(24,2048,1)
        menu_ci_spinbtn.set_value(self._parent.menu_cat_icon_size)
        self.page2_box.attach_next_to(menu_ci_spinbtn,menu_lbl_ci,1,1,1)
        menu_ci_spinbtn.connect('value-changed', self.on_menu_wh_spinbtn, "ci")
        menu_ci_spinbtn.set_input_purpose(Gtk.InputPurpose.DIGITS)
        
        menu_lbl_i = Gtk.Label(label=ITEM_ICON_SIZE)
        self.page2_box.attach(menu_lbl_i,0,3,1,1)
        menu_lbl_i.set_halign(1)
        menu_i_spinbtn = Gtk.SpinButton.new_with_range(24,2048,1)
        menu_i_spinbtn.set_value(self._parent.menu_item_icon_size)
        self.page2_box.attach_next_to(menu_i_spinbtn,menu_lbl_i,1,1,1)
        menu_i_spinbtn.connect('value-changed', self.on_menu_wh_spinbtn, "ii")
        menu_i_spinbtn.set_input_purpose(Gtk.InputPurpose.DIGITS)
        
        # menu column width
        menu_lbl_iw = Gtk.Label(label=MENU_ITEM_WIDTH1)
        menu_lbl_iw.set_tooltip_text(MENU_ITEM_WIDTH1_MSG)
        self.page2_box.attach(menu_lbl_iw,0,4,1,1)
        menu_lbl_iw.set_halign(1)
        menu_iw_spinbtn = Gtk.SpinButton.new_with_range(0,2048,1)
        menu_iw_spinbtn.set_value(self._parent.menu_item_width)
        self.page2_box.attach_next_to(menu_iw_spinbtn,menu_lbl_iw,1,1,1)
        menu_iw_spinbtn.connect('value-changed', self.on_menu_wh_spinbtn, "iw")
        menu_iw_spinbtn.set_input_purpose(Gtk.InputPurpose.DIGITS)
        
        
        # # NOT NECESSARY
        # menu_lbl_t = Gtk.Label(label=TERMINAL)
        # self.page2_box.attach(menu_lbl_t,0,5,1,1)
        # menu_lbl_t.set_halign(1)
        # self.entry_menu_t = Gtk.Entry.new()
        # self.entry_menu_t.connect('changed', self.on_entry_menu, "t")
        # self.page2_box.attach_next_to(self.entry_menu_t,menu_lbl_t,1,1,1)
        # self.entry_menu_t.set_text(self._parent.menu_terminal)
        
        menu_lbl_ls = Gtk.Label(label=LIVE_SEARCH_CHARS)
        menu_lbl_ls.set_tooltip_text(MIN_CHARS_QUERY)
        self.page2_box.attach(menu_lbl_ls,0,6,1,1)
        menu_lbl_ls.set_halign(1)
        menu_ls_spinbtn = Gtk.SpinButton.new_with_range(0,20,1)
        menu_ls_spinbtn.set_value(self._parent.menu_live_search)
        self.page2_box.attach_next_to(menu_ls_spinbtn,menu_lbl_ls,1,1,1)
        menu_ls_spinbtn.connect('value-changed', self.on_menu_wh_spinbtn, "ls")
        menu_ls_spinbtn.set_input_purpose(Gtk.InputPurpose.DIGITS)
        
        menu_lbl_wp = Gtk.Label(label=POSITION2)
        self.page2_box.attach(menu_lbl_wp,0,7,1,1)
        menu_lbl_wp.set_halign(1)
        menu_combo_p = Gtk.ComboBoxText.new()
        menu_combo_p.append_text(LEFT)
        menu_combo_p.append_text(CENTER)
        menu_combo_p.append_text(RIGHT)
        menu_combo_p.set_active(self._parent.menu_win_position)
        menu_combo_p.connect('changed', self.on_menu_combo, "pos")
        self.page2_box.attach_next_to(menu_combo_p,menu_lbl_wp,1,1,1)
        
        menu_editor = Gtk.Label(label=MENU_EDITOR)
        menu_editor.set_tooltip_text(MENU_EDITOR_MSG1)
        self.page2_box.attach(menu_editor,0,8,1,1)
        menu_editor.set_halign(1)
        self.entry_menu_editor = Gtk.Entry.new()
        self.entry_menu_editor.connect('changed', self.on_entry_menu, "me")
        self.page2_box.attach_next_to(self.entry_menu_editor,menu_editor,1,1,1)
        self.entry_menu_editor.set_text(self._parent.menu_editor)
        
        ## SERVICE MENU
        service_lbl_w = Gtk.Label(label=WIDTH)
        service_lbl_w.set_tooltip_text(CAL_WIDTH_MSG1)
        self.page3_box.attach(service_lbl_w,0,0,1,1)
        service_lbl_w.set_halign(1)
        service_w_spinbtn = Gtk.SpinButton.new_with_range(0,4000,1)
        service_w_spinbtn.set_value(self._parent.service_width)
        self.page3_box.attach_next_to(service_w_spinbtn,service_lbl_w,1,1,1)
        service_w_spinbtn.connect('value-changed', self.on_service_wh_spinbtn, "w")
        service_w_spinbtn.set_input_purpose(Gtk.InputPurpose.DIGITS)
            
        service_lbl_h = Gtk.Label(label=HEIGHT)
        service_lbl_h.set_tooltip_text(CAL_HEIGHT_MSG1)
        self.page3_box.attach(service_lbl_h,0,1,1,1)
        service_lbl_h.set_halign(1)
        service_h_spinbtn = Gtk.SpinButton.new_with_range(0,4000,1)
        service_h_spinbtn.set_value(self._parent.service_height)
        self.page3_box.attach_next_to(service_h_spinbtn,service_lbl_h,1,1,1)
        service_h_spinbtn.connect('value-changed', self.on_service_wh_spinbtn, "h")
        service_h_spinbtn.set_input_purpose(Gtk.InputPurpose.DIGITS)
        
        # # sounds
        # timer_lbl_sound = Gtk.Label(label="Play sound")
        # self.page3_box.attach(timer_lbl_sound,0,2,1,1)
        # timer_lbl_sound.set_halign(1)
        # timer_combo = Gtk.ComboBoxText.new()
        # timer_combo.append_text("Internal player")
        # timer_combo.append_text("External player")
        # timer_combo.connect('changed', self.on_timer_combo)
        # self.page3_box.attach_next_to(timer_combo,timer_lbl_sound,1,1,1)
        
        # _entry_timer_lbl = Gtk.Label(label="Player")
        # _entry_timer_lbl.set_halign(1)
        # self.page3_box.attach(_entry_timer_lbl,0,3,1,1)
        # self.entry_timer = Gtk.Entry.new()
        # self.entry_timer.connect('changed', self.on_entry_timer)
        # self.page3_box.attach_next_to(self.entry_timer,_entry_timer_lbl,1,1,1)
        # if self._parent.service_sound_player == 0:
            # timer_combo.set_active(0)
            # self.entry_timer.set_state_flags(Gtk.StateFlags.INSENSITIVE, True)
        # elif self._parent.service_sound_player == 1:
            # timer_combo.set_active(1)
            # self.entry_timer.set_text(self._parent.service_player)
        
        _logout_lbl = Gtk.Label(label=LOGOUT_COMM)
        _logout_lbl.set_halign(1)
        self.page3_box.attach(_logout_lbl,0,4,1,1)
        self.entry_logout = Gtk.Entry.new()
        self.entry_logout.set_text(self._parent._logout)
        self.entry_logout.connect('changed', self.on_entry_commands, "l")
        self.page3_box.attach_next_to(self.entry_logout,_logout_lbl,1,1,1)
        
        _reboot_lbl = Gtk.Label(label=REBOOT_COMM)
        _reboot_lbl.set_halign(1)
        self.page3_box.attach(_reboot_lbl,0,5,1,1)
        self.entry_reboot = Gtk.Entry.new()
        self.entry_reboot.set_text(self._parent._reboot)
        self.entry_reboot.connect('changed', self.on_entry_commands, "r")
        self.page3_box.attach_next_to(self.entry_reboot,_reboot_lbl,1,1,1)
        
        _shutdown_lbl = Gtk.Label(label=SHUTDOWN_COMM)
        _shutdown_lbl.set_halign(1)
        self.page3_box.attach(_shutdown_lbl,0,6,1,1)
        self.entry_shutdown = Gtk.Entry.new()
        self.entry_shutdown.set_text(self._parent._shutdown)
        self.entry_shutdown.connect('changed', self.on_entry_commands, "s")
        self.page3_box.attach_next_to(self.entry_shutdown,_shutdown_lbl,1,1,1)
        
        _note_w_lbl = Gtk.Label(label=NOTE_WIDTH)
        _note_w_lbl.set_halign(1)
        self.page3_box.attach(_note_w_lbl,0,7,1,1)
        note_w_spinbtn = Gtk.SpinButton.new_with_range(0,4000,1)
        note_w_spinbtn.set_value(self._parent.note_width)
        self.page3_box.attach_next_to(note_w_spinbtn,_note_w_lbl,1,1,1)
        note_w_spinbtn.connect('value-changed', self.on_note_wh_spinbtn, "w")
        note_w_spinbtn.set_input_purpose(Gtk.InputPurpose.DIGITS)
        
        _note_h_lbl = Gtk.Label(label=NOTE_HEIGHT)
        _note_h_lbl.set_halign(1)
        self.page3_box.attach(_note_h_lbl,0,8,1,1)
        note_h_spinbtn = Gtk.SpinButton.new_with_range(0,4000,1)
        note_h_spinbtn.set_value(self._parent.note_height)
        self.page3_box.attach_next_to(note_h_spinbtn,_note_h_lbl,1,1,1)
        note_h_spinbtn.connect('value-changed', self.on_note_wh_spinbtn, "h")
        note_h_spinbtn.set_input_purpose(Gtk.InputPurpose.DIGITS)
        
        
        ## CLIPBOARD
        if USE_CLIPBOARD and self._parent.clipboard_use:
            clip_lbl_w = Gtk.Label(label=WIDTH)
            clip_lbl_w.set_tooltip_text(CLIPBOARD_WIDTH_MSG1)
            self.page4_box.attach(clip_lbl_w,0,0,1,1)
            clip_lbl_w.set_halign(1)
            clip_w_spinbtn = Gtk.SpinButton.new_with_range(0,4000,1)
            clip_w_spinbtn.set_value(self._parent.clip_width)
            self.page4_box.attach_next_to(clip_w_spinbtn,clip_lbl_w,1,1,1)
            clip_w_spinbtn.connect('value-changed', self.on_clip_wh_spinbtn, "w")
            clip_w_spinbtn.set_input_purpose(Gtk.InputPurpose.DIGITS)
            
            clip_lbl_h = Gtk.Label(label=HEIGHT)
            clip_lbl_h.set_tooltip_text(CLIPBOARD_HEIGHT_MSG1)
            self.page4_box.attach(clip_lbl_h,0,1,1,1)
            clip_lbl_h.set_halign(1)
            clip_h_spinbtn = Gtk.SpinButton.new_with_range(0,4000,1)
            clip_h_spinbtn.set_value(self._parent.clip_height)
            self.page4_box.attach_next_to(clip_h_spinbtn,clip_lbl_h,1,1,1)
            clip_h_spinbtn.connect('value-changed', self.on_clip_wh_spinbtn, "h")
            clip_h_spinbtn.set_input_purpose(Gtk.InputPurpose.DIGITS)
            
            # max history
            clip_lbl_num = Gtk.Label(label=MAX_CLIPS_STORE)
            clip_lbl_num.set_tooltip_text(MAX_CLIPS_STORE_MSG1)
            self.page4_box.attach(clip_lbl_num,0,3,1,1)
            clip_lbl_num.set_halign(1)
            clip_num_spinbtn = Gtk.SpinButton.new_with_range(1,200,1)
            clip_num_spinbtn.set_value(self._parent.clip_max_clips)
            self.page4_box.attach_next_to(clip_num_spinbtn,clip_lbl_num,1,1,1)
            clip_num_spinbtn.connect('value-changed', self.on_clip_spinbtn, "clips")
            clip_num_spinbtn.set_input_purpose(Gtk.InputPurpose.DIGITS)
        
        ## NOTIFICATIONS
        # window width
        not_lbl_w = Gtk.Label(label=WIDTH)
        not_lbl_w.set_tooltip_text(NOT_WIDTH_MSG1)
        self.page5_box.attach(not_lbl_w,0,1,1,1)
        not_lbl_w.set_halign(1)
        not_w_spinbtn = Gtk.SpinButton.new_with_range(0,4000,1)
        not_w_spinbtn.set_value(self._parent.not_width)
        self.page5_box.attach_next_to(not_w_spinbtn,not_lbl_w,1,1,1)
        not_w_spinbtn.connect('value-changed', self.on_not_wh_spinbtn, "w")
        not_w_spinbtn.set_input_purpose(Gtk.InputPurpose.DIGITS)
        # window height
        not_lbl_h = Gtk.Label(label=HEIGHT)
        not_lbl_h.set_tooltip_text(NOT_HEIGHT_MSG1)
        self.page5_box.attach(not_lbl_h,0,2,1,1)
        not_lbl_h.set_halign(1)
        not_h_spinbtn = Gtk.SpinButton.new_with_range(0,4000,1)
        not_h_spinbtn.set_value(self._parent.not_height)
        self.page5_box.attach_next_to(not_h_spinbtn,not_lbl_h,1,1,1)
        not_h_spinbtn.connect('value-changed', self.on_not_wh_spinbtn, "h")
        not_h_spinbtn.set_input_purpose(Gtk.InputPurpose.DIGITS)
        # icon size
        not_lbl_i = Gtk.Label(label=ICON_SIZE)
        self.page5_box.attach(not_lbl_i,0,3,1,1)
        not_lbl_i.set_halign(1)
        not_i_spinbtn = Gtk.SpinButton.new_with_range(0,2048,1)
        not_i_spinbtn.set_value(self._parent.not_icon_size)
        self.page5_box.attach_next_to(not_i_spinbtn,not_lbl_i,1,1,1)
        not_i_spinbtn.connect('value-changed', self.on_not_wh_spinbtn, "i")
        not_i_spinbtn.set_input_purpose(Gtk.InputPurpose.DIGITS)
        # # do not disturb
        # not_lbl_dnd = Gtk.Label(label="Do not disturb (at start)")
        # self.page5_box.attach(not_lbl_dnd,0,4,1,1)
        # not_lbl_dnd.set_halign(1)
        # dnd_combo = Gtk.ComboBoxText.new()
        # dnd_combo.append_text("Not active")
        # dnd_combo.append_text("Not for urgent")
        # dnd_combo.append_text("Active")
        # dnd_combo.set_active(self._parent.not_dnd)
        # dnd_combo.connect('changed', self.on_dnd_combo)
        # self.page5_box.attach_next_to(dnd_combo,not_lbl_dnd,1,1,1)
        # sounds
        not_lbl_sound = Gtk.Label(label=PLAY_SOUND)
        not_lbl_sound.set_tooltip_text(IF_EXTERNAL)
        self.page5_box.attach(not_lbl_sound,0,5,1,1)
        not_lbl_sound.set_halign(1)
        snd_combo = Gtk.ComboBoxText.new()
        snd_combo.append_text(NO_SOUNDS)
        snd_combo.append_text(INT_PLAYER)
        snd_combo.append_text(EXT_PLAYER)
        snd_combo.connect('changed', self.on_snd_combo)
        self.page5_box.attach_next_to(snd_combo,not_lbl_sound,1,1,1)
        self.entry_sound = Gtk.Entry.new()
        self.entry_sound.connect('changed', self.on_entry_sound)
        self.page5_box.attach(self.entry_sound,1,6,1,1)
        if self._parent.not_sounds in [0,1]:
            snd_combo.set_active(self._parent.not_sounds)
            self.entry_sound.set_state_flags(Gtk.StateFlags.INSENSITIVE, True)
        elif isinstance(self._parent.not_sounds, str):
            snd_combo.set_active(2)
            self.entry_sound.set_text(self._parent.not_sounds)
        # bottom limit
        not_lbl_l = Gtk.Label(label=BOTTOM_LIMIT)
        not_lbl_l.set_tooltip_text(BOTTOM_LIMIT_MSG1)
        self.page5_box.attach(not_lbl_l,0,7,1,1)
        not_lbl_l.set_halign(1)
        not_l_spinbtn = Gtk.SpinButton.new_with_range(0,5000,1)
        not_l_spinbtn.set_value(self._parent.not_bottom_limit)
        self.page5_box.attach_next_to(not_l_spinbtn,not_lbl_l,1,1,1)
        not_l_spinbtn.connect('value-changed', self.on_not_wh_spinbtn, "l")
        not_l_spinbtn.set_input_purpose(Gtk.InputPurpose.DIGITS)
        # applications to skip
        not_lbl_no = Gtk.Label(label=APP_SKIP)
        self.page5_box.attach(not_lbl_no,0,8,1,1)
        not_lbl_no.set_halign(1)
        self.entry_not_no = Gtk.Entry.new()
        self.entry_not_no.set_text(self._parent.skip_apps)
        self.page5_box.attach(self.entry_not_no,1,8,1,1)
        self.entry_not_no.connect('changed', self.on_entry_not_no)
        
        ## OTHER SETTINGS
        _lbl_advice = Gtk.Label(label=RESTART_NEEDED2)
        _lbl_advice.set_halign(3)
        self.page6_box.attach(_lbl_advice,0,0,2,1)
        
        _lbl_pad = Gtk.Label(label=INNER_WIN_PAD)
        self.page6_box.attach(_lbl_pad,0,1,1,1)
        _lbl_pad.set_halign(1)
        _pad_spinbtn = Gtk.SpinButton.new_with_range(0,50,1)
        _pad_spinbtn.set_value(_pad)
        self.page6_box.attach_next_to(_pad_spinbtn,_lbl_pad,1,1,1)
        _pad_spinbtn.connect('value-changed', self.on_other_spinbtn, "pad")
        _pad_spinbtn.set_input_purpose(Gtk.InputPurpose.DIGITS)
        
        # the notification server - enable/disable
        not_lbl_enabled = Gtk.Label(label=ENABLED1)
        self.page6_box.attach(not_lbl_enabled,0,3,1,1)
        not_lbl_enabled.set_halign(1)
        not_lbl_enabled_sw = Gtk.Switch.new()
        not_lbl_enabled_sw.set_halign(1)
        not_lbl_enabled_sw.set_active(self._parent.not_use)
        not_lbl_enabled_sw.connect('notify::active', self.on_switch, "notification")
        self.page6_box.attach_next_to(not_lbl_enabled_sw,not_lbl_enabled,1,1,1)
        
        _lbl_use_tray = Gtk.Label(label=USE_TRAY2)
        self.page6_box.attach(_lbl_use_tray,0,4,1,1)
        _lbl_use_tray.set_halign(1)
        use_tray_combo = Gtk.ComboBoxText.new()
        use_tray_combo.append_text(NO2)
        use_tray_combo.append_text(YES2)
        use_tray_combo.set_active(USE_TRAY)
        use_tray_combo.connect('changed', self.on_other_combo, "tray")
        self.page6_box.attach_next_to(use_tray_combo,_lbl_use_tray,1,1,1)
        
        taskbar_lbl = Gtk.Label(label=USE_TRAY_MSG)
        self.page6_box.attach(taskbar_lbl,0,5,1,1)
        taskbar_lbl.set_halign(1)
        use_taskbar_combo = Gtk.ComboBoxText.new()
        use_taskbar_combo.append_text(NO3)
        use_taskbar_combo.append_text(LEFT3)
        use_taskbar_combo.append_text(RIGHT3)
        use_taskbar_combo.append_text(CENTER3)
        use_taskbar_combo.set_active(USE_TASKBAR)
        use_taskbar_combo.connect('changed', self.on_other_combo, "taskbar")
        self.page6_box.attach_next_to(use_taskbar_combo,taskbar_lbl,1,1,1)
        
        _lbl_double_click = Gtk.Label(label=DOUBLE_CLICK_MSG)
        self.page6_box.attach(_lbl_double_click,0,6,1,1)
        _lbl_double_click.set_halign(1)
        double_click_combo = Gtk.ComboBoxText.new()
        double_click_combo.append_text(NO2)
        double_click_combo.append_text(YES2)
        double_click_combo.set_active(DOUBLE_CLICK)
        double_click_combo.connect('changed', self.on_other_combo, "click")
        self.page6_box.attach_next_to(double_click_combo,_lbl_double_click,1,1,1)
        
        # USE_CSS = _other_settings_conf["use-css"]
        _lbl_use_css = Gtk.Label(label=USE_CUSTOM_CSS)
        self.page6_box.attach(_lbl_use_css,0,7,1,1)
        _lbl_use_css.set_halign(1)
        double_click_css = Gtk.ComboBoxText.new()
        double_click_css.append_text(NO2)
        double_click_css.append_text(YES2)
        double_click_css.set_active(USE_CSS)
        double_click_css.connect('changed', self.on_other_combo, "css")
        self.page6_box.attach_next_to(double_click_css,_lbl_use_css,1,1,1)
        
        # language
        lbl_lang = Gtk.Label(label=LANGUAGE_MSG)
        self.page6_box.attach(lbl_lang,0,8,1,1)
        lbl_lang.set_halign(1)
        lang_combo = Gtk.ComboBoxText.new()
        lang_combo.connect('changed', self.on_other_combo, "lang")
        self.page6_box.attach_next_to(lang_combo,lbl_lang,1,1,1)
        # 
        for el in _lang_list:
            _lang_name = el.split(".")[0]
            lang_combo.append_text(_lang_name)
        
        ###########
        self.show_all()
        self.set_keep_above(True)
    
    def delete_event(self, widget, event=None):
        self._parent.on_close_dialog_conf()
        return True
    
    ### other settings
    def on_other_spinbtn(self, btn, _type):
        if _type == "pad":
            _other_settings_conf["pad-value"] = btn.get_value_as_int()
        try:
            _ff = open(_other_settings_config_file,"w")
            _data_json = _other_settings_conf
            json.dump(_data_json, _ff, indent = 4)
            _ff.close()
        except:
            pass
        
    def on_other_combo(self, cb, _type):
        if _type == "tray":
            _other_settings_conf["use-tray"] = cb.get_active()
        elif _type == "click":
            _other_settings_conf["double-click"] = cb.get_active()
        elif _type == "taskbar":
            _other_settings_conf["use-taskbar"] = cb.get_active()
        elif _type == "css":
            _other_settings_conf["use-css"] = cb.get_active()
        elif _type == "lang":
            _lang_code = cb.get_active_text()
            _new_lang_path = os.path.join(_curr_dir,"langs",_lang_code+".py")
            if os.path.exists(_new_lang_path):
                try:
                    _lang_path = os.path.join(_curr_dir,"lang.py")
                    if os.path.exists(_lang_path):
                        os.unlink(_lang_path)
                    _src = _new_lang_path
                    _dst = _lang_path
                    shutil.copyfile(_src, _dst)
                except:
                    pass
        try:
            _ff = open(_other_settings_config_file,"w")
            _data_json = _other_settings_conf
            json.dump(_data_json, _ff, indent = 4)
            _ff.close()
        except:
            pass
        
    ### menu w h ci ii iw ls
    def on_menu_wh_spinbtn(self, btn, _type):
        self._parent.set_menu_cp(_type, btn.get_value_as_int())
    
    def on_entry_menu(self, _entry, _type):
        self._parent.entry_menu(_type, _entry.get_text())
        
    def on_menu_combo(self, btn, _type):
        self._parent.on_menu_win_position(_type, btn.get_active())
    
    ### PANEL
    def on_width_spinbtn(self, btn):
        self._parent.set_width_size( btn.get_value_as_int())
    
    def on_size_spinbtn(self, btn):
        self._parent.set_self_size(btn.get_value_as_int())
    
    def on_corner_spinbtn(self, btn):
        self._parent.set_self_corners(0, btn.get_value_as_int())
        
    def on_corner_spinbtn2(self, btn):
        self._parent.set_self_corners(1, btn.get_value_as_int())
    
    def on_pos_combo(self, cb):
        self._parent.set_win_position(cb.get_active())
    
    def on_switch(self, btn, _state, _n):
        self._parent.on_switch_btn(_n, btn.get_active())
        
    def on_time_combo(self, cb):
        self._parent.on_time_combo(cb.get_active())
        
    def on_volume_entry(self, _entry):
        self._parent.set_volume_entry(_entry.get_text())
    
    #### service
    def on_service_wh_spinbtn(self, btn, _type):
        self._parent.set_service_window_size (_type, btn.get_value_as_int())
    
    # def on_timer_combo(self, cb):
        # _active = cb.get_active()
        # if _active == 1:
            # self.entry_timer.set_state_flags(Gtk.StateFlags.NORMAL, True)
            # self.entry_timer.set_text(self._parent.service_player)
        # elif _active == 0:
            # # self.entry_timer.set_text("")
            # self.entry_timer.set_state_flags(Gtk.StateFlags.INSENSITIVE, True)
        # self._parent.set_timer_combo(cb.get_active())
    
    # def on_entry_timer(self, _entry):
        # self._parent.entry_timer_text(_entry.get_text())
    
    def on_entry_commands(self, _entry, _type):
        self._parent.entry_commands(_entry.get_text(), _type)
    
    def on_note_wh_spinbtn(self, btn, _type):
        self._parent.set_note_window_size(_type, btn.get_value_as_int())
        
    #### clipboard
    def on_clip_wh_spinbtn(self, btn, _type):
        self._parent.set_clip_window_size (_type, btn.get_value_as_int())
    
    def on_clip_spinbtn(self, btn, _type):
        self._parent.set_clip_type(_type, btn.get_value_as_int())
    
    #### NOTIFICATIONS
    def on_not_wh_spinbtn(self, btn, _type):
        self._parent.set_not_window_size (_type, btn.get_value_as_int())
    
    def on_dnd_combo(self, cb):
        self._parent.set_dnd_combo(cb.get_active())
    
    def on_entry_sound(self, _entry):
        self._parent.entry_sound_text = _entry.get_text()
    
    def on_entry_not_no(self, _entry):
        self._parent.skip_apps = _entry.get_text()
    
    def on_snd_combo(self, cb):
        # cb.get_active_text()
        _active = cb.get_active()
        if _active == 2:
            self.entry_sound.set_state_flags(Gtk.StateFlags.NORMAL, True)
        else:
            self.entry_sound.set_text("")
            self._parent.entry_sound_text = ""
            self.entry_sound.set_state_flags(Gtk.StateFlags.INSENSITIVE, True)
        self._parent.set_sound_combo(cb.get_active())


class labelThread(Thread):
    
    def __init__(self, label, _file, q, event, _type):
        self.label = label
        self._file = _file
        self.q = q
        self.event = event
        self._type = _type
        self.run()
    
    def run(self):
        is_true = 1
        if is_true == 0:
            return
        if self.event.is_set():
            return
        
        cmd = [self._file]
        
        if self._type == 2:
            p = Popen(cmd, stdout=PIPE, bufsize=1, shell=False, universal_newlines=True)
            self.q.put_nowait(p)
            _line = p.stdout.readline()
            self.label.set_text(_line.strip("\n"))
            while _line and is_true:
                _line = p.stdout.readline()
                self.label.set_text(_line.strip("\n"))
        
############## notifications ##############


def dbus_to_python(data):
    if isinstance(data, dbus.String):
        data = str(data)
    elif isinstance(data, dbus.Boolean):
        data = bool(data)
    elif isinstance(data, dbus.Int64):
        data = int(data)
    elif isinstance(data, dbus.Double):
        data = float(data)
    elif isinstance(data, dbus.Byte):
        data = int(data)
    elif isinstance(data, dbus.UInt32):
        data = int(data)
    elif isinstance(data, dbus.Array):
        data = [dbus_to_python(value) for value in data]
    elif isinstance(data, dbus.Dictionary):
        new_data = dict()
        for key in data.keys():
            new_data[dbus_to_python(key)] = dbus_to_python(data[key])
        data = new_data
    return data

# find and return the hint
def _on_hints(_hints, _value):
    if _value in _hints:
        # return _hints[_value]
        return dbus_to_python(_hints[_value])
    return None

class notificationWin(Gtk.Window):
    def __init__(self, _parent, args):
        super().__init__()
        self._notifier = _parent
        # self.set_transient_for(self._parent)
        # self.set_modal(True)
        
        _x = args[0]
        _y = args[1]
        _appname = dbus_to_python(args[2])
        # _pixbuf = args[3] # pixbuf or None
        _icon = args[3]
        _summary = dbus_to_python(args[4])
        _body = dbus_to_python(args[5])
        _timeout = dbus_to_python(args[6])
        _hints = args[7]
        _actions = args[8]
        _replaceid = args[9]
        # self.__replaceid = _replaceid
        
        self.not_width = self._notifier._parent.not_width
        self.not_height = self._notifier._parent.not_height
        
        # hints: "desktop-entry" "image-path" "transient" "urgency" "value"
        #  "suppress-sound" "sound-file" "sound-name"
        
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_namespace(self, "notificationwin")
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.RIGHT, 6 + _x)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, 6 + _y)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, 1)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, 1)
        
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.NONE)
        
        self.self_style_context = self.get_style_context()
        self.self_style_context.add_class("notificationwin")
        
        self.connect('show', self.on_show)
        
        self.set_size_request(self.not_width, self.not_height)
        self.main_box = Gtk.Box.new(1,0)
        self.add(self.main_box)
        
        self.btn_icon_box = Gtk.Box.new(0,0)
        # self.btn_icon_box.set_halign(2)
        self.main_box.pack_start(self.btn_icon_box,True,True,0)
        
        #########
        self._not_path = os.path.join(_curr_dir,"mynots")
        _ICON_SIZE = self._notifier._parent.not_icon_size
        # self.not_width = self._parent._parent.not_width
        # self.not_height = self._parent._parent.not_height
        
        _pixbuf = None
        _desktop_entry = _on_hints(_hints, "desktop-entry")
        ret_icon = None
        #
        if _desktop_entry:
            ret_icon = self._on_desktop_entry(os.path.basename(_desktop_entry))
        _not_name =  str(int(time.time()))
        _notification_path = os.path.join(self._not_path, _not_name)
        _pixbuf = self._find_icon(ret_icon, _icon, _hints, _ICON_SIZE)
        #
        #########
        ###########
        _is_transient = _on_hints(_hints, "transient")
        # write the notification content
        if not _is_transient and STORE_NOTIFICATIONS:
            try:
                if os.access(self._not_path,os.W_OK):
                    os.makedirs(_notification_path)
                    ff = open(os.path.join(_notification_path,"notification"), "w")
                    ff.write(_appname+"\n\n\n@\n\n\n"+_summary+"\n\n\n@\n\n\n"+_body)
                    ff.close()
                    if _pixbuf:
                        _pixbuf.savev(os.path.join(_notification_path,"image.png"),"png",None,None)
            except:
                pass
        #################
        
        if _pixbuf:
            _img = Gtk.Image.new_from_pixbuf(_pixbuf)
            self.btn_icon_box.pack_start(_img,False,True,4)
        
        self.second_box = Gtk.Box.new(1,0)
        self.btn_icon_box.pack_start(self.second_box,True,True,0)
        
        # app - summary - body : in second_box vertical
        if _summary:
            _lbl_summary = Gtk.Label(label="<b>"+_summary+"</b>")
            _lbl_summary.set_use_markup(True)
            _lbl_summary.set_halign(1)
            _lbl_summary.set_line_wrap(True)
            _lbl_summary.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
            if _body:
                _lbl_summary.set_valign(2)
            else:
                _lbl_summary.set_valign(3)
            self.second_box.pack_start(_lbl_summary,True,True,_pad)
        #
        if _body:
            _lbl_body = Gtk.Label(label=_body)
            _lbl_body.set_halign(1)
            _lbl_body.set_use_markup(True)
            _lbl_body.set_line_wrap(True)
            _lbl_body.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
            if _summary:
                _lbl_body.set_valign(1)
            else:
                _lbl_body.set_valign(3)
            self.second_box.pack_start(_lbl_body,True,True,_pad)
        
        self.close_btn = Gtk.Button.new()
        self.close_btn.set_name("closebtn")
        conf_img = Gtk.Image.new_from_icon_name("stock_close", 1)
        self.close_btn.set_image(conf_img)
        self.close_btn.set_relief(Gtk.ReliefStyle.NONE)
        self.close_btn.set_halign(2)
        self.close_btn.set_valign(1)
        # self.conf_btn.props.hexpand = True
        # self.conf_btn.halign = Gtk.Align.FILL
        # self.conf_btn.valign = Gtk.Align.START
        self.close_btn.connect('clicked', self.on_close_btn)
        self.btn_icon_box.pack_start(self.close_btn,False,False,0)
        self.main_box.set_margin_start(_pad)
        # self.main_box.set_margin_end(_pad)
        
        # action buttons in main_box
        if _actions:
            _actions_box = Gtk.Box.new(0,0)
            self.main_box.add(_actions_box)
            _actions_box.set_halign(3)
            for _ee in _actions[::2]:
                btn_name = _actions[_actions.index(_ee)+1]
                _btn = Gtk.Button(label=btn_name)
                _btn.set_relief(Gtk.ReliefStyle.NONE)
                _ellipsize = Pango.EllipsizeMode.END
                _w = _btn.get_child()
                if isinstance(_w, Gtk.Label):
                    _w.set_ellipsize(_ellipsize)
                _btn.connect('clicked',self._on_button_callback, _replaceid, _ee)
                _actions_box.add(_btn)
        
        self.connect('delete-event', self.on_close_win,_replaceid)
        self.connect('destroy-event', self.on_close_win,_replaceid)
        
        # the geometry of this window
        self._value = None
        
        self.show_all()
        
        #################
        # 0 low - 1 normal - 2 critical
        _urgency = _on_hints(_hints, "urgency")
        
        # sounds
        _dnd_file = os.path.join(_curr_dir,"do_not_disturb_mode")
        # if self.no_sound != 0 and not os.path.exists(_dnd_file):
        if self._notifier._parent.not_sounds != 0 and not os.path.exists(_dnd_file):
            if self._notifier.not_dnd == 0 or (self._notifier.not_dnd == 1 and _urgency == 2):
                _no_sound = _on_hints(_hints, "suppress-sound")
                _soundfile = _on_hints(_hints, "sound-file")
                if not _soundfile:
                    _soundfile = _on_hints(_hints, "sound-name")
                #
                if not _no_sound:
                    if _soundfile:
                        self.play_sound(_soundfile)
                    else:
                        if _urgency == 1 or _urgency == None:
                            self.play_sound(os.path.join(_curr_dir, "sounds/urgency-normal.wav"))
                        elif _urgency == 2:
                            self.play_sound(os.path.join(_curr_dir, "sounds/urgency-critical.wav"))

    # action button pressed
    def _on_button_callback(self, _btn, _replaceid, _action):
        self._notifier.ActionInvoked(_replaceid, _action)
        self.close()
    
    def on_close(self,_replaceid):
        self._notifier.NotificationClosed(_replaceid, 3)
        for el in self._notifier.list_notifications[:]:
            if el[0] == self:
                self._notifier.list_notifications.remove(el)
                if len(self._notifier.list_notifications) == 0:
                    self._notifier._y = 0
                break
    
    def on_close_win(self,w,e,_replaceid):
        self.on_close(_replaceid)
        self.close()
    
    def on_close_btn(self, btn):
        self.close()
        
    def on_show(self, widget):
        self._value = self.get_window().get_geometry()
    
    # find the icon from the desktop file
    def _on_desktop_entry(self, _desktop):
        app_dirs_user = [os.path.join(os.path.expanduser("~"), ".local/share/applications")]
        app_dirs_system = ["/usr/share/applications", "/usr/local/share/applications"]
        _ddir = app_dirs_user+app_dirs_system
        _icon = None
        for dd in _ddir:
            if os.path.exists(dd):
                for ff in os.listdir(dd):
                    if os.path.basename(ff) == _desktop+".desktop":
                        try:
                            _ap = Gio.DesktopAppInfo.new_from_filename(os.path.join(dd,ff))
                            _icon = _ap.get_icon()
                            if _icon:
                                if isinstance(_icon,Gio.ThemedIcon):
                                    _icon = _icon.to_string()
                                elif isinstance(_icon,Gio.FileIcon):
                                    _icon = _icon.get_file().get_path()
                                return _icon
                            else:
                                return None
                        except:
                            return None
        return None
    
    # desktop_icon _icon _hints user_icon_size
    # priority: image-data image-path/application_icon
    def _find_icon(self, ret_icon, _icon, _hints, ICON_SIZE):
        _image_data = _on_hints(_hints, "image-data")
        _icon_data = _on_hints(_hints, "icon_data")
        pixbuf = None
        if _image_data or _icon_data:
            if _image_data:
                _image_data = _image_data
            else:
                _image_data = _icon_data
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_bytes(
                        width=_image_data[0],
                        height=_image_data[1],
                        has_alpha=_image_data[3],
                        data=GLib.Bytes.new(_image_data[6]),
                        colorspace=GdkPixbuf.Colorspace.RGB,
                        rowstride=_image_data[2],
                        bits_per_sample=_image_data[4],
                        )
            except:
                pass
            if pixbuf:
                return pixbuf.scale_simple(ICON_SIZE,ICON_SIZE,GdkPixbuf.InterpType.BILINEAR)
        
        _image_path = _on_hints(_hints, "image-path")
        if _image_path:
            if _image_path[0:7] == "file://":
                _image_path = _image_path[7:]
            _base_dir = os.path.dirname(_image_path)
            _base_name = os.path.basename(_image_path)
            if os.path.exists(_base_dir) and os.path.exists(_image_path):
                try:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(_image_path, ICON_SIZE, ICON_SIZE, 1)
                except:
                    pass
                if pixbuf:
                    return pixbuf
            else:
                try:
                    pixbuf = Gtk.IconTheme().load_icon(_image_path, ICON_SIZE, Gtk.IconLookupFlags.FORCE_SVG)
                    pixbuf = pixbuf.scale_simple(ICON_SIZE, ICON_SIZE, GdkPixbuf.InterpType.BILINEAR)
                except:
                    pass
                if pixbuf:
                    return pixbuf
        
        if _icon:
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(_icon, ICON_SIZE, ICON_SIZE, 1)
            except:
                try:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(os.path.join(_curr_dir,"icons","wicon.png"), ICON_SIZE, ICON_SIZE, 1)
                except:
                    pass
            if pixbuf:
                return pixbuf
        
        if ret_icon:
            try:
                pixbuf = Gtk.IconTheme().load_icon(ret_icon, ICON_SIZE, Gtk.IconLookupFlags.FORCE_SVG)
            except:
                try:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(os.path.join(_curr_dir,"icons","wicon.png"), ICON_SIZE, ICON_SIZE, 1)
                except:
                    pass
            if pixbuf:
                return pixbuf
        
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(os.path.join(_curr_dir,"icons","wicon.png"), ICON_SIZE, ICON_SIZE, 1)
            if pixbuf:
                return pixbuf
        except:
            pass
        
        return None
    
    def play_sound(self, _sound):
        if self._notifier._parent.not_sounds and SOUND_PLAYER == 1:
            try:
                ctx = GSound.Context()
                ctx.init()
                ret = ctx.play_full({GSound.ATTR_EVENT_ID: _sound})
                if ret == None:
                    ret = ctx.play_full({GSound.ATTR_MEDIA_FILENAME: _sound})
            except:
                pass
        elif self._parent._parent.no_sounds not in [1,2] and SOUND_PLAYER == 1:
            _player = self._parent._parent.no_sounds
            try:
                os.system("{0} {1} &".format(_player, _sound))
            except:
                pass

class NotSave():
    nname = None
    appname = None
    summary = None
    body = None
    icon = None


class Notifier(Service.Object):
    
    def __init__(self, conn, bus, _parent):
        Service.Object.__init__(self, object_path = "/org/freedesktop/Notifications", bus_name = Service.BusName(bus, conn))
        self._parent = _parent
        self.list_notifications = []
        # self._not_path = os.path.join(_curr_dir,"mynots")
        # # 0 no - 1 yes - 2 yes/with external player
        # # self.no_sound = self._parent.not_sounds
        self.not_dnd = self._parent.not_dnd
        # top margin and _pad
        self.starting_y = 0
        self.not_pad = 2
        # top margin + _pad
        self.__y = self.starting_y+self.not_pad # static value
        self._y = self.__y # variable value
        #
        self._not_counter = 1
    
    @Service.method("org.freedesktop.Notifications", out_signature="as")
    def GetCapabilities(self):
        return ["actions", "action-icons", "body", "body-markup", "body-hyperlinks", "body-images", "icon-static", "sound"]
        
    @Service.method("org.freedesktop.Notifications", in_signature="susssasa{sv}i", out_signature="u")
    def Notify(self, appName, replacesId, appIcon, summary, body, actions, hints, expireTimeout):
        replacesId = dbus_to_python(replacesId)
        
        # # skip these applications
        # if appName in self._parent._SKIP_APPS:
            # return replacesId
        
        if "x-canonical-private-synchronous" in hints:
            replacesId = 3000
        
        # if not replacesId:
        #     replacesId = 0
        if self._not_counter == 4000:
            self._not_counter = 1
        if replacesId == 0 or not replacesId:
            replacesId = self._not_counter
            self._not_counter +=1
        elif replacesId == self._not_counter:
            self._not_counter += 1
        
        action_1 = dbus_to_python(actions)
        
        if not dbus_to_python(appIcon):
            appIcon = ""
        if action_1:
            # if expireTimeout == -1:
            expireTimeout = 10000
            self._qw(appName, summary, body, replacesId, action_1, hints, expireTimeout, appIcon)
        else:
            action_1 = []
            # if expireTimeout == -1:
            expireTimeout = 6000
            self._qw(appName, summary, body, replacesId, action_1, hints, expireTimeout, appIcon)
        
        return replacesId

    @Service.method("org.freedesktop.Notifications", in_signature="u")
    def CloseNotification(self, id):
        # reasons: 1 expired - 2 dismissed by the user - 3 from here - 4 other
        self.NotificationClosed(id, 3)

    @Service.method("org.freedesktop.Notifications", out_signature="ssss")
    def GetServerInformation(self):
        return ("mypanelnotification-server", "Homebrew", "1.0", "0.1")

    @Service.signal("org.freedesktop.Notifications", signature="uu")
    def NotificationClosed(self, id, reason):
        pass

    @Service.signal("org.freedesktop.Notifications", signature="us")
    def ActionInvoked(self, id, actionKey):
        pass
    
    @Service.signal("org.freedesktop.Notifications", signature="us")
    def ActivationToken(self, id, actionKey):
        pass
    
    def _qw(self, _appname, _summ, _body, _replaceid, _actions, _hints, _timeout, _icon):
        
        # skip these applications
        if _appname in self._parent._SKIP_APPS:
            return
        
        # # hints: "desktop-entry" "image-path" "transient" "urgency" "value"
        # #  "suppress-sound" "sound-file" "sound-name"
        # _ICON_SIZE = self._parent.not_icon_size
        # self.not_width = self._parent.not_width
        # self.not_height = self._parent.not_height
        # # # 0 no - 1 yes - 2 yes/with external player
        # # self.no_sound = self._parent.not_sounds # deactivated
        self.not_dnd = self._parent.not_dnd
        ###
        _pix = None
        ####
        #
        _found_same_id = 0
        if _replaceid != 0:
            for _el in self.list_notifications:
                if _el[1] == _replaceid:
                    _found_same_id = 1
                    _el[0].close()
                    break
        # 
        if _found_same_id == 0:
            if self.list_notifications:
                self._y = self.list_notifications[-1][2]+self.not_pad
            else:
                self._y = self.__y
        
        if self._y > self._parent.screen_height - self._parent.not_bottom_limit:
            self._y = self.__y
        
        # 0 low - 1 normal - 2 critical
        _urgency = _on_hints(_hints, "urgency")
        
        NW = None
        _dnd_file = os.path.join(_curr_dir,"do_not_disturb_mode")
        #
        if os.path.exists(_dnd_file):
            # never show the notification
            if self.not_dnd == 0:
                return
        if ( os.path.exists(_dnd_file) == False ) or ( (os.path.exists(_dnd_file) == True) and (self.not_dnd == 1 and _urgency == 2)):
            # NW = notificationWin(self, (0, self._y, _appname, _pix, _summ, _body, _timeout, _hints, _actions, _replaceid))
            NW = notificationWin(self, (0, self._y, _appname, _icon, _summ, _body, _timeout, _hints, _actions, _replaceid))
            #
            # _NW_height = NW.get_size_request().height
            _NW_height = NW._value.height
            self._y += _NW_height
            #
            self.list_notifications.append([NW,_replaceid, self._y])
            self._close_notification(_timeout,NW)
       
    def on_close_notification(self, nw):
        nw.close()
        
    def _close_notification(self,_t,nw):
        GLib.timeout_add(_t, self.on_close_notification, nw)
    

## clipboard daemon wayland
class daemonClipW():
    def __init__(self, _clips_path, _parent):
        self.clipboardpid = None
        
    def _start(self):
        try:
            os.system("killall wl-paste")
        except:
            pass
        # cmd = "/usr/bin/wl-paste -t text/plain -w ./wclipboard.sh".split()
        cmd = "/usr/bin/wl-paste -t text -w ./wclipboard.py".split()
        (self.clipboardpid, _in, _out, _err) = GLib.spawn_async(cmd,flags=GLib.SpawnFlags.DEFAULT, standard_output=True, standard_error=True)
    
    def _stop(self):
        try:
            os.system(f"kill -9 {self.clipboardpid}")
        except:
            pass


############ taskbar

if USE_TASKBAR:
    # Signal hub + Wayland connection
    class taskbarContext(GObject.Object, WaylandConnection):
        def __init__(self):
            GObject.Object.__init__(self)
            WaylandConnection.__init__(self, eventloop_integration=GLibIntegration())
            # self.add_signal('periodic_update', tuple())
            self.add_signal('wayland_sync')
            self.manager = TaskManager(self)

        def add_signal(self, signal_name, signal_args=None):
            if signal_args is None:
                signal_args = (GObject.TYPE_PYOBJECT,)
            GObject.signal_new(
                signal_name, self,
                GObject.SignalFlags.RUN_LAST,
                GObject.TYPE_PYOBJECT, signal_args
            )

        def on_initial_sync(self, data):
            super().on_initial_sync(data)
            self.seat = self.display.seat
            self.emit('wayland_sync', self)

if USE_TASKBAR:
    # Foreign Toplevel / GObject signal emitter bridge
    class ToplevelManager(ForeignTopLevel):
        def __init__(self, wl_connection, context):
            super().__init__(wl_connection)
            self.context = context

        def on_toplevel_created(self, toplevel):
            self.context.emit('toplevel_new', toplevel)

        def on_toplevel_synced(self, toplevel):
            self.context.emit('toplevel_synced', toplevel)

        def on_toplevel_closed(self, toplevel):
            self.context.emit('toplevel_closed', toplevel)

# Foreign Toplevel API
# Supports direct calls or being used as event handler for a GTK widget:
# - manager.app_toggle(toplevel)
# - some_button.connect('clicked', manager.app_toggle, toplevel)
class TaskManager:
    def __init__(self, context):
        context.add_signal('toplevel_new')
        context.add_signal('toplevel_synced')
        context.add_signal('toplevel_closed')
        context.connect('wayland_sync', self.on_wl_sync)
        self.context = context
        self.manager = None

    def on_wl_sync(self, context, wl_connection):
        self.manager = ToplevelManager(wl_connection, context)

    def app_toggle(self, *args):
        toplevel = args[-1]
        if 'activated' in toplevel.states:
            toplevel.set_minimize(True)
        else:
            self.app_activate(toplevel)

    def app_activate(self, *args):
        toplevel = args[-1]
        toplevel.activate(self.context.seat)

    def app_minimize(self, *args):
        toplevel = args[-1]
        if 'minimized' in toplevel.states:
            return
        toplevel.set_minimize(True)

    def app_toggle_minimize(self, *args):
        toplevel = args[-1]
        toplevel.set_minimize('minimized' not in toplevel.states)

    def app_toggle_maximize(self, *args):
        toplevel = args[-1]
        toplevel.set_maximize('maximized' not in toplevel.states)

    def app_toggle_fullscreen(self, *args):
        toplevel = args[-1]
        toplevel.set_fullscreen('fullscreen' not in toplevel.states)

    def app_close(self, *args):
        toplevel = args[-1]
        toplevel.close()

####################


win = MyWindow()

if USE_TRAY:
    owner_id = Gio.bus_own_name(
            Gio.BusType.SESSION,
            NODE_INFO.interfaces[0].name,
            Gio.BusNameOwnerFlags.NONE,
            win.on_bus_acquired,
            None,
            win.on_name_lost,
            )

try:
    Gtk.main()
finally:
    if USE_TRAY:
        Gio.bus_unown_name(owner_id)
