from optparse import OptionParser
import sys

import ClusterShell.Task as Task
import ClusterShell.NodeSet as NodeSet

import Config, Node
import managers

class ClushSvcCLI:
    def __init__(self):
        self.config = None
        # For GUI display
        self.result = []

    def remove_nodes_from_tree(self, dependencies, nodes):
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

    def tasks_run(self, arg_tasks, action):
        """
        Prepare and run tasks
        """
        print "TASKS RUN =>", action
        workers = []
        task = Task.task_self()
        for script in arg_tasks:
            groupedNodes = Node.Node.group_by_manager(arg_tasks[script])
            for manager in groupedNodes:
                nodesList = ','.join([node.name for node in groupedNodes[manager]])
                command = managers.get_command(manager=manager, service=script,
                    action=action)
                print "Task run: " + command + ", nodes: " + nodesList
                worker = task.shell(command, nodes=nodesList)
                workers.append((worker, script))
        task.run()
        task.join()
        return workers

    def dependencies_run(self, dependencies, action):
        """
        Prepare and run a list of dependent tasks groups
        """
        self.result = []
        print "DEPENDENCIES GROUP RUN =>", action
        for depgroupindex in xrange(len(dependencies)):
            commands = {}
            for dependency in dependencies[depgroupindex]:
                commands.update(Node.Node.group_by_script(self.config, dependency, 
                    dependencies[depgroupindex][dependency]))
            if action not in ('status'):
                tasks = self.tasks_run(commands, action)
                print "--------------------------"
            # check status for each service
            tasks = self.tasks_run(commands, 'status')
            for (task, script) in tasks:
                for (rc, keys) in task.iter_retcodes():
                    nodes = NodeSet.NodeSet.fromlist(keys)
                    success = False if rc != 0 else True
                    success = not success if action in ('stop') else success
                    if success:
                        self.result.append((nodes, script, "success"))
                    else:
                        self.result.append((nodes, script, "failed"))
                        print "%s on %s: failed" %(script, nodes)
                        self.remove_nodes_from_tree(dependencies, nodes)
            print "=========================="

    def main(self):
        arg_nodes = None
        arg_group = None
        arg_service = None
        arg_action = None

        # Parse command line options
        parser = OptionParser(usage="%prog [-w NODES SERVICE | " +
                "GROUP] ACTION")
        parser.add_option("-w", dest="nodes",
                help="nodes where to run the command")
        (options, args) = parser.parse_args()
        if len(args) != 2:
            parser.print_usage()
            sys.exit(1)

        # Read config
        self.config = Config.Config()

        # are we using groups?
        if (not options.nodes):
            arg_group = args[0]
            arg_action = args[1]
            arg_task = self.config.groups.get(arg_group.lower())
            for service in arg_task:
                arg_task[service] = set(self.config.nodes.get_from_nodeset(
                    arg_task[service]))
        else:
            arg_nodes = self.config.nodes.get_from_nodeset(NodeSet.NodeSet(
                options.nodes.lower()))
            arg_service = args[0]
            arg_action = args[1]
            arg_task = {arg_service: set(arg_nodes)}

        # Do we check dependencies too?
        if arg_action in ('start', 'status'): # if arg_action not in ('stop', 'restart')
            dependencies = self.config.dependencies.get_recursive(arg_task)
            dependencies.append(arg_task)
            self.dependencies_run(dependencies, arg_action)
        else:
            dependencies = [arg_task]
            self.dependencies_run(dependencies, arg_action)
