managers = {
    'service': {
        'base': 'service ',
        'start': "start %s",
        'stop': "stop %s",
        'restart': "restart %s",
        'status': "status %s",
    },
    'sysvinit': {
        'base': '/etc/init.d/',
        'start': "%s start",
        'stop': "%s stop",
        'restart': "%s restart",
        'status': "%s status",
    },
    'bsdinit': {
        'base': '/etc/rc.d/',
        'start': "%s start",
        'stop': "%s stop",
        'restart': "%s restart",
        'status': "%s status",
    },
    'systemd': {
        'base': 'systemctl ',
        'start': "start %s.service",
        'stop': "stop %s.service",
        'restart': "restart %s.service",
        'status': "status %s.service",
    }
}

def get_command(manager, service, action):
    return managers[manager]['base']+managers[manager][action]%service
