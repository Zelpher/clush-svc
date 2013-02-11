#!/usr/bin/env python

from optparse import OptionParser

import ClusterShell.Task as Task
import ClusterShell.NodeSet as NodeSet

import Config, Node
import managers

def tasks_run(arg_tasks, action):
    """
    Prepare and launch tasks
    """
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

def main():
    # Parse command line options
    parser = OptionParser()
    parser.add_option("-w", dest="nodes")
    (options, args) = parser.parse_args()

    # Read config
    config = Config.Config()
    # parse_nodes needs config
    arg_nodes = config.nodes.get_from_nodeset(NodeSet.NodeSet(options.nodes))
    arg_service = args[0]
    arg_action = args[1]

    all_dependencies = config.dependencies.get_recursive(arg_service, arg_nodes)
    all_dependencies.append({arg_service: set(arg_nodes)})
    for depgroupindex in xrange(len(all_dependencies)):
        commands = {}
        for dependency in all_dependencies[depgroupindex]:
            commands.update(Node.Node.group_by_script(config, dependency, 
                all_dependencies[depgroupindex][dependency]))
        tasks = tasks_run(commands, arg_action)
        for (task, script) in tasks:
            task.join()
            task.abort()
        print "--------------------------"
        # check status for each service
        if arg_action != 'status':
            tasks = tasks_run(commands, 'status')
            for (task, script) in tasks:
                task.join()
                for (rc, keys) in task.iter_retcodes():
                    nodes = NodeSet.NodeSet.fromlist(keys)
                    if rc != 0:
                        print "%s on %s: failed" %(script, nodes)
                        remove_nodes_from_tree(all_dependencies, nodes)
                task.abort()
        print "=========================="
    # Lancer les taches principales
    print "fin du main"

if __name__ == '__main__':
    main()
