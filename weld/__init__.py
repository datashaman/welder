# -*- coding: utf-8 -*-

import inspect
from lxml import etree
import collections, logging.config
from pyquery import PyQuery

logging.config.fileConfig('logging.ini')
log = logging.getLogger(__name__)

class AttrDict(dict):
    def __init__(self, d = {}):
        dict.__init__(self, d)
        self.__dict__ = self

depth = 0

color = AttrDict(dict(gray='\033[37m', darkgray='\033[40;30m', red='\033[31m',\
    green='\033[32m', yellow='\033[33m', lightblue='\033[1;34m',\
    cyan='\033[36m', white='\033[1;37m'))

successIndicator = color.green + ' ✓' + color.gray
failureIndicator = color.red + ' ✗' + color.gray

def pad():
    global depth

    l = depth
    ret = ''

    while(l > 0):
        ret += '│    '
        l = l - 1

    return ret

def colorize(val):
    sval = str(val)

    if sval is 'False' or sval is 'None' or sval is "" or val is False:
        if sval is "":
            sval = '(empty string)'
        return color.red + sval + color.gray
    else:
        return color.yellow + sval + color.gray

    return sval


def debuggable(name, func=None):
    label = name.upper()

    def new_func(p, e, k, v):
        global depth

        log.debug('%s%s┌ %s - parent:%s, element:%s, key:%s, value:%s'\
                % (pad(), color.gray, label, colorize(p), colorize(e),\
                    colorize(k), colorize(v)))
        depth = depth + 1

        if func:
            res = func(p, e, k, v)
            depth = depth - 1
            if res is not False:
                indicator = successIndicator
            else:
                indicator = failureIndicator

            log.debug('%s└ %s%s' % (pad(), e.__html__(), indicator))
            return res

        depth = depth - 1
        d('- OPERATION NOT FOUND: ', label)

    return new_func

def weld(DOMTarget, data, pconfig={}):
    def element_type(p, e, k, v):
        if e:
            node_name = e[0].tag

            if isinstance(node_name, str):
                if node_name.lower() in ('input', 'select', 'textarea',\
                        'option', 'button'):
                    return 'input'

                if node_name == 'img':
                    return 'image'

    def map(p, e, k, v):
        return True

    def set(p, e, k, v):
        if ops.map(p, e, k, v) == False:
            return False

        if debug:
            log.debug('- SET: value is %s' % v.tagName)

        type = ops.element_type(p, e, k, v)
        res = False

        if None not in (v, v.nodeType):
            if e.ownerDocument != v.ownerDocument:
                value = e.ownerDocument.importNode(v, true)
            elif v.getparent() is not None:
                v.getparent().removeChild(v)

            while e.firstChild is not None:
                e.removeChild(e.firstChild)

            e.appendChild(v)
            res = True
        elif type == 'input':
            e.setAttribute('value', v)
            res = True
        elif type == 'image':
            e.setAttribute('src', v)
            res = True
        else:
            e.textContent = v
            res = True

        return res

    def match(p, e, k, v):
        if 'alias' in config:
            if config.alias and k in config.alias:
                if inspect.isfunction(config.alias[k]):
                    k = config.alias[k](p, e, k, v) or k
                elif config.alias[k] is False:
                    return False
                else:
                    k = config.alias[k]

        if k and hasattr(k, 'nodeType'):
            return k

        if e:
            selector = '.{0}, #{0}, [name="{0}"]'.format(k)
            return e(selector)

    def traverse(p, e, k, v):
        template = e
        templateParent = e.parent()

        if v is None or isinstance(v, str):
            ops.set(p, e, k, v)
        elif isinstance(v, collections.Sequence):
            if templateParent is not None:
                ops.siblings(templateParent, template, k, v)
            elif None not in (template.weld, template.weld.parent):
                templateParent = template.weld.parent

            for i, val in enumerate(value):
                if debug:
                    log.debug('- CLONE - element: %s class: %s id: %s' % (element, element.className, element.id))

                target = e.clone()
                target.weld = {}

                if element.weld is not None:
                    target.weld.update(element.weld)

                ops.traverse(templateParent, target, i, val)
                ops.insert(templateParent, target)
        else:
            for key, obj in v.items():
                target = ops.match(template, e, key, obj)
                if target:
                    ops.traverse(template, target, key, obj)

    parent = DOMTarget.parent()

    config = AttrDict(dict(alias={}, debug=False, insert=False))
    config.update(pconfig)

    debug = config['debug']

    print debug

    ops = AttrDict(dict(filter(lambda i: inspect.isfunction(i[1]),\
        locals().items())))

    for name, func in ops.items():
        if name in config:
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

def pyquery_weld(data, config=dict(debug=True)):
    weld(this[0], data, config)
    return this

PyQuery.fn.weld = pyquery_weld
