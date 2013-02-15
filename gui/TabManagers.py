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
        DictTabManager.__init__(self, interface, config, dict_treeview)
        self.props_tv = self.interface.get_object(list_treeview)
        self.props_lst = self.props_tv.get_model()
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
    def update_props(self):
        element = self.get_last_selected()
        self.props_lst.clear()
        [ self.props_lst.append(data) for data in
                self.config[element].items() ]

class DictListListTabManager(DictListTabManager):
    def __init__(self, interface, config, dict_treeview, list1_treeview,
            list2_treeview):
        DictListTabManager.__init__(self, interface, config,
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
