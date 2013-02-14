#!/usr/bin/env python

from sys import path as syspath

import pygtk
pygtk.require("2.0")
import gtk

from ClusterShell import NodeSet

syspath.append('..')
import ClushSvcCLI
import Config
import Node

class Hello:
    def __init__(self):
        self.config = Config.Config()
        self.interface = gtk.Builder()

        self.interface.add_from_file('test.glade')
        self.interface.connect_signals(self)

        self.all_treeview_init()
        self.all_liststores_init()

        self.command_target_switch = False
        self.interface.get_object('command_radio_nodeset_radiobutton').set_active(True)

        self.command = ClushSvcCLI.ClushSvcCLI()
        self.command.config = Config.Config()


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

    def on_command_exec(self, widget):
        self.interface.get_object('command_liststore').clear()

        target = self.interface.get_object('command_target_entry').get_text()
        service = self.interface.get_object('command_service_entry').get_text()
        action = self.interface.get_object('command_action_entry').get_text()

        # Same bloc as in ClushSvcCLI.main
        # ==========
        # are we using groups?
        if (not self.command_target_switch):
            arg_group = target
            arg_action = action
            arg_task = self.command.config.groups.get(arg_group.lower())
            for service in arg_task:
                arg_task[service] = set(self.command.config.nodes.get_from_nodeset(
                    arg_task[service]))
        else:
            arg_nodes = self.command.config.nodes.get_from_nodeset(NodeSet.NodeSet(
                target.lower()))
            arg_service = service
            arg_action = action
            arg_task = {arg_service: set(arg_nodes)}

        # Do we check dependencies too?
        if arg_action in ('start', 'status'): # if arg_action not in ('stop', 'restart')
            dependencies = self.command.config.dependencies.get_recursive(arg_task)
            dependencies.append(arg_task)
            self.command.dependencies_run(dependencies, arg_action)
        else:
            dependencies = [arg_task]
            self.command.dependencies_run(dependencies, arg_action)
        # ==========

        for (nodes, script, status) in self.command.result:
            self.interface.get_object('command_liststore').append([nodes, script, status])

    def on_command_target_switch(self, widget):
        if self.command_target_switch:
            self.interface.get_object('command_service_frame').hide_all()
        else:
            self.interface.get_object('command_service_frame').show_all()
        self.command_target_switch = not self.command_target_switch

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
