#!/usr/bin/env python

from sys import path as syspath

import pygtk
pygtk.require("2.0")
import gtk

syspath.append('..')
import Config

class Hello:
    def __init__(self):
        self.config = Config.Config()
        self.interface = gtk.Builder()

        self.interface.add_from_file('test.glade')
        self.interface.connect_signals(self)

        self.all_treeview_init()
        self.all_liststores_init()

    def on_main_window_destroy(self, widget):
        gtk.main_quit()

    def all_treeview_init(self):
        """
        Add columns to every treeview
        """
        cell = gtk.CellRendererText()
        treeviews = {
            'status_treeview': ['NodeSet', 'Service', 'Status'],
            'command_treeview': ['NodeSet', 'Service', 'Status'],
            'services_treeview': ['Service'],
            'service_treeview': ['NodeSet', 'Alias'],
            'nodes_treeview': ['NodeSet'],
            'groups_treeview': ['Group'],
            'group_treeview': ['Service', 'Nodes'],
            'dependencies_services_treeview': ['Service'],
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

    def all_liststores_init(self):
        """
        Put data from config into all base liststores
        """
        [ self.interface.get_object("services_liststore").append([service])
                for service in self.config.services.services ]
        [ self.interface.get_object("groups_liststore").append([group])
                for group in self.config.groups.groups ]
        [ self.interface.get_object("nodes_liststore").append([node])
                for node in self.config.nodes.nodes ]
        [ self.interface.get_object("dependencies_dependencies_liststore")
                .append([dependency])
                for dependency in self.config.dependencies.dependencies ]

if __name__ == "__main__":
    Hello()
    gtk.main()
