class Node:
    """
    Our internal representation of a node with its settings.
    """
    def __init__(self, name=None, manager='service'):
        self.name = name
        self.manager = manager

    @staticmethod
    def group_by_manager(nodes):
        """
        Take a list of Nodes and group them by manager. Return a dict with
        service manager as key and Nodes as values.
        """
        groupedNodes = {}
        for node in nodes:
            if node.manager not in groupedNodes:
                groupedNodes[node.manager] = []
            groupedNodes[node.manager].append(node)
        return groupedNodes

    @staticmethod
    def group_by_script(config, service, nodes):
        """
        Make groups of Nodes by script name for requested service.
        Returns { 'script_name': [node1, node2, ...], ... }
        """
        nodesByScript = {}
        for node in nodes:
            script = config.services.get_alias(service, node.name)
            if script not in nodesByScript:
                nodesByScript[script] = []
            nodesByScript[script].append(node)
        return nodesByScript
