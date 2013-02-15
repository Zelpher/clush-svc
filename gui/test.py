#!/usr/bin/env python

from sys import path as syspath
import pygtk
pygtk.require("2.0")
import gtk

from ClusterShell import NodeSet

syspath.append('..')
import TabManagers
import ClushSvcCLI
import Config
import Node

class Hello:
    def __init__(self):
        self.config = Config.Config()
        self.interface = gtk.Builder()

        self.interface.add_from_file('test.glade')
        self.interface.connect_signals(self)

        self.groups = TabManagers.DictDictTabManager(self.interface,
                self.config.groups.groups, "groups_treeview", "group_treeview",
                "groups_entry", "group_service_entry", "group_nodeset_entry",
                (str, str, NodeSet.NodeSet))
        self.services = TabManagers.DictDictTabManager(self.interface,
                self.config.services.services,
                "services_treeview", "service_treeview","services_entry",
                "service_nodeset_entry", "service_alias_entry",
                (str, NodeSet.NodeSet, str))
        self.dependencies = TabManagers.DictDictListTabManager(self.interface,
                self.config.dependencies.dependencies,
                "dependencies_services_treeview",
                "dependencies_nodeset_treeview",
                "dependencies_dependencies_treeview",
                "dependencies_services_entry", "dependencies_nodeset_entry",
                "dependencies_dependencies_entry",
                (str, NodeSet.NodeSet, str))
        self.nodes = TabManagers.NodesTabManager(self.interface,
                self.config.nodes.nodes, "nodes_treeview", "nodes_edit_entry",
                (str, Node.Node))

        self.all_treeview_init()
        self.all_liststores_init()

        self.command_target_switch = False
        self.interface.get_object('command_radio_nodeset_radiobutton').set_active(True)

        self.command = ClushSvcCLI.ClushSvcCLI()
        self.command.config = self.config

        # First status check on launch
        self.main_tabs_widget = self.interface.get_object('main_tabs')
        self.on_main_tabs_switch_page(self.main_tabs_widget, self.main_tabs_widget.get_nth_page(0), 0)

    def all_treeview_init(self):
        """
        Add columns to every treeview
        """
        cell = gtk.CellRendererText()
        treeviews = {
            'status_treeview': ['Groups', 'Status'],
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
            treeview_object.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
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
        [ self.interface.get_object("dependencies_services_liststore")
            .append([dependency])
            for dependency in self.config.dependencies.dependencies ]

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

    def on_main_tabs_switch_page(self, widget, page, page_num):
        if (page_num == 0):
            self.interface.get_object('status_liststore').clear()
            for arg_group in self.command.config.groups.groups:
                state = "Running"
                arg_task = self.command.config.groups.get(arg_group.lower())
                for service in arg_task:
                    arg_task[service] = set(self.command.config.nodes.get_from_nodeset(
                        arg_task[service]))
                dependencies = self.command.config.dependencies.get_recursive(arg_task)
                dependencies.append(arg_task)
                self.command.dependencies_run(dependencies, 'status')
                for (nodes, script, status) in self.command.result:
                    if (status == "failed"):
                        state = "Stopped"
                self.interface.get_object('status_liststore').append([arg_group, state])

    def on_main_window_destroy(self, widget):
        gtk.main_quit()

    def on_save_button(self, button):
        self.config.save()

    def on_services_treeview_cursor_changed(self, treeview):
        self.services.update_props()

    def on_services_delete(self, button):
        self.services.del_selected()
        self.services.update()

    def on_services_add(self, button):
        self.services.add()
        self.services.update()

    def on_service_delete(self, button):
        self.services.del_selected_props()
        self.services.update_props()

    def on_service_add(self, button):
        self.services.add_props()
        self.services.update_props()

    def on_groups_treeview_cursor_changed(self, treeview):
        self.groups.update_props()

    def on_groups_delete(self, button):
        self.groups.del_selected()
        self.groups.update()

    def on_groups_add(self, button):
        self.groups.add()
        self.groups.update()

    def on_group_delete(self, button):
        self.groups.del_selected_props()
        self.groups.update_props()

    def on_group_add(self, button):
        self.groups.add_props()
        self.groups.update_props()

    def on_nodes_treeview_cursor_changed(self, treeview):
        self.nodes.update_props()

    def on_nodes_delete(self, button):
        self.nodes.del_selected()
        self.nodes.update()

    def on_nodes_add(self, button):
        self.nodes.add()
        self.nodes.update()

    def on_dependencies_services_treeview_cursor_changed(self, treeview):
        self.dependencies.update_props()

    def on_dependencies_services_delete(self, button):
        self.dependencies.del_selected()
        self.dependencies.update()

    def on_dependencies_services_add(self, button):
        self.dependencies.add()
        self.dependencies.update()

    def on_dependencies_nodeset_treeview_cursor_changed(self, treeview):
        self.dependencies.update_secProps()

    def on_dependencies_nodeset_add(self, button):
        self.dependencies.add_props()
        self.dependencies.update_props()

    def on_dependencies_nodeset_delete(self, button):
        self.dependencies.del_selected_props()
        self.dependencies.update_props()

    def on_dependencies_dependencies_delete(self, button):
        self.dependencies.del_selected_secProps()
        self.dependencies.update_secProps()

    def on_dependencies_dependencies_add(self, button):
        self.dependencies.add_secProps()
        self.dependencies.update_secProps()

if __name__ == "__main__":
    Hello()
    gtk.main()
