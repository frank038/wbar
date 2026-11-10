#!/usr/bin/env python3

import sys,os
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk,Gio,GLib
from menueditorlang import *

freedesktop_main_categories = [TCAV,TCDEV,TCED,TCGM,TCGR,TCNW,TCOFF,TCSETT,TCSYS,TCUT]

self_main = None
_HOME = os.path.expanduser("~")

# the dir of the application desktop files
app_dir_user = _HOME+"/.local/share/applications"


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, _file, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_default_size(400, 300)
        self.app_ = self.get_application()
        global self_main
        self_main = self
        #
        self.headerbar = Gtk.HeaderBar.new()
        self.set_titlebar(self.headerbar)
        #
        _w = Gtk.Box.new(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        _w.set_size_request(1,-1)
        _w.set_hexpand(False)
        self.headerbar.set_title_widget(_w)
        self.headerbar.set_show_title_buttons(False)
        # remove the title widget
        hb_tw = self.headerbar.get_title_widget()
        self.headerbar.remove(hb_tw)
        ### buttons: delete - accept - close
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.headerbar.pack_start(btn_box)
        #
        btn_delete = Gtk.Button(label=MBDELETE)
        btn_delete.set_halign(Gtk.Align.START)
        btn_box.append(btn_delete)
        #
        _box1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=0)
        _box1.set_hexpand(True)
        btn_box.append(_box1)
        self.title_lbl = Gtk.Label(label=TMENU)
        self.title_lbl.set_halign(Gtk.Align.FILL)
        self.title_lbl.set_hexpand(True)
        _box1.append(self.title_lbl)
        #
        btn_accept = Gtk.Button(label=MBACCEPT)
        btn_accept.set_halign(Gtk.Align.END)
        btn_box.append(btn_accept)
        #
        btn_close = Gtk.Button(label=MBCLOSE)
        btn_close.set_halign(Gtk.Align.END)
        btn_box.append(btn_close)
        btn_close.connect("clicked", lambda w: self.destroy())
        ####
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(self.main_box)
        #
        self.grid1 = Gtk.Grid.new()
        self.grid1.set_column_spacing(10)
        self.grid1.set_row_spacing(4)
        self.main_box.append(self.grid1)
        # file name
        filename_lbl = Gtk.Label(label=MFILENAME)
        self.grid1.attach(filename_lbl,0,1,1,1)
        self.buffer_filename = Gtk.EntryBuffer.new("", -1)
        self.entry_filename = Gtk.Entry.new_with_buffer(self.buffer_filename)
        self.entry_filename.set_hexpand(True)
        self.grid1.attach_next_to(self.entry_filename,filename_lbl,1,1,1)
        # name
        name_lbl = Gtk.Label(label=MNAME)
        self.grid1.attach(name_lbl,0,2,1,1)
        self.buffer_name = Gtk.EntryBuffer.new("", -1)
        self.entry_name = Gtk.Entry.new_with_buffer(self.buffer_name)
        self.grid1.attach_next_to(self.entry_name,name_lbl,1,1,1)
        # generic name
        genericname_lbl = Gtk.Label(label=MGNAME)
        self.grid1.attach(genericname_lbl,0,3,1,1)
        self.buffer_gname = Gtk.EntryBuffer.new("", -1)
        self.entry_gname = Gtk.Entry.new_with_buffer(self.buffer_gname)
        self.grid1.attach_next_to(self.entry_gname,genericname_lbl,1,1,1)
        # executable
        executable_btn = Gtk.Button(label=MEXECUTABLE)
        self.grid1.attach(executable_btn,0,4,1,1)
        self.buffer_exec = Gtk.EntryBuffer.new("", -1)
        self.entry_exec = Gtk.Entry.new_with_buffer(self.buffer_exec)
        self.grid1.attach_next_to(self.entry_exec,executable_btn,1,1,1)
        executable_btn.connect("clicked", self.on_open, self.buffer_exec, 1)
        # try executable
        tryexecutable_btn = Gtk.Button(label=MTRYEXECUTABLE)
        self.grid1.attach(tryexecutable_btn,0,5,1,1)
        self.buffer_texec = Gtk.EntryBuffer.new("", -1)
        self.entry_texec = Gtk.Entry.new_with_buffer(self.buffer_texec)
        self.grid1.attach_next_to(self.entry_texec,tryexecutable_btn,1,1,1)
        tryexecutable_btn.connect("clicked", self.on_open, self.buffer_texec, 1)
        # path
        path_btn = Gtk.Button(label=MPATH)
        self.grid1.attach(path_btn,0,6,1,1)
        self.buffer_path = Gtk.EntryBuffer.new("", -1)
        self.entry_path = Gtk.Entry.new_with_buffer(self.buffer_path)
        self.grid1.attach_next_to(self.entry_path,path_btn,1,1,1)
        path_btn.connect("clicked", self.on_open, self.buffer_path, 2)
        # category
        category_lbl = Gtk.Label(label=MCATEGORY)
        self.grid1.attach(category_lbl,0,7,1,1)
        self.cat_dd = Gtk.DropDown.new_from_strings(freedesktop_main_categories)
        self.grid1.attach_next_to(self.cat_dd,category_lbl,1,1,1)
        # mimetypes
        mimetypes_lbl = Gtk.Label(label=MMIMETYPES)
        self.grid1.attach(mimetypes_lbl,0,8,1,1)
        self.buffer_mime = Gtk.EntryBuffer.new("", -1)
        self.entry_mime = Gtk.Entry.new_with_buffer(self.buffer_mime)
        self.grid1.attach_next_to(self.entry_mime,mimetypes_lbl,1,1,1)
        # keywords
        keywords_lbl = Gtk.Label(label=MKEYWORDS)
        self.grid1.attach(keywords_lbl,0,9,1,1)
        self.buffer_keyw = Gtk.EntryBuffer.new("", -1)
        self.entry_keyw = Gtk.Entry.new_with_buffer(self.buffer_keyw)
        self.grid1.attach_next_to(self.entry_keyw,keywords_lbl,1,1,1)
        # icon
        icon_btn = Gtk.Button(label=MICON)
        self.grid1.attach(icon_btn,0,10,1,1)
        self.buffer_icon = Gtk.EntryBuffer.new("", -1)
        self.entry_icon = Gtk.Entry.new_with_buffer(self.buffer_icon)
        self.grid1.attach_next_to(self.entry_icon,icon_btn,1,1,1)
        icon_btn.connect("clicked", self.on_open, self.buffer_icon, 1)
        # comment
        comment_lbl = Gtk.Label(label=MCOMMENT)
        self.grid1.attach(comment_lbl,0,11,1,1)
        self.buffer_comm = Gtk.EntryBuffer.new("", -1)
        self.entry_comm = Gtk.Entry.new_with_buffer(self.buffer_comm)
        self.grid1.attach_next_to(self.entry_comm,comment_lbl,1,1,1)
        ### labels mandatory and optional
        service_lbl = Gtk.Label(label=MSERVICE)
        self.grid1.attach(service_lbl,0,12,2,1)
        ### check buttons: run in terminal - no display - hidden
        box_chkbtn = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.grid1.attach(box_chkbtn,0,13,2,1)
        box_chkbtn.set_hexpand(True)
        #
        self.runterm_chk = Gtk.CheckButton.new_with_label(label=MRUNINTERMINAL)
        box_chkbtn.append(self.runterm_chk)
        self.runterm_chk.set_hexpand(True)
        #
        self.nodisplay_chk = Gtk.CheckButton.new_with_label(label=MNODISPLAY)
        box_chkbtn.append(self.nodisplay_chk)
        self.nodisplay_chk.set_hexpand(True)
        #
        self.hidden_chk = Gtk.CheckButton.new_with_label(label=MHIDDEN)
        box_chkbtn.append(self.hidden_chk)
        self.hidden_chk.set_hexpand(True)
        ###
        if _file:
            # file to open full path
            self.file_name = _file.get_path()
            self.new_file = None
            if not os.path.exists(sys.argv[1]):
                sys.exit()
            else:
                btn_delete.connect("clicked", self.on_delete_desktopfile, self.file_name)
                 # file name
                self._file_name_tmp = os.path.basename(self.file_name)
                # file name without the suffix .desktop
                self._file_name = self._file_name_tmp[:len(self._file_name_tmp)-len(".desktop")]
                #
                # self.f_modify(os.access(self.file_name, os.W_OK))
                if self.file_name.startswith(_HOME):
                    self.title_lbl.set_label(self._file_name)
                    self.f_modify(1)
                    btn_accept.connect("clicked", self.on_accept, self.file_name)
                else:
                    self.new_file = os.path.join(app_dir_user, self._file_name_tmp)
                    while os.path.exists(self.new_file):
                        _nt = os.path.basename(self.new_file)
                        _nt2 = _nt[:len(_nt)-len(".desktop")]
                        self.new_file = os.path.join(app_dir_user, _nt2+"_1"+".desktop")
                    new_name_tmp = os.path.basename(self.new_file)
                    self.title_lbl.set_label(new_name_tmp[:len(new_name_tmp)-len(".desktop")])
                    self.f_modify(0)
                    btn_accept.connect("clicked", self.on_accept, self.new_file)
                
    def on_accept(self, _w, file_name):
        if not self.buffer_filename.get_text().endswith(".desktop"):
            return
        elif self.buffer_filename.get_text() != os.path.basename(file_name):
            file_name = os.path.join(os.path.dirname(file_name), self.buffer_filename.get_text())
        f_content="""[Desktop Entry]
Type=Application
Version=1.0
Name={}
GenericName={}
Exec={}
TryExec={}
Path={}
Categories={};
MimeType={}
Keywords={}
Icon={}
Comment={}
Terminal={}
NoDisplay={}
Hidden={}
""".format(self.buffer_name.get_text(),self.buffer_gname.get_text(),self.buffer_exec.get_text(),self.buffer_texec.get_text(),self.buffer_path.get_text(),self.cat_dd.get_selected_item().get_string(), self.buffer_mime.get_text(), self.buffer_keyw.get_text(), self.buffer_icon.get_text(), self.buffer_comm.get_text(), str(bool(self.runterm_chk.get_active())).lower(),str(bool(self.nodisplay_chk.get_active())).lower(),str(bool(self.hidden_chk.get_active())).lower())
        #
        try:
            ffile = open(file_name, "w")
            ffile.write(f_content)
            ffile.close()
        except Exception as E:
            AlDial(self_main, str(E))
            return
        self.app_.quit()
    
    # _type: 1 is in home dir - 0 is system file
    def f_modify(self, _type):
        file_content = None
        _locale = None
        _comment_found = 0
        _name_found = 0
        _generic_name_found = 0
        _keyword_found = 0
        try:
            _locale = os.environ['LANG'].split(".")[0].split("_")[0]
        except:
            _locale = None
        #
        with open(self.file_name, "r") as ffile:
            file_content = ffile.readlines()
        # the file name
        self.buffer_filename.set_text(self._file_name_tmp,-1)
        if _type == 0:
            self.entry_filename.set_state_flags(Gtk.StateFlags.INSENSITIVE, True)
            self.entry_name.set_state_flags(Gtk.StateFlags.INSENSITIVE, True)
            self.entry_gname.set_state_flags(Gtk.StateFlags.INSENSITIVE, True)
        #
        for el in file_content:
            if el[0:9] == "Name[{}]=".format(_locale):
                self.buffer_name.set_text(el[9:].strip("\n"),-1)
                _name_found = 1
            elif _name_found == 0 and el[0:5] == "Name=":
                self.buffer_name.set_text(el[5:].strip("\n"),-1)
            elif el[0:16] == "GenericName[{}]=".format(_locale):
                self.buffer_gname.set_text(el[16:].strip("\n"),-1)
                _generic_name_found = 1
            elif _generic_name_found == 0 and el[0:12] == "GenericName=":
                self.buffer_gname.set_text(el[12:].strip("\n"),-1)
            elif el[0:5] == "Exec=":
                self.buffer_exec.set_text(el[5:].strip("\n"), -1)
            elif el[0:8] == "TryExec=":
                self.buffer_texec.set_text(el[8:].strip("\n"), -1)
            elif el[0:5] == "Path=":
                self.buffer_path.set_text(el[5:].strip("\n"), -1)
            elif el[0:11] == "Categories=":
                cat_names = el[11:].strip("\n").split(";")
                for cat_name in cat_names:
                    if cat_name in freedesktop_main_categories:
                        cb_idx = freedesktop_main_categories.index(cat_name)
                        if cb_idx != -1:
                            self.cat_dd.set_selected(cb_idx)
                            break
            elif el[0:9] == "MimeType=":
                self.buffer_mime.set_text(el[9:].strip("\n"), -1)
            elif el[0:13] == "Keywords[{}]=".format(_locale):
                self.buffer_keyw.set_text(el[13:].strip("\n"), -1)
                _keyword_found = 1
            elif _keyword_found == 0 and el[0:9] == "Keywords=":
                self.buffer_keyw.set_text(el[9:].strip("\n"), -1)
            elif el[0:5] == "Icon=":
                self.buffer_icon.set_text(el[5:].strip("\n"), -1)
            elif el[0:12] == "Comment[{}]=".format(_locale):
                _comment_found = 1
                self.buffer_comm.set_text(el[12:].strip("\n"), -1)
            elif _comment_found == 0 and el[0:8] == "Comment=":
                self.buffer_comm.set_text(el[8:].strip("\n"), -1)
            elif el[0:9] == "Terminal=":
                term_chk = el[9:].strip("\n")
                self.runterm_chk.set_active(False if term_chk=="false" else True)
            elif el[0:10] == "NoDisplay=":
                nodisp_chk = el[10:].strip("\n")
                self.nodisplay_chk.set_active(False if nodisp_chk=="false" else True)
            elif el[0:7] == "Hidden=":
                hidd_chk = el[7:].strip("\n")
                self.hidden_chk.set_active(False if hidd_chk=="false" else True)
                
    def on_open(self, _w, _buff, _type=None):
        _fd = Gtk.FileDialog.new()
        _fd.set_modal(True)
        _fd.set_initial_folder(Gio.File.new_for_path(_HOME))
        # _filter = Gtk.FileFilter.new()
        # _filter.add_pattern("*.txt")
        # _fd.set_default_filter(_filter)
        def open_callback(source_object, res, data):
            try:
                l_gfile = _fd.open_text_file_finish(res)
                _file = l_gfile[0].get_path()
                if _type == 1:
                    _buff.set_text(_file, -1)
                elif _type == 2:
                    _buff.set_text(os.path.dirname(_file), -1)
            except GLib.GError as e:
                return
        try:
            _fd.open_text_file(self, None, open_callback, None)
        except Exception as E:
            AlDial(self_main, str(E))
            
    def dialog_action(self, _obj, _res, _data=None):
        _result = _obj.choose_finish(_res)
        if _result == 0:
            try:
                os.unlink(_data)
            except Exception as E:
                AlDial(self_main, str(E))
            self.app_.quit()
        else:
            return
    
    def on_delete_desktopfile(self, _w, _path):
        if not _path.startswith(_HOME):
            return
        YNDial(self, DELMSG, "{}".format(os.path.basename(_path)), _path)
        

# yes/no dialog - close the application and check for files modified
class YNDial(Gtk.AlertDialog):
    def __init__(self, _parent, _str1, _str2, _path):
        super().__init__()
        self._parent = _parent
        self._str1 = _str1
        self._str2 = _str2
        #
        self.set_buttons([DYES, DNO])
        self.props.cancel_button = 1
        #
        self.set_message(self._str1)
        self.set_detail(self._str2)
        #
        self.choose(self._parent, None, self._parent.dialog_action, _path)

class AlDial(Gtk.AlertDialog):
    def __init__(self, _parent, _str1):
        super().__init__()
        self._parent = _parent
        self._str1 = _str1
        #
        self.set_message(self._str1)
        #
        self.show(self._parent)

class MyApp(Gtk.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._file = None

    def do_activate(self):
        active_window = self.props.active_window
        if active_window:
            active_window.present()
        else:
            self.win = MainWindow(application=self, _file=self._file)
            self.win.present()
    
    def do_open(self, _files, n_files, _data):
        if n_files > 0:
            self._file = _files[0]
        self.activate()

app = MyApp(application_id=None,flags=Gio.ApplicationFlags.HANDLES_OPEN)
app.run(sys.argv)