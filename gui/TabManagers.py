import gtk

import Node
import managers

class DictTabManager:
    def __init__(self, interface, config, dict_treeview, dict_entry,
            entry_types):
        self.config = config
        self.interface = interface
        self.tv = self.interface.get_object(dict_treeview)
        self.lst = self.tv.get_model()
        self.entry = self.interface.get_object(dict_entry)
        self.entryTypes = entry_types
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
    def add(self):
        entry = self.entry.get_text().lower()
        if entry:
            self.config[self.entryTypes[0](entry)] = {}
            self.entry.set_text('')
            self.update()
    def update(self):
        self.lst.clear()
        [ self.lst.append([element]) for element in self.config ]

class NodesTabManager(DictTabManager):
    def __init__(self, interface, config, dict_treeview, dict_entry,
            entry_types):
        DictTabManager.__init__(self, interface, config, dict_treeview,
                dict_entry, entry_types)
        self.manager_entry = gtk.combo_box_new_text()
        self.manager_entry.connect('changed', self.save_manager)
        props_box = self.interface.get_object("node_prop_value_vbox")
        props_box.pack_start(self.manager_entry, False); props_box.show_all()
        for manager in managers.managers:
            self.manager_entry.append_text(manager)
    def add(self):
        entry = self.entry.get_text().lower()
        if entry:
            self.config[entry] = Node.Node()
            self.config[entry].name = entry
            self.entry.set_text('')
            self.update()
    def update_props(self):
        node = self.get_last_selected()
        if node:
            self.manager_entry.set_active(
                    managers.managers.keys().index(self.config[node].manager))
    def save_manager(self, entry):
        nodes = self.get_selected()
        manager = self.manager_entry.get_active_text()
        if manager != -1:
            for node in nodes:
                self.config[node].manager = manager

class DictDictTabManager(DictTabManager):
    def __init__(self, interface, config, dict1_treeview, dict2_treeview,
            dict1_entry, dict2_entry, final_entry, entry_types):
        DictTabManager.__init__(self, interface, config, dict1_treeview,
                dict1_entry, entry_types)
        self.props_tv = self.interface.get_object(dict2_treeview)
        self.props_lst = self.props_tv.get_model()
        self.prop1_entry = self.interface.get_object(dict2_entry)
        self.prop2_entry = self.interface.get_object(final_entry)
    def update(self):
        self.props_lst.clear()
        DictTabManager.update(self)
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
    def add_props(self):
        element = self.get_last_selected()
        prop1 = self.prop1_entry.get_text().lower()
        prop2 = self.prop2_entry.get_text().lower()
        if prop1 and prop2 and element:
            prop1 = self.entryTypes[1](prop1)
            prop2 = self.entryTypes[2](prop2)
            self.config[element][prop1] = prop2
            self.prop1_entry.set_text(''); self.prop2_entry.set_text('')
            self.update_props()
    def update_props(self):
        element = self.get_last_selected()
        self.props_lst.clear()
        [ self.props_lst.append(data) for data in
                self.config[self.entryTypes[0](element)].items() ]

class DictDictListTabManager(DictDictTabManager):
    def __init__(self, interface, config, dict1_treeview, dict2_treeview,
            list_treeview, dict1_entry, dict2_entry, list_entry, entry_types):
        DictDictTabManager.__init__(self, interface, config,
                dict1_treeview, dict2_treeview, dict1_entry, dict2_entry,
                list_entry, entry_types)
        self.secProps_tv = self.interface.get_object(list_treeview)
        self.secProps_lst = self.secProps_tv.get_model()
    def add_props(self):
        element = self.get_last_selected()
        prop1 = self.prop1_entry.get_text().lower()
        if prop1 and element:
            prop1 = self.entryTypes[1](prop1)
            self.config[element][prop1] = []
            self.prop1_entry.set_text('');
            self.update_props()
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
    def add_secProps(self):
        element = self.get_last_selected()
        prop1 = self.get_last_selected_props()
        prop2 = self.prop2_entry.get_text().lower()
        if prop1 and prop2 and element:
            prop2 = self.entryTypes[2](prop2)
            self.config[element][prop1].append(prop2)
            self.prop2_entry.set_text('');
            self.update_secProps()
    def update_secProps(self):
        element = self.get_last_selected()
        props = self.get_last_selected_props()
        self.secProps_lst.clear()
        [ self.secProps_lst.append([data]) for data in
                [ datas for datas in self.config[element][props] ] ]
