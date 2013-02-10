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
    config = Config.Config()
    # parse_nodes needs config
    arg_nodes = config.nodes.get_from_nodeset(NodeSet.NodeSet(options.nodes))
    arg_service = args[0]

    all_dependencies = config.dependencies.get_recursive(arg_service, arg_nodes)
    for dependencies_group in all_dependencies:
        tasks = {}
        for dependency in dependencies_group:
            tasks.update(Node.Node.group_by_script(config, dependency, 
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
