import os
from lxml import etree
from pyquery import PyQuery
from weld import weld
from nose.util import *

def get_template(name):
    filename = os.path.join(os.path.dirname(__file__), 'test.html')
    file = open(filename, 'rb')
    source = file.read()

    return PyQuery(source)('#weld-templates')\
            .clone()\
            .find('#' + name)

def test_sanity():
    """Test 1: Sanity"""
    template = PyQuery('<div><a class="link"></a></div>')('div')

    def set_text(p, e, k, v):
        template(e).text('woo')

    weld(template, dict(link='text'), dict(set=set_text, debug=True))
    eq_(template.text(), 'woo')

def test_object_literal():
    "Test 2: Assign data to elements using an object literal that has one level of depth"
    template = get_template('singular')

    data = dict(key='someKey', value='someValue', icon='/path/to/image.png')
    weld(template, data)

    eq_(template('.key').text(), data['key'])
    eq_(template('.icon').attr('src'), data['icon'])
    eq_(template('.input[name="value"]').val(), data['value'])
