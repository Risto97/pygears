import inspect
import logging
import os

from pygears import PluginBase, registry, safe_bind, config
from pygears.conf import register_custom_log
from pygears.core.hier_node import HierVisitorBase
from .intf import SVIntfGen
from pygears.definitions import LIB_SVLIB_DIR, USER_SVLIB_DIR


class SVGenInstVisitor(HierVisitorBase):
    def __init__(self):
        self.namespace = registry('svgen/module_namespace')
        self.svgen_map = registry('svgen/map')

    def RTLGear(self, node):
        if 'svgen' not in node.params:
            node.params['svgen'] = {}

        if 'svgen_cls' not in node.params['svgen']:
            svgen_cls = self.namespace.get(node.gear.definition, None)

            if svgen_cls is None:
                for base_class in inspect.getmro(node.gear.__class__):
                    if base_class.__name__ in self.namespace:
                        svgen_cls = self.namespace[base_class.__name__]
                        break

            node.params['svgen']['svgen_cls'] = svgen_cls

    def RTLNode(self, node):
        svgen_cls = node.params['svgen']['svgen_cls']

        if svgen_cls:
            svgen_inst = svgen_cls(node)
        else:
            svgen_inst = None

        self.svgen_map[node] = svgen_inst

    def RTLIntf(self, intf):
        self.svgen_map[intf] = SVIntfGen(intf)


def svgen_inst(top, conf):
    config['hdl/include_paths'].extend([USER_SVLIB_DIR, LIB_SVLIB_DIR])

    v = SVGenInstVisitor()
    v.visit(top)

    return top


def svgen_log():
    return logging.getLogger('svgen')


class SVGenInstPlugin(PluginBase):
    @classmethod
    def bind(cls):
        safe_bind('svgen/map', {})
        register_custom_log('svgen', logging.WARNING)

    @classmethod
    def reset(cls):
        safe_bind('svgen/map', {})
