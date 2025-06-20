#!/usr/bin/env python3
#### v 0.9
from PyQt6 import QtCore, QtGui, QtWidgets
import sys, os
from cfg import DIALOGWIDTH


freedesktop_main_categories = ["AudioVideo","Development",
                              "Education","Game","Graphics","Network",
                              "Office","Settings","System","Utility"]

# the dir of the application desktop files
app_dir_user = os.path.expanduser("~")+"/.local/share/applications"

class appWin(QtWidgets.QWidget):
    def __init__(self, arg1=None):
        super(appWin, self).__init__()
        self.setWindowIcon(QtGui.QIcon("icons/menu.svg"))
        self.setWindowTitle("Appmenu")
        self.file_name = arg1
        # whether it is the second or more modification
        self._name_need_to_be_modified = 0
        ####### box 
        self.mainBox = QtWidgets.QGridLayout()
        self.setLayout(self.mainBox)
        #### file name
        lbl_file_name = QtWidgets.QLabel("File name *")
        self.mainBox.addWidget(lbl_file_name, 0, 0)
        self.le_file_name = QtWidgets.QLineEdit()
        self.mainBox.addWidget(self.le_file_name, 0, 1, 1, 5)
        #### name
        lbl_name = QtWidgets.QLabel("Name *")
        self.mainBox.addWidget(lbl_name, 1, 0)
        self.le_name = QtWidgets.QLineEdit()
        self.mainBox.addWidget(self.le_name, 1, 1, 1, 5)
        #### generic name
        lbl_gen_name = QtWidgets.QLabel("Generic Name")
        self.mainBox.addWidget(lbl_gen_name, 2, 0)
        self.le_gen_name = QtWidgets.QLineEdit()
        self.mainBox.addWidget(self.le_gen_name, 2, 1, 1, 5)
        #### executable
        lbl_exec = QtWidgets.QPushButton("Executable *")
        self.mainBox.addWidget(lbl_exec, 3, 0)
        self.le_exec = QtWidgets.QLineEdit()
        self.mainBox.addWidget(self.le_exec, 3, 1, 1, 5)
        lbl_exec.clicked.connect(lambda:self.f_choose(self.le_exec, "All Files (*.*)"))
        #### try executable
        lbl_exec_try = QtWidgets.QPushButton("Try Executable")
        self.mainBox.addWidget(lbl_exec_try, 4, 0)
        self.le_exec_try = QtWidgets.QLineEdit()
        self.mainBox.addWidget(self.le_exec_try, 4, 1, 1, 5)
        lbl_exec_try.clicked.connect(lambda:self.f_choose(self.le_exec_try, "All Files (*.*)"))
        #### path
        lbl_path = QtWidgets.QPushButton("Path")
        self.mainBox.addWidget(lbl_path, 5, 0)
        self.le_path = QtWidgets.QLineEdit()
        self.mainBox.addWidget(self.le_path, 5, 1, 1, 5)
        lbl_path.clicked.connect(lambda:self.f_choose(self.le_path, "All Files (*.*)"))
        #### categories
        lbl_categ = QtWidgets.QLabel("Category *")
        self.mainBox.addWidget(lbl_categ, 6, 0)
        self.combo_categ = QtWidgets.QComboBox()
        self.mainBox.addWidget(self.combo_categ, 6, 1, 1, 5)
        self.combo_categ.addItems(freedesktop_main_categories)
        #### mimetypes
        lbl_mime = QtWidgets.QLabel("Mimetypes **")
        self.mainBox.addWidget(lbl_mime, 7, 0)
        self.le_mime = QtWidgets.QLineEdit()
        self.mainBox.addWidget(self.le_mime, 7, 1, 1, 5)
        #### keywords
        lbl_keys = QtWidgets.QLabel("Keywords **")
        self.mainBox.addWidget(lbl_keys, 8, 0)
        self.le_keys = QtWidgets.QLineEdit()
        self.mainBox.addWidget(self.le_keys, 8, 1, 1, 5)
        #### icon
        lbl_icon = QtWidgets.QPushButton("Icon")
        self.mainBox.addWidget(lbl_icon, 9, 0)
        self.le_icon = QtWidgets.QLineEdit()
        self.mainBox.addWidget(self.le_icon, 9, 1, 1, 5)
        lbl_icon.clicked.connect(lambda:self.f_choose(self.le_icon, "Icons (*.png *.svg *.xpm)"))
        #### comment
        lbl_comment = QtWidgets.QLabel("Comment")
        self.mainBox.addWidget(lbl_comment, 10, 0)
        self.le_comment = QtWidgets.QLineEdit()
        self.mainBox.addWidget(self.le_comment, 10, 1, 1, 5)
        ####
        lbl_optional = QtWidgets.QLabel("(* mandatory - ** optional and separate with a semicolon)")
        self.mainBox.addWidget(lbl_optional, 11, 0, 1, 6)
        #### check buttons
        hbox_chk_btn = QtWidgets.QHBoxLayout()
        self.mainBox.addLayout(hbox_chk_btn, 12, 0, 1, 6)
        self.chk_term = QtWidgets.QCheckBox("Run in Terminal")
        hbox_chk_btn.addWidget(self.chk_term)
        self.chk_disp = QtWidgets.QCheckBox("No Display")
        hbox_chk_btn.addWidget(self.chk_disp)
        self.chk_hidd = QtWidgets.QCheckBox("Hidden")
        hbox_chk_btn.addWidget(self.chk_hidd)
        #### buttons
        self.hbox_btn = QtWidgets.QHBoxLayout()
        self.mainBox.addLayout(self.hbox_btn, 13, 0, 1, 6)
        ## delete button
        self.del_btn = QtWidgets.QPushButton("Delete")
        self.del_btn.clicked.connect(self.f_delete)
        self.hbox_btn.addWidget(self.del_btn)
        ## accept button
        self.acpt_btn = QtWidgets.QPushButton("Accept")
        self.acpt_btn.clicked.connect(self.f_accept)
        self.hbox_btn.addWidget(self.acpt_btn)
        ## close button
        self.quit_btn = QtWidgets.QPushButton("Close")
        self.quit_btn.clicked.connect(self.close)
        self.hbox_btn.addWidget(self.quit_btn)
        #
        if arg1:
            self.f_modify()
        #
        self.show()
        
    def closeEvent(self, e):
        ret = MyDialog("Question", "Close this program?", self)
        if ret.getValue() == 1:
            e.accept()
        elif ret.getValue() == 0:
            e.ignore()
        
    def f_delete(self):
        if not self.le_file_name.text() or not self.le_name.text() or not self.le_exec.text():
            MyDialog("Info", "Nothing to do.", self)
            return
        #
        if os.path.dirname(self.file_name) == app_dir_user:
            #
            ret = MyDialog("Question", "Delete?", self)
            if ret.getValue() == 1:
                try:
                    os.remove(self.file_name)
                    self.close()
                except Exception as E:
                    MyDialog("Error", str(E), self)
                    return
        else:
            MyDialog("Info", "Cannot remove a system file.", self)
            return
    
    def f_accept(self):
        if not self.le_file_name.text() or not self.le_name.text() or not self.le_exec.text():
            MyDialog("Info", "Mandatory field(s) empty.", self)
            return
        # #
        # if self._name_need_to_be_modified == self.le_name.text():
            # MyDialog("Info", "The Name field must be changed.", self)
            # return
        #
        file_name = self.le_file_name.text()
        if not file_name.endswith(".desktop"):
            file_name += ".desktop"
        file_name_path = os.path.join(app_dir_user, file_name)
        if os.path.exists(file_name_path):
            ret = MyDialog("Question", "The desktop file already exists.\nDo you want to overwrite it?", self)
            if ret.getValue() == 0:
                return
        #
        mime_types = ""
        mime_types = self.le_mime.text()
        if mime_types:
            if not mime_types[-1] == ";":
                mime_types += ";"
        #
        key_words = ""
        key_words = self.le_keys.text()
        if key_words:
            if not key_words[-1] == ";":
                key_words += ";"
        #
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
""".format(self.le_name.text(), self.le_gen_name.text(), self.le_exec.text(), self.le_exec_try.text(), self.le_path.text(), self.combo_categ.currentText(), mime_types, key_words, self.le_icon.text(), self.le_comment.text(), str(self.chk_term.isChecked()).lower(), str(self.chk_disp.isChecked()).lower(), str(self.chk_hidd.isChecked()).lower())
        #
        try:
            ffile = open(file_name_path, "w")
            ffile.write(f_content)
            ffile.close()
            MyDialog("Info", "Done.", self)
        except Exception as E:
            MyDialog("Error", str(E), self)
        #
        self.file_name = file_name_path
        #
        self.le_file_name.setText(file_name)
        self.le_file_name.setEnabled(False)
    
    def f_modify(self):
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
        #
        _file_base_name = os.path.basename(self.file_name)
        if not os.path.exists(os.path.join(app_dir_user,_file_base_name)):
            self.le_file_name.setEnabled(False)
            # i = 1
            # _base_name, _ext = os.path.splitext(_file_base_name)
            # while os.path.exists(os.path.join(app_dir_user,_base_name+"_{}".format(i)+_ext)):
                # i += 1
            # else:
                # _file_base_name = _base_name+"_{}".format(i)+_ext
        else:
            self._name_need_to_be_modified = 1
        self.le_file_name.setText(_file_base_name)
        # self.le_file_name.setEnabled(False)
        #
        for el in file_content:
            if el[0:9] == "Name[{}]=".format(_locale):
                self.le_name.setText(el[9:].strip("\n"))
                _name_found = 1
                if self._name_need_to_be_modified == 1:
                    self._name_need_to_be_modified = el[9:].strip("\n")
            elif _name_found == 0 and el[0:5] == "Name=":
                self.le_name.setText(el[5:].strip("\n"))
                if self._name_need_to_be_modified == 1:
                    self._name_need_to_be_modified = el[5:].strip("\n")
            elif el[0:16] == "GenericName[{}]=".format(_locale):
                self.le_gen_name.setText(el[16:].strip("\n"))
                _generic_name_found = 1
            elif _generic_name_found == 0 and el[0:12] == "GenericName=":
                self.le_gen_name.setText(el[12:].strip("\n"))
            elif el[0:5] == "Exec=":
                self.le_exec.setText(el[5:].strip("\n"))
            elif el[0:8] == "TryExec=":
                self.le_exec_try.setText(el[8:].strip("\n"))
            elif el[0:5] == "Path=":
                self.le_path.setText(el[5:].strip("\n"))
            elif el[0:11] == "Categories=":
                # cat_name = el[11:].strip("\n").split(";")[0]
                cat_names = el[11:].strip("\n").split(";")
                for cat_name in cat_names:
                    if cat_name in freedesktop_main_categories:
                        cb_idx = self.combo_categ.findText(cat_name)
                        if cb_idx != -1:
                            self.combo_categ.setCurrentIndex(cb_idx)
                            break
            elif el[0:9] == "MimeType=":
                self.le_mime.setText(el[9:].strip("\n"))
            elif el[0:13] == "Keywords[{}]=".format(_locale):
                self.le_keys.setText(el[13:].strip("\n"))
                _keyword_found = 1
            elif _keyword_found == 0 and el[0:9] == "Keywords=":
                self.le_keys.setText(el[9:].strip("\n"))
            elif el[0:5] == "Icon=":
                self.le_icon.setText(el[5:].strip("\n"))
            elif el[0:12] == "Comment[{}]=".format(_locale):
                    _comment_found = 1
                    self.le_comment.setText(el[12:].strip("\n"))
            elif _comment_found == 0 and el[0:8] == "Comment=":
                self.le_comment.setText(el[8:].strip("\n"))
            elif el[0:9] == "Terminal=":
                term_chk = el[9:].strip("\n")
                self.chk_term.setChecked(False if term_chk=="false" else True)
            elif el[0:10] == "NoDisplay=":
                nodisp_chk = el[10:].strip("\n")
                self.chk_disp.setChecked(False if nodisp_chk=="false" else True)
            elif el[0:7] == "Hidden=":
                hidd_chk = el[7:].strip("\n")
                self.chk_hidd.setChecked(False if hidd_chk=="false" else True)
    
    def f_choose(self, wgt, f_type):
        fileName = QtWidgets.QFileDialog.getOpenFileName(self,
            "Choose", os.path.expanduser("~"), f_type)
        if fileName[0]:
            wgt.setText(fileName[0])
        

#############

# args: type - message - parent
class MyDialog(QtWidgets.QMessageBox):
    def __init__(self, *args):
        super(MyDialog, self).__init__(args[-1])
        if args[0] == "Info":
            self.setIcon(QtWidgets.QMessageBox.Icon.Information)
            self.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
        elif args[0] == "Error":
            self.setIcon(QtWidgets.QMessageBox.Icon.Critical)
            self.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
        elif args[0] == "Question":
            self.setIcon(QtWidgets.QMessageBox.Icon.Question)
            self.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok|QtWidgets.QMessageBox.StandardButton.Cancel)
        self.setWindowIcon(QtGui.QIcon("icons/dialog-red.svg"))
        self.setWindowTitle(args[0])
        self.resize(DIALOGWIDTH,50)
        self.setText(args[1])
        self.Value = None
        retval = self.exec()
        #
        if retval == QtWidgets.QMessageBox.StandardButton.Ok:
            self.Value = 1
        elif retval == QtWidgets.QMessageBox.StandardButton.Cancel:
            self.Value = 0
    
    def getValue(self):
        return self.Value
    
    def event(self, e):
        result = QtWidgets.QMessageBox.event(self, e)
        #
        self.setMinimumHeight(0)
        self.setMaximumHeight(16777215)
        self.setMinimumWidth(0)
        self.setMaximumWidth(16777215)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        # 
        return result


################
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    if len(sys.argv) > 1:
        if sys.argv[1]:
            if not os.path.exists(sys.argv[1]):
                MyDialog("Error", "The desktop file doesn't exist.", None)
                sys.exit()
            else:
                window = appWin(sys.argv[1])
    else:
        window = appWin()
    sys.exit(app.exec())
