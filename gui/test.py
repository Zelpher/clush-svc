#!/usr/bin/env python

import pygtk
pygtk.require("2.0")
import gtk

class Hello:
    def __init__(self):
        self.interface = gtk.Builder()
        self.interface.add_from_file('test.glade')
        self.interface.connect_signals(self)
        self.all_treeview_init()

    def on_main_window_destroy(self, widget):
        gtk.main_quit()

    def all_treeview_init(self):
        cell = gtk.CellRendererText()
        treeviews = {
            'status_treeview': ['NodeSet', 'Service', 'Status'],
            'command_treeview': ['NodeSet', 'Service', 'Status'],
            'services_treeview': ['Service'],
            'service_treeview': ['NodeSet', 'Alias'],
            'nodes_treeview': ['NodeSet'],
            'groups_treeview': ['Group'],
            'group_treeview': ['Service', 'Nodes'],
            'dependencies_service_treeview': ['Service'],
            'dependencies_nodeset_treeview': ['NodeSet'],
            'dependencies_dependencies_treeview': ['Dependencies'],
        }

        for treeview in treeviews:
            treeview_object = self.interface.get_object(treeview)
            if not treeview_object:
                print "Error: treeview %s not found"%treeview
                continue
            for column in xrange(len(treeviews[treeview])):
                col = gtk.TreeViewColumn(treeviews[treeview][column])
                treeview_object.append_column(col)
                col.pack_start(cell)
                col.add_attribute(cell, "text", column)
                col.set_resizable(True)

if __name__ == "__main__":
    Hello()
    gtk.main()
