managers = {
    'bsdinit': {
        'base': '/etc/rc.d/',
        'start': "%s start",
        'stop': "%s stop",
        'restart': "%s status",
        'status': "%s status",
    },
    'systemd': {
        'base': 'systemctl ',
        'start': "%s.service start",
        'stop': "%s.service stop",
        'restart': "%s.service status",
        'status': "%s.service status",
    },
    'sysvinit': {
        'base': '/etc/init.d/',
        'start': "%s start",
        'stop': "%s stop",
        'restart': "%s status",
        'status': "%s status",
    }
}

def get_command(manager, service, action):
    return managers[manager]['base']+managers[manager][action]%service
