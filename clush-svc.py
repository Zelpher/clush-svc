#!/usr/bin/env python

from optparse import OptionParser

import ClusterShell.Task as Task
import ClusterShell.NodeSet as NodeSet

import Config, Node
import managers

def remove_nodes_from_tree(dependencies, nodes):
    """
    Remove nodes from the commands tree.
    nodes should be a nodeset or a nodes hostnames list.
    """
    for depindex in xrange(len(dependencies)):
        for service in dependencies[depindex]:
            for node in nodes:
                for depnode in dependencies[depindex][service].copy():
                    if node == depnode.name:
                        dependencies[depindex][service].remove(depnode)

def tasks_run(arg_tasks, action):
    """
    Prepare and run tasks
    """
    print "TASKS RUN =>", action
    tasks = []
    for script in arg_tasks:
        groupedNodes = Node.Node.group_by_manager(arg_tasks[script])
        for manager in groupedNodes:
            task = Task.Task()
            nodesList = ','.join([node.name for node in groupedNodes[manager]])
            command = managers.get_command(manager=manager, service=script,
                action=action)
            print "Task run: " + command + ", nodes: " + nodesList
            task.run(command, nodes=nodesList)
            tasks.append((task, script))
    return tasks

def dependencies_run(config, dependencies, action):
    """
    Prepare and run a list of dependent tasks groups
    """
    print "DEPENDENCIES GROUP RUN =>", action
    for depgroupindex in xrange(len(dependencies)):
        commands = {}
        for dependency in dependencies[depgroupindex]:
            commands.update(Node.Node.group_by_script(config, dependency, 
                dependencies[depgroupindex][dependency]))
        tasks = tasks_run(commands, action)
        for (task, script) in tasks:
            task.join()
            task.abort()
        print "--------------------------"
        # check status for each service
        if action not in ('status', 'stop'):
            tasks = tasks_run(commands, 'status')
            for (task, script) in tasks:
                task.join()
                for (rc, keys) in task.iter_retcodes():
                    nodes = NodeSet.NodeSet.fromlist(keys)
                    if rc != 0:
                        print "%s on %s: failed" %(script, nodes)
                        remove_nodes_from_tree(dependencies, nodes)
                task.abort()
        print "=========================="

def main():
    # Parse command line options
    parser = OptionParser()
    parser.add_option("-w", dest="nodes")
    (options, args) = parser.parse_args()

    # Read config
    config = Config.Config()
    # parse_nodes needs config
    arg_nodes = config.nodes.get_from_nodeset(
            NodeSet.NodeSet(options.nodes.lower()))
    arg_service = args[0]
    arg_action = args[1]

    # Do we check dependencies too?
    if arg_action in ('start', 'status'): # if arg_action not in ('stop', 'restart')
        dependencies = config.dependencies.get_recursive(arg_service, arg_nodes)
        dependencies.append({arg_service: set(arg_nodes)})
        dependencies_run(config, dependencies, arg_action)
    else:
        dependencies = [{arg_service: set(arg_nodes)}]
        dependencies_run(config, dependencies, arg_action)

if __name__ == '__main__':
    main()
