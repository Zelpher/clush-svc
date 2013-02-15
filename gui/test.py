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
    class DictTabManager:
        def __init__(self, interface, config, dict_treeview):
            self.config = config
            self.interface = interface
            self.tv = self.interface.get_object(dict_treeview)
            self.lst = self.tv.get_model()
        def get_last_selected(self):
            cur = self.tv.get_cursor()[0]
            if cur:
                return self.lst[cur[0]][0]
        def get_selected(self):
            selected = self.tv.get_selection().get_selected_rows()[1]
            return [ self.lst[element][0] for element in selected ]
        def del_selected(self):
            for element in self.get_selected():
                del self.config[element]
        def update(self):
            self.lst.clear()
            [ self.lst.append([element]) for element in self.config ]

    class DictListTabManager(DictTabManager):
        def __init__(self, interface, config, dict_treeview, list_treeview):
            Hello.DictTabManager.__init__(self, interface, config, dict_treeview)
            self.props_tv = self.interface.get_object(list_treeview)
            self.props_lst = self.props_tv.get_model()
        def update(self):
            self.props_lst.clear()
            Hello.DictTabManager.update(self)
        def get_selected_props(self):
            selected = [ index[0] for index in
                    self.props_tv.get_selection().get_selected_rows()[1] ]
            selected.sort(); selected.reverse()
            element = self.get_last_selected()
            props = self.config[element].keys()
            return [ props[index] for index in selected ]
        def del_selected_props(self):
            element = self.get_last_selected()
            for props in self.get_selected_props():
                del self.config[element][props]
        def update_props(self):
            element = self.get_last_selected()
            self.props_lst.clear()
            [ self.props_lst.append(data) for data in
                    self.config[element].items() ]

    class DictListListTabManager(DictListTabManager):
        def __init__(self, interface, config, dict_treeview, list1_treeview,
                list2_treeview):
            Hello.DictListTabManager.__init__(self, interface, config,
                    dict_treeview, list1_treeview)
            self.secProps_tv = self.interface.get_object(list2_treeview)
            self.secProps_lst = self.secProps_tv.get_model()
        def update_props(self):
            self.secProps_lst.clear()
            element = self.get_last_selected()
            self.props_lst.clear()
            [ self.props_lst.append(data[:-1]) for data in
                    self.config[element].items() ]
        def get_last_selected_props(self):
            element = self.get_last_selected()
            cur = self.props_tv.get_cursor()[0]
            if cur:
                return self.config[element].keys()[cur[0]]
        def get_selected_secProps(self):
            selected = [ index[0] for index in
                    self.secProps_tv.get_selection().get_selected_rows()[1] ]
            selected.sort(); selected.reverse()
            element = self.get_last_selected()
            props = self.get_last_selected_props()
            secProps = self.config[element][props]
            return [ secProps[index] for index in selected ]
        def del_selected_secProps(self):
            element = self.get_last_selected()
            props = self.get_last_selected_props()
            [ self.config[element][props].remove(secProps) for secProps in
                    self.get_selected_secProps() ]
        def update_secProps(self):
            element = self.get_last_selected()
            props = self.get_last_selected_props()
            self.secProps_lst.clear()
            [ self.secProps_lst.append([data]) for data in
                    [ datas for datas in self.config[element][props] ] ]
            
    def __init__(self):
        self.config = Config.Config()
        self.interface = gtk.Builder()

        self.interface.add_from_file('test.glade')
        self.interface.connect_signals(self)

        self.nodes = Hello.DictTabManager(self.interface,
                self.config.nodes.nodes, "nodes_treeview")
        self.services = Hello.DictListTabManager(self.interface,
            self.config.services.services,
            "services_treeview", "service_treeview")
        self.groups = Hello.DictListTabManager(self.interface,
            self.config.groups.groups, "groups_treeview", "group_treeview")
        self.dependencies = Hello.DictListListTabManager(self.interface,
                self.config.dependencies.dependencies,
                "dependencies_services_treeview",
                "dependencies_nodeset_treeview",
                "dependencies_dependencies_treeview")

        self.all_treeview_init()
        self.all_liststores_init()

        self.command_target_switch = False
        self.interface.get_object('command_radio_nodeset_radiobutton').set_active(True)

        self.command = ClushSvcCLI.ClushSvcCLI()
        self.command.config = self.config

        # First status check on launch
        self.main_tabs_widget = self.interface.get_object('main_tabs')
        self.on_main_tabs_switch_page(self.main_tabs_widget, self.main_tabs_widget.get_nth_page(0), 0)

    def on_main_window_destroy(self, widget):
        gtk.main_quit()

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

    def on_services_treeview_cursor_changed(self, treeview):
        self.services.update_props()

    def on_services_delete(self, button):
        self.services.del_selected()
        self.services.update()

    def on_service_delete(self, button):
        self.services.del_selected_props()
        self.services.update_props()

    def on_groups_treeview_cursor_changed(self, treeview):
        self.groups.update_props()

    def on_groups_delete(self, button):
        self.groups.del_selected()
        self.groups.update()

    def on_group_delete(self, button):
        self.groups.del_selected_props()
        self.groups.update_props()

    def on_nodes_delete(self, button):
        self.nodes.del_selected()
        self.nodes.update()

    def on_dependencies_services_treeview_cursor_changed(self, treeview):
        self.dependencies.update_props()

    def on_dependencies_services_delete(self, button):
        self.dependencies.del_selected()
        self.dependencies.update()

    def on_dependencies_nodeset_treeview_cursor_changed(self, treeview):
        self.dependencies.update_secProps()

    def on_dependencies_nodeset_delete(self, button):
        self.dependencies.del_selected_props()
        self.dependencies.update_props()

    def on_dependencies_dependencies_delete(self, button):
        self.dependencies.del_selected_secProps()
        self.dependencies.update_secProps()

if __name__ == "__main__":
    Hello()
    gtk.main()
