#!/usr/bin/env python

import pygtk
pygtk.require("2.0")
import gtk

class Hello:
    def __init__(self):
        interface = gtk.Builder()
        interface.add_from_file('test.glade')
        interface.connect_signals(self)
    def on_main_window_destroy(self, widget):
        gtk.main_quit()

if __name__ == "__main__":
    Hello()
    gtk.main()
