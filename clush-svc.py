#!/usr/bin/env python

from ConfigParser import ConfigParser
from optparse import OptionParser
import os

import ClusterShell.Task as Task
import ClusterShell.NodeSet as NodeSet

import templates

Config = {
    'nodes': {},
    'services': {},
    'dependencies': {},
    'groups': {}
}

class Node:
    name = None
    manager = 'service'

    def __init__(self, name=None):
        self.name = name


def config_read():
    """
    Load nodes from config files into Config
    """
    # { nodeName: <Node object>, ... }
    conf = ConfigParser()
    conf.read(['/etc/clush-svc/nodes.cfg',
        os.path.expanduser('~/.config/clush-svc/nodes.cfg')])
    for (nodes, manager) in conf.items('Managers'):
        for node in NodeSet.NodeSet(nodes):
            if node not in Config['nodes']:
                Config['nodes'][node] = Node()
            Config['nodes'][node].name = node
            Config['nodes'][node].manager = manager

    # { serviceName: { <NodeSet object>: script }, ... }
    conf = ConfigParser()
    conf.read(['/etc/clush-svc/services.cfg',
        os.path.expanduser('~/.config/clush-svc/services.cfg')])
    for service in conf.sections():
        Config['services'][service] = {}
        for (nodeset, script) in conf.items(service):
            nodeset = NodeSet.NodeSet(nodeset)
            Config['services'][service][nodeset] = script

    # { serviceName: { <NodeSet object>: [dependency1, ...], ... }, ... }
    conf = ConfigParser()
    conf.read(['/etc/clush-svc/dependencies.cfg',
        os.path.expanduser('~/.config/clush-svc/dependencies.cfg')])
    for service in conf.sections():
        Config['dependencies'][service] = {}
        for (nodeset, dependencies) in conf.items(service):
            dependencies = map(str.strip, dependencies.split(','))
            nodeset = NodeSet.NodeSet(nodeset)
            Config['dependencies'][service][nodeset] = dependencies

    # { groupName: { serviceName: <NodeSet object>, ...  }, ... }
    conf = ConfigParser()
    conf.read(['/etc/clush-svc/groups.cfg',
        os.path.expanduser('~/.config/clush-svc/groups.cfg')])
    for group in conf.sections():
        Config['groups'][group] = {}
        for (service, nodeset) in conf.items(group):
            nodeset = NodeSet.NodeSet(nodeset)
            Config['groups'][group][service] = nodeset

def parse_nodes(nodeset):
    """
    Take a string NodeSet and return a list of Nodes
    """
    nodes = []
    for node in NodeSet.NodeSet(nodeset):
        nodes.append(Config['nodes'][node] if node in Config['nodes']
                else Node(node))
    return nodes

def group_nodes(nodes):
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

def main():
    # Parse command line options
    parser = OptionParser()
    parser.add_option("-w", dest="nodes")
    (options, args) = parser.parse_args()

    # Read config
    config_read()

    # Prepare and launch tasks
    groupedNodes = group_nodes(parse_nodes(options.nodes))
    tasks = []
    for manager in groupedNodes:
        task = Task.task_self()
        nodesList = ','.join([node.name for node in groupedNodes[manager]])
        task.run(templates.get_command(manager=manager, service=args[0],
            action=args[1]), nodes=nodesList)
        tasks.append(task)

    for task in tasks:
        for (rc, keys) in task.iter_retcodes():
            print NodeSet.NodeSet.fromlist(keys), str(rc)

if __name__ == '__main__':
    main()
