#!/usr/bin/env python

import ClusterShell.Task as Task
import ClusterShell.NodeSet as NodeSet
from optparse import OptionParser

def main():
    parser = OptionParser()
    parser.add_option("-w", dest="nodes")
    (options, args) = parser.parse_args()

    task = Task.task_self()
    task.run("/etc/init.d/%s %s"%(args[0], args[1]), nodes=options.nodes)
    rc_str = {0: 'ok', 3: 'service not running', 255: 'erreur'}
    for (rc, keys) in task.iter_retcodes():
        print NodeSet.NodeSet.fromlist(keys), rc_str[rc]

if __name__ == '__main__':
    main()
