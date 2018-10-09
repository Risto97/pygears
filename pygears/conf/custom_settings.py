import inspect
import json
import os
import pprint
import runpy

import yaml

from .log import conf_log
from .registry import PluginBase, bind
from .utils import dict_generator

PYGEARSRC = '.pygears'


def print_registry():
    reg = pprint.pformat(PluginBase.registry)
    conf_log().info(f'Registry settings:\n{reg}')


class RCSettings:
    def __init__(self):
        search_dirs = self.find_seach_dirs()
        for path in reversed(search_dirs):
            self.find_rc(path)

    def find_seach_dirs(self):
        search_dirs = []
        home_path = os.environ.get('HOME')

        _, filename, _, function_name, _, _ = inspect.stack()[-1]
        dirname = os.path.dirname(filename)
        search_dirs.append(dirname)

        while dirname not in ('/', home_path):
            dirname = os.path.abspath(os.path.join(dirname, '..'))
            search_dirs.append(dirname)

        search_dirs.append(home_path)

        return search_dirs

    def find_rc(self, dirname):
        rc_path = os.path.join(dirname, PYGEARSRC + '.py')
        if (os.path.exists(rc_path)):
            runpy.run_path(rc_path)
            return

        conf = None
        rc_path = os.path.join(dirname, PYGEARSRC + '.yaml')
        if (os.path.exists(rc_path)):
            with open(rc_path) as f:
                conf = yaml.safe_load(f)

        rc_path = os.path.join(dirname, PYGEARSRC + '.json')
        if (os.path.exists(rc_path)):
            with open(rc_path) as f:
                conf = json.load(f)

        if conf:
            for c_list in dict_generator(conf):
                keys = '/'.join([str(x) for x in c_list[:-1]])
                bind(keys, c_list[-1])
