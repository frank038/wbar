#!/usr/bin/env python3

import os, shutil
from xdg import DesktopEntry
# from xdg import IconTheme
# to get the language
# import locale
# 
# user_locale = "en"

#######################

class getItem():
    
    def __init__(self, _desktop):
        self._desktop = _desktop
        # arguments in the exec fiels
        # self.execArgs = [" %f", " %F", " %u", " %U", " %d", " %D", " %n", " %N", " %k", " %v"]
        self.execArgs = ["%f", "%F", "%u", "%U", "%d", "%D", "%n", "%N", "%k", "%v"]
        #
        # list of all desktop files found
        self.list = []
        self.fpop(self._desktop)
        self.retList()
        
    # return the lists
    def retList(self):
        # self.list_one = sorted(self.lists, key=lambda list_one: list_one[0].lower(), reverse=False)
        # return list_one
        return self.list
    
    def fpop(self, file_path):
        if not file_path.lower().endswith(".desktop"):
            return
        #
        try:
            entry = DesktopEntry.DesktopEntry(file_path)
            ftype = entry.getType()
            if ftype != "Application":
                return
            #
            ftry = entry.getTryExec()
            if ftry:
                if not shutil.which(ftry):
                    return
            #
            hidden = entry.getHidden()
            nodisplay = entry.getNoDisplay()
            # do not show those marked as hidden or not to display
            if hidden or nodisplay:
                return
            # item.name
            fname = entry.getName()
            # item.path
            # fpath
            # # category
            # ccat = entry.getCategories()
            # fcategory = self.get_category(ccat)
            # ## item.name.lower()
            # fname_lower = fname.lower()
            # pexec (executable)
            fexec = entry.getExec()
            # if fexec[0] == '"':
                # fexec = fexec.lstrip('"').rstrip('"')
            if fexec[0:5] == "$HOME":
                fexec = "~"+fexec[5:]
            # check for arguments and remove them
            # # # if fexec[-3:] in self.execArgs:
                # # # fexec = fexec[:-3]
            # # for aargs in self.execArgs:
                # # if aargs in fexec:
                    # # fexec = fexec.strip(aargs)
            # fexec = fexec.split(" ")[0]
            fexec_temp = fexec.split(" ")
            for targ in self.execArgs:
                if targ in fexec_temp:
                    fexec_temp.remove(targ)
            fexec = " ".join(fexec_temp)
            # icon
            ficon = entry.getIcon()
            # comment
            fcomment = entry.getComment()
            # tryexec
            fpath = entry.getPath()
            # terminal
            fterminal = str(entry.getTerminal())
            ###
            # if not self.menu_prog:
                # file_fpath = ""
            # else:
                # file_fpath = file_path
            # label - executable - icon - comment - path - terminal - file full path
            # self.list.append([fname, fexec, ficon, fcomment, fpath, fterminal, file_path])
            # ICON - NAME - EXEC - TOOLTIP - PATH - TERMINAL - FILENAME
            self.list = [ficon, fname, fexec, fcomment, fpath, fterminal, file_path]
        except:
            pass
    