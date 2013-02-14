#!/usr/bin/env python

from sys import path as syspath
import pygtk
pygtk.require("2.0")
import gtk

from ClusterShell import NodeSet

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
            'dependencies_service_treeview': ['Service'],
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
        [ self.interface.get_object("dependencies_service_liststore")
            .append([dependency])
            for dependency in self.config.dependencies.dependencies ]

    ##########
    # FIXME: this is a horrible mess
    def on_services_treeview_cursor_changed(self, treeview):
        service = treeview.get_model()[treeview.get_cursor()[0]][0]
        service_liststore = self.interface.get_object("service_liststore")
        service_liststore.clear()
        [ service_liststore.append([nodeset, script]) for (nodeset, script) in
            self.config.services.services[service].items() ]

    def on_services_delete(self, button):
        (services, selected) = self.interface.get_object(
            "services_treeview").get_selection().get_selected_rows()
        for index in selected:
            service = services[index][0]
            del self.config.services.services[service]
        self.interface.get_object("service_liststore").clear()
        services.clear()
        [ services.append([service])
            for service in self.config.services.services ]

    def on_service_delete(self, button):
        (service, selected) = self.interface.get_object(
                "service_treeview").get_selection().get_selected_rows()
        if selected:
            services = self.interface.get_object("services_treeview")
            service_name = services.get_model()[services.get_cursor()[0]][0]
            selected = [ index[0] for index in selected ]
            selected.sort(); selected.reverse()
            for index in selected:
                # we're being a bit hackish here
                del self.config.services.services[service_name][
                        self.config.services.services[
                        service_name].keys()[index]]
            service.clear()
            self.on_services_treeview_cursor_changed(services)

    def on_groups_treeview_cursor_changed(self, treeview):
        group = treeview.get_model()[treeview.get_cursor()[0]][0]
        group_liststore = self.interface.get_object("group_liststore")
        group_liststore.clear()
        [ group_liststore.append([service, nodeset]) for (service, nodeset) in
            self.config.groups.groups[group].items() ]

    def on_groups_delete(self, button):
        (groups, selected) = self.interface.get_object(
            "groups_treeview").get_selection().get_selected_rows()
        for index in selected:
            group = groups[index][0]
            del self.config.groups.groups[group]
        self.interface.get_object("group_liststore").clear()
        self.interface.get_object("groups_liststore").clear()
        [ groups.append([group])
            for group in self.config.groups.groups ]

    def on_group_delete(self, button):
        (group, selected) = self.interface.get_object(
            "group_treeview").get_selection().get_selected_rows()
        if selected:
            groups = self.interface.get_object("groups_treeview")
            group_name = groups.get_model()[groups.get_cursor()[0]][0]
            selected = [ index[0] for index in selected ]
            selected.sort(); selected.reverse()
            for index in selected:
                # we're being a bit hackish here
                del self.config.groups.groups[group_name][
                        self.config.groups.groups[
                        group_name].keys()[index]]
            self.interface.get_object("group_liststore").clear()
            group.clear()
            self.on_groups_treeview_cursor_changed(groups)

    def on_nodes_delete(self, button):
        (nodes, selected) = self.interface.get_object(
                "nodes_treeview").get_selection().get_selected_rows()
        selected = [ index[0] for index in selected ]
        selected.sort(); selected.reverse()
        for index in selected:
            del self.config.nodes.nodes[
                self.config.nodes.nodes.keys()[index]]
        nodes.clear()
        [ nodes.append([node]) for node in self.config.nodes.nodes ]

    def on_dependencies_services_treeview_cursor_changed(self, treeview):
        service = treeview.get_model()[treeview.get_cursor()[0]][0]
        nodeset_liststore = self.interface.get_object(
            "dependencies_nodeset_liststore")
        nodeset_liststore.clear()
        [ nodeset_liststore.append([nodeset]) for nodeset in
            self.config.dependencies.dependencies[service] ]
        self.interface.get_object(
            "dependencies_dependencies_treeview").get_model().clear()

    def on_dependencies_nodeset_treeview_cursor_changed(self, treeview):
        service_tv = self.interface.get_object("dependencies_service_treeview")
        service = service_tv.get_model()[service_tv.get_cursor()[0]][0]
        nodeset = treeview.get_cursor()[0][0]
        dependencies_liststore = self.interface.get_object(
            "dependencies_dependencies_liststore")
        dependencies_liststore.clear()
        # we're being a bit hackish here
        [ dependencies_liststore.append([dependency]) for dependency in
            self.config.dependencies.dependencies[service][
            self.config.dependencies.dependencies[service].keys()[nodeset]] ]

    def on_dependencies_service_delete(self, button):
        (services, selected) = self.interface.get_object(
            "dependencies_service_treeview").get_selection().get_selected_rows()
        for index in selected:
            service = services[index][0]
            del self.config.dependencies.dependencies[service]
        for liststore in ['nodeset', 'dependencies']:
            self.interface.get_object("dependencies_%s_liststore"
                %liststore).clear()
        services.clear()
        [ services.append([service])
            for service in self.config.dependencies.dependencies ]

    def on_dependencies_nodeset_delete(self, button):
        (nodesets, selected) = self.interface.get_object(
            "dependencies_nodeset_treeview").get_selection().get_selected_rows()
        if selected:
            services = self.interface.get_object(
                "dependencies_service_treeview")
            service_name = services.get_model()[services.get_cursor()[0]][0]
            selected = [ index[0] for index in selected ]
            selected.sort(); selected.reverse()
            # we're being a bit hackish here
            for index in selected:
                del self.config.dependencies.dependencies[service_name][
                    self.config.dependencies.dependencies[service_name]
                    .keys()[index]]
            self.interface.get_object(
                "dependencies_dependencies_liststore").clear()
            nodesets.clear()
            [ nodesets.append([nodeset]) for nodeset in
                self.config.dependencies.dependencies[service_name] ]

    def on_dependencies_dependencies_delete(self, button):
        (dependencies, selected) = self.interface.get_object(
            "dependencies_dependencies_treeview"
            ).get_selection().get_selected_rows()
        if selected:
            nodesets = self.interface.get_object(
                "dependencies_nodeset_treeview")
            nodeset_number = nodesets.get_cursor()[0][0]
            services = self.interface.get_object("dependencies_service_treeview")
            service_name = services.get_model()[services.get_cursor()[0]][0]
            for index in selected:
                dependency = dependencies[index][0]
                self.config.dependencies.dependencies[service_name][
                    self.config.dependencies.dependencies[service_name]
                    .keys()[nodeset_number]].remove(dependency)
            dependencies.clear()
            self.on_dependencies_nodeset_treeview_cursor_changed(nodesets)
    ##########

if __name__ == "__main__":
    Hello()
    gtk.main()
