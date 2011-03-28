# -*- coding: utf-8 -*-

import inspect
from lxml import etree
from copy import deepcopy
import collections, logging.config
from pyquery import PyQuery

logging.config.fileConfig('logging.ini')
log = logging.getLogger(__name__)

def d_label(action, element):
    return '%s - element: %s, class: %s, id: %s' %\
        (action.upper(), colorize(etree.tostring(element)),\
                colorize(element.get('class')), colorize(element.get('id')))

def d(action, element):
    log.debug('- %s' % d_label(action, element))

class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

depth = 0

color = AttrDict(dict(gray='\033[37m', darkgray='\033[40;30m', red='\033[31m',\
    green='\033[32m', yellow='\033[33m', lightblue='\033[1;34m',\
    cyan='\033[36m', white='\033[1;37m'))

successIndicator = color.green + ' ✓' + color.gray
failureIndicator = color.red + ' ✗' + color.gray

pad = lambda: '│    ' * depth

def colorize(val):
    sval = str(val)

    if sval in ('False', 'None', '') or val is False:
        if sval is '':
            sval = '(empty string)'
        return color.red + sval + color.gray
    else:
        return color.yellow + sval + color.gray

    return sval

def debuggable(name, func=None):
    label = name.upper()

    def new_func(parent, element, key=None, value=None):
        global depth
        depth += 1

        log.debug('%s%s┌ %s - parent:%s, element:%s, key:%s, value:%s'\
                % (pad(), color.gray, label,\
                    colorize(parent is not None and etree.tostring(parent) or 'None'),\
                    colorize(etree.tostring(element)),\
                    colorize(key), colorize(value)))

        if inspect.isfunction(func):
            res = func(parent, element, key, value)
            depth -= 1
            if res is not False:
                indicator = successIndicator
            else:
                indicator = failureIndicator

            log.debug('%s└ %s%s' % (pad(), etree.tostring(element), indicator))
            return res

        depth -= 1
        d('OPERATION NOT FOUND', label)

    return new_func

def weld(DOMTarget, data, pconfig={}):
    assert isinstance(DOMTarget, etree._Element)

    def _check_args(parent, element):
        assert parent is None or isinstance(parent, etree._Element)
        assert isinstance(element, etree._Element)

    def siblings(parent, element, key, value):
        _check_args(parent, element)

        siblings = parent.getchildren()
        cs = len(siblings)

        element.weld = AttrDict(parent=parent,\
                classes=element.get('class', '').split(' '), insertBefore=None)

        while cs:
            cs -= 1
            sibling = siblings[cs]

            if sibling is element:
                if debug:
                    d('remove', element)

                index = parent.index(element)
                parent.remove(element)

                if index < len(parent):
                    element.weld.insertBefore = parent[index]
            else:
                classes = sibling.get('class', '').split(' ')
                match = True

                for _class in classes:
                    if _class not in element.weld.classes:
                        match = False
                        break

                if match:
                    if debug:
                        d('remove', sibling)

                    parent.remove(sibling)

    def traverse(parent, element, key, value):
        _check_args(parent, element)

        template = element
        templateParent = element.getparent()

        if value is None or isinstance(value, str) or isinstance(value, etree._Element):
            ops.set(parent, element, key, value)
        elif isinstance(value, collections.Sequence) and len(value) and value[0] is not None:
            if templateParent is not None:
                ops.siblings(templateParent, template, key, value)
            elif None not in (template.weld, template.weld.parent):
                templateParent = template.weld.parent

            for index, obj in enumerate(value):
                if debug:
                    d('clone', element)

                target = deepcopy(element)
                target.weld = AttrDict()

                if element.weld is not None:
                    target.weld.update(element.weld)

                ops.traverse(templateParent, target, index, obj)
                ops.insert(templateParent, target)
        else:
            for key, obj in value.items():
                target = ops.match(template, element, key, obj)
                if target is not None:
                    ops.traverse(template, target, key, obj)

    def insert(parent, element, key=None, value=None):
        _check_args(parent, element)

        if None not in (element.weld, element.weld.insertBefore):
            if debug:
                log.debug('Insert %s before element %s in %s' %
                    (etree.tostring(element),
                        etree.tostring(element.weld.insertBefore),
                        etree.tostring(parent)))
            parent.insert(parent.index(element.weld.insertBefore), element)
        else:
            parent.append(element)

    def element_type(parent, element, key, value):
        _check_args(parent, element)

        if isinstance(element, etree._Element):
            node_name = element.tag

            if node_name.lower() in ('input', 'select', 'textarea',\
                    'option', 'button'):
                return 'input'

            if node_name == 'img':
                return 'image'

    def map(parent, element, key, value):
        _check_args(parent, element)

        return True

    def set(parent, element, key, value):
        _check_args(parent, element)

        if ops.map(parent, element, key, value) is False:
            return False

        if debug:
            log.debug('- SET: element:%s, key:%s, value:%s' % (element.tag, key, value))

        type = ops.element_type(parent, element, key, value)

        if value is not None and isinstance(value, etree._Element):
            if element.ownerDocument != value.ownerDocument:
                value = element.ownerDocument.importNode(value, true)
            elif value.getparent() is not None:
                value.getparent().removeChild(value)

            while element.firstChild is not None:
                element.removeChild(element.firstChild)

            element.appendChild(value)
        elif type == 'input':
            element.set('value', value)
        elif type == 'image':
            element.set('src', value)
        else:
            element.text = value

        return True

    def match(parent, element, key, value):
        _check_args(parent, element)

        if 'alias' in config:
            if config.alias and key in config.alias:
                if inspect.isfunction(config.alias[key]):
                    key = config.alias[key](parent, element, key, value) or key
                elif config.alias[key] is False:
                    return False
                else:
                    key = config.alias[key]

        if isinstance(key, etree._Element):
            return key

        if element is not None:
            selector = "//*[contains(@class, '{0}')] | //*[@id='{0}'] | //*[@name='{0}']".format(key)
            result = element.xpath(selector)
            if result:
                return result[0]

    parent = DOMTarget.getparent()

    config = AttrDict(dict(alias={}, debug=False, insert=False))
    config.update(pconfig)

    debug = config['debug']

    ops = AttrDict(dict(filter(lambda index: inspect.isfunction(index[1]),\
        locals().items())))

    for name, func in ops.items():
        if name in config and config[name]:
            func = config[name]

        if debug:
            func = debuggable(name, func)

        ops[name] = func

    ops.traverse(None, DOMTarget, None, data)

    if debug:
        if parent:
            debug = parent.html()
        else:
            debug = 'None'

        log.debug(debug)

def pyquery_weld(data, config={}):
    weld(this[0], data, config)
    return this

PyQuery.fn.weld = pyquery_weld
