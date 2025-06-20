import dbus
import dbus.service
import sys, os, shutil
from subprocess import Popen

class launchApps(dbus.service.Object):
    def __init__(self, _loop):
        self.bus = dbus.SessionBus()
        name = dbus.service.BusName('com.appExec.Execapp', bus=self.bus)
        super().__init__(name, '/Application')
        self.mainloop = _loop
        
    # @dbus.service.method('com.gkbrk.Time', out_signature='s')
    # def CurrentTime(self):
        # """Use strftime to return a formatted timestamp
        # that looks like 23-02-2018 06:57:04."""
        # 
        # formatter = '%d-%m-%Y %H:%M:%S'
        # print("TIME FROM SERVER: ", time.strftime(formatter))
        # os.system("sakura &")
        # return time.strftime(formatter)
    
    @dbus.service.method('com.appExec.Execapp', in_signature="s", out_signature="s")
    def execProg(self, _app_desktop_file):
        _cmd = _app_desktop_file.split("/")[-1].removesuffix(".desktop")
        try:
            if shutil.which("gtk-launch"):
                _cmd2 = "gtk-launch {}".format(_cmd)
                ret = GLib.spawn_command_line_async(_cmd2)
                return "success"
            else:
                return "gtk-launch not found"
        except Exception as E:
            return str(E)
        
    @dbus.service.method('com.appExec.Execapp', in_signature="s", out_signature="s")
    def execProg2(self, _prog):
        try:
            Popen([_prog, "&"], shell=True)
        except Exception as E:
            return str(E)
        return "success"
    
    @dbus.service.method('com.gkbrk.Time', in_signature=None, out_signature=None)
    def setStatus(self):
        self.mainloop.quit()
        
    
# # example
# @dbus.service.method(dbus_interface="com.example.HelloWorldInterface", in_signature="s", out_signature="s", sender_keyword="sender", connection_keyword="conn")
# def SayHello(self, name, sender=None, conn=None):
    # return "Hello " + name


if __name__ == '__main__':
    import dbus.mainloop.glib
    from gi.repository import GLib
    
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    
    loop = GLib.MainLoop()
    object = launchApps(loop)
    loop.run()

