#!/usr/bin/env python

from ConfigParser import ConfigParser
from optparse import OptionParser
import os

import ClusterShell.Task as Task
import ClusterShell.NodeSet as NodeSet

import managers

Config = {
    'nodes': {},
    'services': {},
    'dependencies': {},
    'groups': {}
}

class Node:
    def __init__(self, name=None, manager='service'):
        self.name = name
        self.manager = manager

class InfiniteRecursionError(Exception):
    def __init__(self, service, node):
        self.service = service
        self.node = node
    def __str__(self):
        return "Service %s on node %s" %(self.service, self.node.name)


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

def group_nodes_by_manager(nodes):
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

def get_dependencies(arg_dependencies):
    """
    Take and return a dict { 'service': set(<Node object>, ...), ... }
    """
    dependencies = {}
    for arg_service in arg_dependencies:
        if arg_service in Config['dependencies']:
            for target_node in arg_dependencies[arg_service]:
                for dep_nodes in Config['dependencies'][arg_service]:
                    if target_node.name in dep_nodes:
                        dep_services = Config['dependencies'][arg_service][dep_nodes]
                        for dep_service in dep_services:
                            if dep_service not in dependencies:
                                dependencies[dep_service] = set()
                            dependencies[dep_service].add(target_node)
    return dependencies

def get_all_dependencies(arg_service, arg_nodes):
    """
    Recursive get_dependencies. Return a list of dicts like get_dependencies
    """
    all_dependencies = []
    dependencies = get_dependencies({arg_service: arg_nodes})
    while dependencies:
        for service in dependencies:
            for node in dependencies[service]:
                for dependency in all_dependencies:
                    if service in dependency:
                        if node in dependency[service]:
                            raise InfiniteRecursionError(service, node)
        all_dependencies.append(dependencies)
        dependencies = get_dependencies(dependencies)
    return all_dependencies

def group_nodes_by_script(service, nodes):
    """
    Make groups of nodes by script name for requested service
    """
    nodesByScript = {} # { 'script_name': [node1, node2, ...], ... }
    for target_node in nodes:
        nodeInConfig = False
        if service in Config['services']:
            for script_nodeset in Config['services'][service]:
                if target_node.name in script_nodeset:
                    scriptName = Config['services'][service][script_nodeset]
                    if scriptName not in nodesByScript.keys():
                        nodesByScript[scriptName] = []
                    nodesByScript[scriptName].append(target_node)
                    nodeInConfig = True
        if not nodeInConfig:
            if service not in nodesByScript.keys():
                nodesByScript[service] = []
            nodesByScript[service].append(target_node)
    return nodesByScript

def tasks_run(arg_tasks, action):
    """
    Prepare and launch tasks
    """
    tasks = []
    for script in arg_tasks:
        groupedNodes = group_nodes_by_manager(arg_tasks[script])
        for manager in groupedNodes:
            task = Task.task_self()
            nodesList = ','.join([node.name for node in groupedNodes[manager]])
            command = managers.get_command(manager=manager, service=script,
                action=action)
            print "Task run: " + command + ", nodes: " + nodesList
            #task.run(command, nodes=nodesList)
            tasks.append(task)

def main():
    # Parse command line options
    parser = OptionParser()
    parser.add_option("-w", dest="nodes")
    (options, args) = parser.parse_args()

    # Read config
    config_read()
    # parse_nodes needs config
    arg_nodes = parse_nodes(options.nodes)
    arg_service = args[0]

    all_dependencies = get_all_dependencies(arg_service, arg_nodes)
    all_dependencies.reverse()
    for dependencies_group in all_dependencies:
        tasks = {}
        for dependency in dependencies_group:
            tasks.update(group_nodes_by_script(dependency, 
                                            dependencies_group[dependency]))
        tasks = tasks_run(tasks, args[1])
        print "--------------------------"
        # Verifier les codes de retour
    # Lancer les taches principales

#    for task in tasks:
#        for (rc, keys) in task.iter_retcodes():
#            print NodeSet.NodeSet.fromlist(keys), str(rc)

if __name__ == '__main__':
    main()
