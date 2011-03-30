# -*- coding: utf-8 -*-

import inspect, types
from lxml import etree
from copy import deepcopy
import collections, logging

log = logging.getLogger(__name__)

e = lambda x: etree.tostring(x)

def d_label(action, element):
    return '%s - element: %s, class: %s, id: %s' %\
        (action.upper(), colorize(e(element)),\
                colorize(element.get('class')), colorize(element.get('id')))

def d(action, element):
    log.debug('- %s' % d_label(action, element))

class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

depth = 0
welds = {}

def has_weld(element):
    return id(element) in welds

def get_weld(element):
    return welds.get(id(element), None)

def set_weld(element, w):
    global welds
    welds[id(element)] = w
    return w

color = AttrDict(dict(gray='\033[37m', darkgray='\033[40;30m', red='\033[31m',\
    green='\033[32m', yellow='\033[33m', lightblue='\033[1;34m',\
    cyan='\033[36m', white='\033[1;37m'))

successIndicator = color.green + ' ✓' + color.gray
failureIndicator = color.red + ' ✗' + color.gray

pad = lambda: '│    ' * depth

def colorize(val):
    sval = str(val)

    if sval in ('False', 'None', '') or val is False:
        return color.red + '<' + sval + '>' + color.gray
    else:
        return color.yellow + sval + color.gray

def debuggable(name, func=None):
    label = name.upper()

    def new_func(parent, element, key=None, value=None):
        global depth

        depth += 1
        log.debug('%s%s┌ %s - parent:%s, element:%s, key:%s, value:%s'\
                % (pad(), color.gray, label,\
                    colorize(parent is not None and e(parent) or 'None'),\
                    colorize(e(element)),\
                    colorize(key), colorize(value)))

        res = func(parent, element, key, value)
        if res is not False:
            indicator = successIndicator
        else:
            indicator = failureIndicator

        depth -= 1
        log.debug('%s└ %s%s' % (pad(), e(element), indicator))

        return res

    return new_func

def weld(DOMTarget, data, pconfig={}):
    assert isinstance(DOMTarget, etree._Element)

    def check_args(parent, element):
        assert parent is None or isinstance(parent, etree._Element)
        assert isinstance(element, etree._Element)

    def siblings(parent, element, key, value):
        check_args(parent, element)

        siblings = parent.getchildren()
        cs = len(siblings)

        w = set_weld(element, AttrDict(parent=parent,\
                classes=element.get('class', '').split(' '),
                insertBefore=None))

        while cs:
            cs -= 1
            sibling = siblings[cs]

            if sibling is element:
                if config.debug:
                    d('remove', element)

                index = parent.index(element)
                parent.remove(element)

                if index < len(parent):
                    w.insertBefore = parent[index]
            else:
                classes = sibling.get('class', '').split(' ')
                match = True

                for _class in classes:
                    if _class not in w.classes:
                        match = False
                        break

                if match:
                    if config.debug:
                        d('remove', sibling)

                    parent.remove(sibling)

    def traverse(parent, element, key, value):
        check_args(parent, element)

        template = element
        templateParent = element.getparent()

        if value is None or isinstance(value, types.StringTypes) or isinstance(value, etree._Element):
            ops.set(parent, element, key, value)
        else:
            if isinstance(value, collections.Sequence):
                if templateParent is not None:
                    ops.siblings(templateParent, template, key, value)
                elif has_weld(template):
                    w = get_weld(template)
                    templateParent = w.parent

                for index, obj in enumerate(value):
                    if config.debug:
                        d('clone', element)

                    target = deepcopy(element)
                    w = set_weld(target, AttrDict())

                    if has_weld(element):
                        w.update(get_weld(element))

                    ops.traverse(templateParent, target, index, obj)
                    ops.insert(templateParent, target)
            else:
                for key, obj in value.items():
                    target = ops.match(template, element, key, obj)
                    if target not in (None, False):
                        ops.traverse(template, target, key, obj)

    def insert(parent, element, key=None, value=None):
        check_args(parent, element)

        if has_weld(element):
            w = get_weld(element)
            if hasattr(w, 'insertBefore') and w.insertBefore > 0:
                if config.debug:
                    log.debug('Insert %s before element %s in %s' %
                        (e(element),
                            w.insertBefore,
                            e(parent)))
                parent.insert(parent.index(w.insertBefore), element)
                return

        if None not in (parent, element):
            parent.append(element)

    def element_type(parent, element, key, value):
        check_args(parent, element)

        if isinstance(element, etree._Element):
            node_name = element.tag

            if node_name.lower() in ('input', 'select', 'textarea',\
                    'option', 'button'):
                return 'input'

            if node_name == 'img':
                return 'image'

    def map(parent, element, key, value):
        check_args(parent, element)

        return True

    def set(parent, element, key, value):
        check_args(parent, element)

        if ops.map(parent, element, key, value) is False:
            return False

        if config.debug:
            log.debug('- SET: element:%s, key:%s, value:%s' % (element.tag, key, value))

        element_type = ops.element_type(parent, element, key, value)

        if value is not None and isinstance(value, etree._Element):
            if value.getparent() is not None:
                value.getparent().remove(value)

            element[:] = []
            element.text = ''

            element.append(value)
        elif element_type == 'input':
            element.set('value', value)
        elif element_type == 'image':
            element.set('src', value)
        else:
            element.text = value

        return True

    def match(parent, element, key, value):
        check_args(parent, element)

        if key in config.alias:
            if config.alias[key] is False:
                return False
            elif inspect.isfunction(config.alias[key]):
                func = config.alias[key]
                result = func(parent, element, key, value)
                if result is not None:
                    key = result
            else:
                key = config.alias[key]

        if isinstance(key, etree._Element):
            return key

        if element is not None:
            selector = "descendant::*[contains(@class, '{0}')] | descendant::*[@id='{0}'] | descendant::*[@name='{0}']".format(key)
            result = element.xpath(selector)
            if result:
                return result[0]

    config = AttrDict(dict(alias={}, debug=False, insert=False))
    config.update(pconfig)

    parent = DOMTarget.getparent()

    ops = AttrDict(dict(filter(lambda index: inspect.isfunction(index[1]),\
        locals().items())))

    for name, func in ops.items():
        if name in config and config[name]:
            func = config[name]

        if config.debug:
            func = debuggable(name, func)

        ops[name] = func

    ops.traverse(None, DOMTarget, None, data)

    if config.debug:
        if parent:
            debug = e(parent)
        else:
            debug = 'None'

        log.debug(debug)
