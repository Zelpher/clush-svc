class CircularDependencyError(Exception):
    def __init__(self, service, node):
        self.service = service
        self.node = node
    def __str__(self):
        return "Service %s on node %s" %(self.service, self.node.name)
