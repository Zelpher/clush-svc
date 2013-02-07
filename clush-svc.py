#!/usr/bin/env python

from ConfigParser import ConfigParser
from optparse import OptionParser
import os

import ClusterShell.Task as Task
import ClusterShell.NodeSet as NodeSet

import templates

Config = {}

class Node:
    name = None
    manager = 'sysvinit'

    def __init__(self, name=None):
        self.name = name

def config_read_nodes():
    """
    Load nodes from config files into Config['nodes']
    """
    Config['nodes'] = {}
    conf = ConfigParser()
    conf.read(['/etc/clush-svc/nodes.cfg',
        os.path.expanduser('~/.config/clush-svc/nodes.cfg')])
    for (nodes, manager) in conf.items('Managers'):
        for node in NodeSet.NodeSet(nodes):
            if node not in Config['nodes']:
                Config['nodes'][node] = Node()
            Config['nodes'][node].name = node
            Config['nodes'][node].manager = manager

def parse_nodes(nodeset):
    """
    Take a string NodeSet and return a list of Nodes
    """
    nodes = []
    for node in NodeSet.NodeSet(nodeset):
        nodes.append(Config['nodes'][node] if node in Config['nodes'] else Node(node))
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
    config_read_nodes()

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
