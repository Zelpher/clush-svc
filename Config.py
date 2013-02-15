import os

from ConfigParser import ConfigParser, NoSectionError
import ClusterShell.NodeSet as NodeSet
import Node, CircularDependencyError

class Config:
    ##### Internal classes
    class Nodes():
        def __init__(self, config):
            self.config = config
            self.nodes = {}

        def load(self):
            """
            Load nodes from config files
            """
            # { nodeName: <Node object>, ... }
            conf = ConfigParser()
            conf.read(['/etc/clush-svc/nodes.cfg',
                os.path.expanduser('~/.config/clush-svc/nodes.cfg')])
            try:
                for (nodes, manager) in conf.items('managers'):
                    for node in NodeSet.NodeSet(nodes):
                        node = node.lower()
                        if node not in self.nodes:
                            self.nodes[node] = Node.Node()
                        self.nodes[node].name = node
                        self.nodes[node].manager = manager
            except NoSectionError:
                pass

        def save(self):
            conf = ConfigParser()
            conf.add_section('managers')
            nodesByManager = Node.Node.group_by_manager(self.nodes.values())
            for manager in nodesByManager:
                nodes = NodeSet.NodeSet().fromlist([ node.name for node in
                    nodesByManager[manager] ])
                conf.set('managers', str(nodes), manager)
            cfgfile = open(os.path.expanduser(
                '~/.config/clush-svc/nodes.cfg'), 'w')
            conf.write(cfgfile)
            cfgfile.close()

        def get_from_nodeset(self, nodeset):
            """
            Take a NodeSet and return a list of Nodes with their known
            settings
            """
            return [ self.nodes[node] if node in self.nodes else Node.Node(node)
                    for node in nodeset ]

    class Services():
        def __init__(self, config):
            self.config = config
            self.services = {}

        def load(self):
            """
            Load services from config files
            """
            # { serviceName: { <NodeSet object>: script }, ... }
            conf = ConfigParser()
            conf.read(['/etc/clush-svc/services.cfg',
                os.path.expanduser('~/.config/clush-svc/services.cfg')])
            for service in conf.sections():
                self.services[service] = {}
                for (nodeset, script) in conf.items(service):
                    nodeset = NodeSet.NodeSet(nodeset.lower())
                    self.services[service][nodeset] = script

        def save(self):
            conf = ConfigParser()
            for service in self.services:
                conf.add_section(service)
                for nodeset in self.services[service]:
                    conf.set(service, str(nodeset),
                            self.services[service][nodeset])
            cfgfile = open(os.path.expanduser(
                '~/.config/clush-svc/services.cfg'), 'w')
            conf.write(cfgfile)
            cfgfile.close()

        def get_alias(self, service, node):
            """
            Return the script name for a given service on a given node. Return the
            given service name if it does not have any alias defined.
            """
            if service in self.services:
                for nodeset in self.services[service]:
                    if node in nodeset:
                        return self.services[service][nodeset]
            return service

    class Dependencies():
        def __init__(self, config):
            self.config = config
            self.dependencies = {}

        def load(self):
            """
            Load dependencies from config files
            """
            # { serviceName: { <NodeSet object>: [dependency1, ...], ... }, ... }
            conf = ConfigParser()
            conf.read(['/etc/clush-svc/dependencies.cfg',
                os.path.expanduser('~/.config/clush-svc/dependencies.cfg')])
            for service in conf.sections():
                self.dependencies[service] = {}
                for (nodeset, dependencies) in conf.items(service):
                    dependencies = map(str.strip, dependencies.split(','))
                    nodeset = NodeSet.NodeSet(nodeset.lower())
                    self.dependencies[service][nodeset] = dependencies

        def save(self):
            conf = ConfigParser()
            for service in self.dependencies:
                conf.add_section(service)
                for nodeset in self.dependencies[service]:
                    conf.set(service, str(nodeset),
                            ', '.join(self.dependencies[service][nodeset]))
            cfgfile = open(os.path.expanduser(
                '~/.config/clush-svc/dependencies.cfg'), 'w')
            conf.write(cfgfile)
            cfgfile.close()

        def get_for_one(self, service, node):
            """
            Return the local services required by a given service on a given node
            as a set of their names
            """
            deps = set()
            if service in self.dependencies:
                for nodeset in self.dependencies[service]:
                    if node in nodeset:
                        deps = deps.union(self.dependencies[service][nodeset])
            return deps

        def get_for_many(self, arg_dependencies):
            """
            Take and return a dict with services as keys and a set of Nodes as
            values. Allows to easily get a list of tasks and their nodes to run
            before you can start the given services.
            { 'service': set(<Node object>, ...), ... }
            """
            dependencies = {}
            for arg_service in arg_dependencies:
                for node in arg_dependencies[arg_service]:
                    for dep_service in self.get_for_one(arg_service, node.name):
                        if dep_service not in dependencies:
                            dependencies[dep_service] = set()
                        dependencies[dep_service].add(node)
            return dependencies

        def get_recursive(self, arg_services):
            """
            Recursively get all dependencies for a given set of services on a
            given node. Return a list of dependencies groups, from the
            independent one to the most dependent one.
            [ { 'service': set(<Node object>, ...), ... }, ... ]
            """
            all_dependencies = []
            dependencies = self.get_for_many(arg_services)
            while dependencies:
                # check for circular dependencies
                for service in dependencies:
                    for node in dependencies[service]:
                        for dependency in all_dependencies:
                            if service in dependency:
                                if node in dependency[service]:
                                    raise CircularDependencyError(service, node)
                all_dependencies.append(dependencies)
                dependencies = self.get_for_many(dependencies)
            all_dependencies.reverse()
            return all_dependencies

    class Groups():
        def __init__(self, config):
            self.config = config
            self.groups = {}

        def load(self):
            """
            Load groups from config files
            """
            # { groupName: { serviceName: <NodeSet object>, ... }, ... }
            conf = ConfigParser()
            conf.read(['/etc/clush-svc/groups.cfg',
                os.path.expanduser('~/.config/clush-svc/groups.cfg')])
            for group in conf.sections():
                group = group.lower()
                self.groups[group] = {}
                for (service, nodeset) in conf.items(group):
                    nodeset = NodeSet.NodeSet(nodeset.lower())
                    self.groups[group][service] = nodeset

        def save(self):
            conf = ConfigParser()
            for group in self.groups:
                conf.add_section(group)
                for service in self.groups[group]:
                    conf.set(group, service, str(self.groups[group][service]))
            cfgfile = open(os.path.expanduser(
                '~/.config/clush-svc/groups.cfg'), 'w')
            conf.write(cfgfile)
            cfgfile.close()

        def get(self, group):
            """
            Return the services and associated NodeSets of a given group by its name.
            { serviceName: <NodeSet object>, ... }
            """
            return self.groups[group].copy() if group in self.groups else {}
    ##########

    def __init__(self):
        self.nodes = Config.Nodes(self)
        self.services = Config.Services(self)
        self.dependencies = Config.Dependencies(self)
        self.groups = Config.Groups(self)
        self.load()

    def check_home_cfg(self):
        path = os.path.expanduser("~/.config/clush-svc")
        try:
            os.listdir(path)
        except OSError:
            os.mkdir(path)

    def load(self):
        """
        Read config files and load them
        """
        self.nodes.load()
        self.services.load()
        self.dependencies.load()
        self.groups.load()

    def save(self):
        """
        Save config to files in ~/.config/clush-svc/
        """
        self.check_home_cfg()
        self.nodes.save()
        self.services.save()
        self.dependencies.save()
        self.groups.save()
