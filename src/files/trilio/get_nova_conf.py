from oslo_config import cfg
from nova import config as nova_conf
import sys

CONF = cfg.CONF

default_config_files = sys.argv[1].split(',') if len(
    sys.argv) > 1 else ['/etc/nova/nova.conf']

nova_conf.parse_args(["/usr/bin/nova-compute"])
if not ('config_file' in CONF.keys() and CONF['config_file']):
    try:
        nova_conf.parse_args(
            ["/usr/bin/nova-compute"],
            default_config_files=default_config_files)
    except cfg.ConfigFilesNotFoundError:
        raise
    except BaseException:
        pass

config_files = " --config-file=".join([""] + CONF['config_file']).strip()
print(config_files)
