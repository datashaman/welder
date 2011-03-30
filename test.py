import os
from lxml import etree, cssselect, html
from pyquery import PyQuery
from welder import weld
from nose.tools import *

data = (
    dict(name='hij1nx', title='code exploder'),
    dict(name='tmpvar', title='code pimp'),
)

def get_template(name):
    filename = os.path.join(os.path.dirname(__file__), 'test.html')
    file = open(filename, 'rb')
    source = file.read()

    return PyQuery(source)('#weld-templates')\
            .clone()\
            .find('#' + name)

def check_contacts(template, reversed=False):
    eq_(template('.contact').length, 2)

    if reversed:
        indices = '21'
    else:
        indices = '12'

    eq_(template('.contact:nth-child(%s) .foo' % indices[0]).text(), 'hij1nx')
    eq_(template('.contact:nth-child(%s) .foo' % indices[1]).text(), 'tmpvar')

    eq_(template('.contact:nth-child(%s) .title' % indices[0]).text(), 'code exploder')
    eq_(template('.contact:nth-child(%s) .title' % indices[1]).text(), 'code pimp')

def test_sanity():
    """Test 1: Sanity"""
    template = PyQuery('<div><a class="link"></a></div>')

    def set_text(p, e, k, v):
        template(e).text('woo')

    weld(template[0], dict(link='text'), dict(set=set_text))
    eq_(template.text(), 'woo')

def test_object_literal():
    "Test 2: Assign data to elements using an object literal that has one level of depth"
    template = get_template('singular')

    data = dict(key='someKey', value='someValue', icon='/path/to/image.png')
    weld(template[0], data)

    eq_(template('.key').text(), data['key'])
    eq_(template('.icon').attr('src'), data['icon'])
    eq_(template(':input[@name="value"]').val(), data['value'])

def test_alias():
    """Test 3: Generate markup based on an element using the alias parameter to explicitly correlate data-keys and elements"""
    template = get_template('contacts-alias')

    weld(template('.contact')[0], data, dict(
        alias=dict(name='foo', title='title')
    ))

    check_contacts(template)

def test_alias_function():
    """Test 4: Generate markup based on an element using an (alias w/function) parameter to explicitly correlate data and elements"""
    template = get_template('contacts-alias')

    def alias_name(p, e, k, v):
        eq_(k, 'name')
        return 'foo'

    weld(template('.contact')[0], data, dict(alias=dict(name=alias_name,\
        title='title')))

    check_contacts(template)

times = 0

def test_alternate_insert():
    """Test 5: Generate markup from an element with an alternate insert method"""
    template = get_template('contacts')

    def alternate_insert(p, e, k=None, v=None):
        global times
        times += 1
        p.insert(0, e)

    weld(template('.contact')[0], data, dict(insert=alternate_insert))

    check_contacts(template, True)
    eq_(times, 2)

def test_reweld():
    """Test 6: Append to a node that has already been the subject of a weld"""
    template = get_template('contacts')

    data = (
        dict(name='hij1nx', title='manhattan'),
        dict(name='tmpvar', title='brooklyn'),
    )

    contact_template = template('.contact')[0]
    weld(contact_template, data)
    weld(contact_template, data)

    eq_(template('.contact:nth-child(1) .name').text(), 'hij1nx')
    eq_(template('.contact:nth-child(2) .name').text(), 'tmpvar')
    eq_(template('.contact:nth-child(3) .name').text(), 'hij1nx')
    eq_(template('.contact:nth-child(4) .name').text(), 'tmpvar')

    eq_(template('.contact:nth-child(1) .title').text(), 'manhattan')
    eq_(template('.contact:nth-child(2) .title').text(), 'brooklyn')
    eq_(template('.contact:nth-child(3) .title').text(), 'manhattan')
    eq_(template('.contact:nth-child(4) .title').text(), 'brooklyn')

    eq_(template('.contact').length, 4)
    eq_(template('.contact .name').length, 4)
    eq_(template('.contact .title').length, 4)

def test_array():
    """Test 7: Create markup from an array of objects that have one dimension"""
    template = get_template('contacts')

    weld(template('.contact')[0], data)

    check_contacts(template)

def test_unmatched_selectors():
    """Test 8: Try to pair data with selectors that yield no matching elements"""
    template = get_template('contacts-none')

    data = (
        dict(x01h='hij1nx', x0x1h='code exploder'),
        dict(name='tmpvar', x0x1h='code wrangler'),
    )

    weld(template('.contact')[0], data)

    ok_('tmpvar' in template('.name:eq(1)').text())
    ok_('Leet Developer' in template('.title:eq(1)').text())

def test_array_of_arrays():
    """Test 9: Create markup from an object literal that has one dimension that contains an array of objects with one dimension"""
    template = get_template('array-of-arrays')

    data = dict(person=(
        dict(name='John', job=('guru', 'monkey', 'tester')),
        dict(name='Bob', job=('supervise', 'yell')),
    ), bar='hello')

    def alternative_map(p, e, k, v):
        template(e).addClass('pre-processed')

    weld(template('.people')[0], data, dict(map=alternative_map))

    eq_(template('.person:nth-child(1) .name').text(), 'John')
    eq_(template('.person:nth-child(1) .job').length, 3)

    eq_(template('.person:nth-child(2) .name').text(), 'Bob')
    eq_(template('.person:nth-child(2) .job').length, 2)

    eq_(template('.person.bar').text(), 'hello')
    eq_(template('.person.bar').length, 1)

    eq_(template('.person.submit').text(), 'Sidecase #2: additional classes (no data equiv)')
    eq_(template('.person.submit').length, 1)

    eq_(template('.pre-processed').length, 8)

def test_form_elements():
    """Test 10: Create markup using form elements as the template"""
    template = get_template('form')

    data = dict(email='tmpvar@gmail.com')

    weld(template('form')[0], data)

    eq_(template(':input[name=email]').val(), data['email'])

def test_false_map():
    """Test 11: Returning false from map stops the current branch from being visited"""

    template = PyQuery('<ul class="list"><li class="item">hello <span class="where">do not touch</span></li></ul>')
    template('#temp').append(template)

    weld(template[0], [
        dict(where='world')
        ], dict(map=lambda p, e, k, v: False))

    eq_(template('.where').text(), 'do not touch')

def test_external():
    """Test 12: Use a NodeList from another template and weld it into the target document"""
    source_template = get_template('source-and-dest #data')
    template = get_template('source-and-dest #dest')

    sources = source_template('span')

    weld(template('li.number')[0], sources)

    eq_(template('li.number').length, 3)
    eq_(template('li.number:nth-child(1) span').text(), 'zero')
    eq_(template('li.number:nth-child(2) span').text(), 'one')
    eq_(template('li.number:nth-child(3) span').text(), 'two')
    eq_(template('li.number').text(), 'zero one two')

def test_internal():
    """Test 13: Use a NodeList from the current document and weld it to another area in the same document"""
    template = get_template('source-and-dest')
    sources = template('#data span')

    weld(template('li.number')[0], sources)

    eq_(template('li.number').length, 3)
    eq_(template('li.number:nth-child(1) span').text(), 'zero')
    eq_(template('li.number:nth-child(2) span').text(), 'one')
    eq_(template('li.number:nth-child(3) span').text(), 'two')
    eq_(template('li.number').text(), 'zero one two')


def test_alias_element():
    """Test 14: Alias may return a dom element which is used instead of doing an explicit match"""
    template = get_template('contacts-alias-opt-out')

    def alternate_name(p, e, k, v):
        eq_(k, 'name')
        return template(e).find('.foo')[0]

    weld(template('.contact')[0], data, dict(
        alias=dict(name=alternate_name)
    ))

    check_contacts(template)

def test_opt_out():
    """Test 15: Alias may opt out of rendering a data-key/element match because of a false value"""
    template = get_template('contacts-opt-out')

    weld(template('.contact')[0], data, dict(alias=dict(name=False)))

    eq_(template('.contact').length, 2)
    eq_(template('.contact:nth-child(1) .foo').text(), 'My Name')
    eq_(template('.contact:nth-child(2) .foo').text(), 'My Name')
