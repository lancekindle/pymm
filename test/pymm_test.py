"""
    This is the testing module for pymm. It tests that import and export work
    correctly, as well as that element features like child subsets and node
    attributes work correctly.
"""
from __future__ import print_function
import sys
# append parent directory so that import finds pymm
sys.path.append('../')
from uuid import uuid4
import unittest
import inspect
import os
import collections
try:
    import pymm
    from pymm import element as mme
    from pymm import Mindmap
    from pymm.access import ChildSubset, SingleChild
except ImportError:
    print('Error: I think you are editting file NOT from the test directory')
    print('please cd to test/ and rerun tests.py')
    raise

# pylint: disable=R0904
# pylint: disable=no-self-use


# FAILING: richcontent does not handle itself correctly if html is not set
# (usually if somebody just inits a richcontent node)
# AKA: I have no idea if type variants are used at all in any mindmap


def append_elements_to_list(children_list, *children):
    """given a children list and 1+ children, append children in the order
    given to the children list. Note children_list is not an element. It is the
    element's .children or .nodes, etc attribute
    """
    for child in children:
        children_list.append(child)


def is_pymm_element_class(cls):
    """Checks that cls is an object representing a class which inherits
    from BaseElement
    """
    return inspect.isclass(cls) and issubclass(cls, pymm.element.BaseElement)


def get_all_pymm_element_classes(*namespaces):
    """Return list of pymm elements. Search pymm and pymm.Elements namespaces
    for any elements inheriting from BaseElement, including BaseElement. Any
    namespaces/modules passed as an argument to this function will also be
    searched, and any elements found will be including in returned list.
    """
    modules = [pymm, pymm.element] + list(namespaces)
    elements = set()
    for module in modules:
        for _, cls in inspect.getmembers(module, is_pymm_element_class):
            elements.add(cls)
    return list(elements)



class TestElementRegistry(unittest.TestCase):
    """Element registry keeps track of all element classes defined
    within the pymm module.
    """

    def test_register_new_class(self):
        """This tests that Elements.registry registers a new
        element class when created (it must inherit from BaseElement).
        Order of elements also matters, so this verifies that newly
        created test class is the last one in the list.
        """
        before = pymm.element.registry.get_elements()
        class TestElementClass0x123(pymm.element.BaseElement):
            pass
        test_class = TestElementClass0x123
        after = pymm.element.registry.get_elements()
        self.assertTrue(test_class not in before)
        self.assertTrue(test_class in after)
        self.assertTrue(test_class == after[-1])

    def test_elements_order(self):
        """order of elements matters. Older elements (as far as when
        they were created) should be first in list, with newer-defined
        classes being at the end of the list. Verify BaseElement is first
        """
        factories = pymm.element.registry.get_elements()
        self.assertTrue(pymm.element.BaseElement == factories[0])


class TestFactoryRegistry(unittest.TestCase):
    """Factory registry keeps track of all new factories created. Prior
    to encoding/decoding, all factories are noted, and compared with
    elements registry. Any elements that do not have a corresponding
    factory are "unclaimed". Factories are then generated for each
    unclaimed element, in order of oldest to newest unclaimed elements
    """

    def test_factory_exists_for_each_element(self):
        """when calling get_factories(), the existing list of factories
        are returned PLUS a generated list of factories for unclaimed
        elements. The factories are generated in the order that the
        unclaimed factories were created
        """
        elements = pymm.element.registry.get_elements()
        factories = pymm.factory.registry.get_factories()
        for elem in elements:
            decoding_elements = (f.decoding_element for f in factories)
            self.assertIn(
                elem, decoding_elements, 'no factory for element: ' + str(elem)
            )

    def test_register_new_factory(self):
        """verify that new factory created is registered last in
        list of non-generated factories
        """
        class TestFactory0x123(pymm.factory.DefaultFactory):
            pass
        test_class = TestFactory0x123
        self.assertTrue(test_class == pymm.factory.registry._factories[-1])
        del pymm.factory.registry._factories[-1]

    def test_factories_order(self):
        """test that oldest factory is first in list"""
        factories = pymm.factory.registry.get_factories()
        self.assertTrue(pymm.factory.DefaultFactory == factories[0])


class TestConversionHandler(unittest.TestCase):
    """ConversionHandler is responsible for non-recursively encoding or
    decoding an element and its tree hierarchy (all its children and
    children's children, etc.).
    """

    def setUp(self):
        self.ch = pymm.factory.ConversionHandler()
        class FakeNode0x123(pymm.element.Node):
            pass
        self.fake_element = FakeNode0x123

    def tearDown(self):
        pymm.element.registry._elements.remove(self.fake_element)

    def test_unknown_element(self):
        """test that AFTER a ConversionHandler instance is made,
        a new pymm element will still be matched to a factory
        (specifically DefaultFactory) when encoding.
        Verify that during decoding, new pymm element will be matched
        to factory for inherited class.
        """
        fake = self.fake_element()
        self.assertTrue(
            self.ch.find_encode_factory(fake) == pymm.factory.DefaultFactory
        )
        factory = self.ch.find_decode_factory(fake)
        self.assertTrue(isinstance(fake, factory.decoding_element))
        node_factory = self.ch.find_decode_factory(pymm.Node())
        self.assertTrue(factory == node_factory)

    def test_convert_keyword(self):
        """test that any convert keyword not "encode" or "decode" raises
        ValueError
        """
        fake = self.fake_element()
        self.ch.convert_element_hierarchy(fake, 'encode')
        self.ch.convert_element_hierarchy(pymm.ET.Element('d'), 'decode')
        self.assertRaises(
            ValueError, self.ch.convert_element_hierarchy, fake, 'debug'
        )

    def test_wrong_element_conversion(self):
        """verify that decoding a pymm element raises TypeError.
        Verify that encoding a non-pymm element raises TypeError
        (because you decode other -> pymm, and encode pymm -> other
        """
        self.assertRaises(TypeError, pymm.factory.decode, self.fake_element())
        self.assertRaises(TypeError, pymm.factory.encode, pymm.ET.Element('d'))


class TestAttribSpec(unittest.TestCase):
    """Element.spec contains a key/value pair that describes an attribute
    (key) and a list of alloweable values. These allowable values can be
    specific elements (like a 1, or '1') or a class (like str, int) or a
    function that converts the attrib. If an allowable value presents a
    function, then any attribute for that specific key is allowed
    """

    def setUp(self):
        self.elements = get_all_pymm_element_classes(pymm)

    def test_spec_values_are_lists(self):
        """Each element has a spec dictionary. For each key/value pair,
        verify that the value is a list
        """
        for elem in self.elements:
            for val in elem.spec.values():
                self.assertTrue(
                    isinstance(val, list),
                    str(elem) + ' has non-list spec value: ' + str(val)
                )

    def test_spec_keys_are_strings(self):
        """Each element has a spec dictionary. For each key/value pair,
        verify that the key is a string
        """
        for elem in self.elements:
            for key in elem.spec.keys():
                self.assertTrue(
                    isinstance(key, str),
                    str(elem) + ' has non-str spec key: ' + str(key)
                )

#TODO: add test for node.note, node.cloud
class TestNodeProperties(unittest.TestCase):
    """Node has a large number of properties that act as a quick
    shortcut to attrib or children. For example, Node.cloud gets/sets a
    cloud. Node.text gets/sets Node.attrib['TEXT'], etc.
    This is to verify these different properties work as expected
    """

    def setUp(self):
        self.node = pymm.element.Node()

    def test_text(self):
        """test node.text sets node.attrib['TEXT']"""
        text = 'abc123'
        default = ''
        node = self.node
        self.assertTrue(node.text == default)
        node.attrib['TEXT'] = text
        self.assertTrue(node.text == text)
        del node.text
        self.assertTrue(node.text == default)

    def test_link(self):
        """test node.link sets node.attrib['LINK']. However, if
        node.link is set to another node, instead it copies the 'ID'
        attrib from linked node. If it does not exist, or is deleted,
        return or set the link to None
        """
        url = 'http://github.com/lancekindle'
        default = None
        node = self.node
        self.assertTrue(node.link == default)
        node.link = url
        self.assertTrue(node.attrib['LINK'] == url)
        node2 = pymm.element.Node()
        node.link = node2
        link_id = node2.attrib['ID']
        self.assertTrue(node.attrib['LINK'] == link_id)
        del node.link
        self.assertTrue(node.link == default)


class TestNodeImplicitAttributes(unittest.TestCase):
    """Nodes have attributes that are a name, value pair visually
    stored beneath the node in freeplane. They are implemented as a
    dictionary within Node, such that node[key] = value is a valid
    assignment. During reading of a file, "Attribute" Element removes
    itself from the hierarchy and adds itself to the node's implicit
    attribute dictionary. Test that decode and encode correctly removes
    and adds Attribute to hierarchy.
    """

    def setUp(self):
        self.attributes = {'requires': 'maintenance', 'serial#': 'XJ3V2'}
        self.filename = 'test_attributes.mm'
        self.node = mme.Node()
        for key, val in self.attributes.items():
            self.node[key] = val

    def test_items(self):
        """Test that attribute.items() matches node's attribute.items()"""
        self.assertTrue(self.node.items() == self.attributes.items())

    def test_setitem(self):
        """Test implicit setitem of node sets node's attribute item"""
        val = 'a new value'
        for key, _ in self.node.items():
            self.node[key] = val
            self.assertTrue((key, val) in self.node.items())
            break

    def test_getitem(self):
        """Test Node implicit getitem returns correct attribute values"""
        for key, value in self.node.items():
            self.assertTrue(self.node[key] == value)

    def test_delitem(self):
        """Test node implicit delitem deletes correct attribute"""
        count = len(self.node.items())
        for key, value in self.node.items():
            del self.node[key]
            self.assertFalse((key, value) in self.node.items())
            self.assertTrue(count - 1 == len(self.node.items()))
            break

    def test_iter(self):
        """Test that attributes can be iterated from node"""
        for attr in self.node:
            self.assertIn(attr, self.attributes)

    def test_contains(self):
        """Test that attributes can be checked if IN node"""
        for attr in self.attributes:
            self.assertTrue(attr in self.node)

    def test_getattributes(self):
        """test get_attributes returns node attributes dict
        Verify the two attributes match, but are different dicts
        """
        self.assertEqual(self.attributes, self.node.get_attributes())
        self.assertIsNot(self.attributes, self.node.get_attributes())

    def test_encode_decode(self):
        """verify that attribute saves to file, and is loaded
        back into node
        """
        with pymm.Mindmap(self.filename, 'w') as mm:
            for key, val in self.attributes.items():
                mm.root[key] = val
        self.assertTrue(mm.root.items() == self.attributes.items())
        mm = None
        mm = pymm.Mindmap(self.filename)
        self.assertTrue(mm.root.items() == self.attributes.items())


class TestMutableClassVariables(unittest.TestCase):
    """BaseElement and some inheriting elements define some mutable
    variables in their class definition (such as children). This is
    done for clarity as to what data-structure the user should expect.
    However, this presents the danger that an instance of BaseElement
    may share the same "children" list with its instances. Were this
    the case, appending a child to one element would also append a
    child to the class itself and to all other instances that share the
    same "children" variable. Test that mutable variables are not
    shared by verifying that a class's instance holds different mutable
    variables than the class itself. Specifically, verify that all
    dicts and lists defined in BaseElement and any inheriting class
    does not share that dict/list with its instances, with a few
    exceptions (noteably spec and _display_attrib)
    """

    def setUp(self):
        """Gather all the `element` classes into `self.elements`"""
        self.base = pymm.element.BaseElement
        self.elements = get_all_pymm_element_classes()

    def test_unique_mutable_vars(
            self, filt=None,
            filter_out=[
                'spec', '_display_attrib', 'identifier', 'color_rotation'
            ]):
        """Test each element's mutable variable and confirm it does not
        share the same memory address as the element's Class
        """
        is_mutable = lambda k, v: (isinstance(v, dict) or
                                   isinstance(v, list)) and \
                                   not k.endswith('__')
        base_mutables = [k for k, v in vars(self.base).items()
                         if is_mutable(k, v)]
        for elem_class in self.elements:
            mutables = [k for k, v in vars(elem_class).items()
                        if is_mutable(k, v)]
            mutables = list(set(base_mutables + mutables))

            # optional filter to search only for known attributes
            if filt:
                mutables = [m for m in mutables if m in filt]
            # optional filter to remove known attributes (they are OK to share)
            if filter_out:
                mutables = [m for m in mutables if m not in filter_out]
            elem = elem_class()

            # check if vars have same memory address
            for key in mutables:
                if id(getattr(elem, key)) == id(getattr(elem_class, key)):
                    self.fail(str(elem_class) + ' does not copy ' + key)

    def test_specific_nonduplicates(self):
        """test that children, attrib, _display_attrib, and spec are
        all copied to a new list/dict instance in every element when
        instantiated as an instance. This, for example, tests that an
        instance of Mindmap would not add children to the Mindmap class
        accidentally, because the class attribute children is a
        different from the instance attribute children.
        """
        filt = ['children', 'attrib',]
        self.test_unique_mutable_vars(filt)


class TestIfRichContentFixedYet(unittest.TestCase):
    """ for now I expect this to fail. idk what to do about it """

    @unittest.expectedFailure
    def test_convert_and_write(self):
        """Test that a RichContent object will convert and write"""
        rich_content = mme.RichContent()
        mind_map = pymm.Mindmap()
        mind_map.nodes[0].children.append(rich_content)
        pymm.write('richcontent_test.mm', mind_map)


class MindmapSetup(unittest.TestCase):
    """provide setUp and tearDown functions for testing Mindmap.
    Also provide shared variables for easier debugging
    """

    def setUp(self):
        self.filename = 'test_context_manager.mm'
        self.text = 'testing 123'

    def tearDown(self):
        try:
            os.remove(self.filename)
        except FileNotFoundError:
            pass


class TestMindmapFeatures(MindmapSetup):
    """test context manager. Test loading-default hierarchy"""

    def test_max_arg_error(self):
        """verify that arguments in excess of 2 (filename and mode) to
        mindmap result in an error
        """
        self.assertRaises(ValueError, pymm.Mindmap, self.filename, 'r', 'r')

    def test_mode_error(self):
        """verify that a mode of both read and write raises error.
        Also verify that any mode aside from 'r' or 'w' raises error
        """
        self.assertRaises(ValueError, pymm.Mindmap, self.filename, 'rw')
        for mode in 'abcdefghijklmnopqstuvxyz':  # missing r and w
            self.assertRaises(ValueError, pymm.Mindmap, self.filename, mode)

    def test_loads_default_hierarchy(self):
        """test that default hierarchy loads correctly.
        Should load one Mindmap with one one root node, (with text
        "new_mindmap") and several children. If Mindmap loads default
        hierarchy each time it is instantiated, python will enter a
        recursive loop that will end in error
        """
        mm = pymm.Mindmap()
        self.assertTrue(mm.children != [])
        self.assertTrue(mm.root is not None)
        self.assertTrue(mm.root.text == "new_mindmap")

    def test_context_manager_write(self):
        """verify that mindmap context manager writes to file"""
        with pymm.Mindmap(self.filename, 'w') as mm:
            mm.root.text = self.text
        self.assertTrue(os.path.exists(self.filename))

    def test_read_error(self):
        """Verify that attempting to read from a non-existant file
        raises a FileNotFoundError
        """
        self.assertRaises(FileNotFoundError, pymm.Mindmap, self.filename, 'r')
        self.assertRaises(FileNotFoundError, pymm.Mindmap, self.filename)

    def test_context_manager_read(self):
        """context manager should be able to read a file"""
        with pymm.Mindmap(self.filename, 'w') as mm:
            mm.root.text = self.text
        with pymm.Mindmap(self.filename, 'r') as mm:
            self.assertTrue(mm.root.text == self.text)

    def test_context_manager_abort(self):
        """Test that context manager writes to file even if an error
        occurs. Also verify that context-manager does not handle error,
        instead allowing error to propagate
        """
        mm = None
        self.assertFalse(os.path.exists(self.filename))
        with self.assertRaises(TypeError):
            with pymm.Mindmap(self.filename, 'w') as mm:
                mm.root.text = self.text
                mm.root.children.append(3, 3)  # triggers TypeError
        self.assertTrue(os.path.exists(self.filename))
        self.assertTrue(mm is not None)
        with pymm.Mindmap(self.filename) as mm:
            self.assertTrue(mm.root.text == self.text)


class TestPymmModuleFeatures(MindmapSetup):
    """Test various top-level features within the pymm module such as
    read, write, encode, decode
    """

    def test_write_file(self):
        """Test that a "blank" mindmap can be written to file"""
        pymm.write(self.filename, pymm.Mindmap())
        self.assertTrue(os.path.exists(self.filename))

    def test_write_args_error(self):
        """verify that an 2nd argument must be pymm element"""
        self.assertRaises(ValueError, pymm.write, self.filename, [])

    def test_encode_args_error(self):
        """verify that 2nd arg must be a pymm element"""
        self.assertRaises(ValueError, pymm.encode, [])


class TestFileLocked(MindmapSetup):
    """file_locked is a special function-like class to handle marking a
    file as "locked" when being read. It is only used by pymm.decode
    and pymm.Mindmap to ensure that Mindmap does not recursively load
    its default hierarchy
    """

    def test_lock_context(self):
        """verify file stays "locked" only as long as within context
        """
        self.assertFalse(pymm.file_locked(self.filename))
        with pymm.file_locked(self.filename) as file_lock:
            self.assertTrue(file_lock)
            self.assertTrue(pymm.file_locked(self.filename))
        self.assertFalse(pymm.file_locked(self.filename))

    def test_no_locked_files(self):
        """verify no files are currently locked"""
        for filename, status in pymm.file_locked.locked.items():
            self.assertFalse(status, str(filename) + ' marked as locked')

    def test_lock_boolean(self):
        """file_locked can also act a boolean, returning true or false
        if a file is locked or not.
        """
        self.assertFalse(pymm.file_locked(self.filename))
        mm = pymm.Mindmap(self.filename, 'w')
        self.assertFalse(pymm.file_locked(self.filename))


class TestTypeVariants(unittest.TestCase):
    """test typeVariant attribute of factory to load different objects
    given the same tag. (special attrib values are given that
    differentiate them)
    """

    def setUp(self):
        # I removed richcontent variants because they do not work correctly
        # when their html is not set. it causes ET to crash
        self.variants = [mme.Hook,
                         mme.EmbeddedImage, mme.MapConfig, mme.Equation,
                         mme.AutomaticEdgeColor]
        self.mind_map = Mindmap()
        root = self.mind_map.root
        # clear out children of root
        root.children = []
        for variant in self.variants:
            # add a child variant element type
            root.children.append(variant())
        self.filename = uuid4().hex + '.mm'

        pymm.write(self.filename, self.mind_map)
        self.second_mind_map = pymm.read(self.filename)

    def tearDown(self):
        """Clean up the previously created temp files"""
        os.remove(self.filename)

    def test_for_variants(self):
        """Check that the root contains at least one child for each
        variant element type
        """
        root = self.second_mind_map.root
        variants = self.variants.copy()
        child = None
        for variant in variants:
            for child in root.children:
                if isinstance(child, variant):
                    break
            # we only reach `else` if no child matched the given variant
            else:
                self.fail('no child of type: ' + str(variant))
            # remove child after it matches a variant
            root.children.remove(child)


class TestReadWriteExample(unittest.TestCase):
    """Test full import and export functionality"""

    def setUp(self):
        self.filename = 'export_test_0x123'

    def tearDown(self):
        os.remove(self.filename)

    def test_read_and_write_file(self):
        """Test the reading and writing of a mind map. Also (important)
        verify that order and number of factories used is same (or
        nearly so)
        """
        # Since this test could be run outside of it's directory, derive the
        # path to the doc file in a more portable way.
        this_path = os.path.dirname(os.path.realpath(__file__))
        mm_path = os.path.join(this_path, '../docs/input.mm')
        mind_map = pymm.read(mm_path)
        self.assertTrue(mind_map)
        self.assertTrue(mind_map.root)
        pymm.write(self.filename, mind_map)
        self.verify_conversion_traces_match()

    def verify_conversion_traces_match(self):
        """pymm.factory.ConversionHandler contains a trace of factory
        classes used in the last encode and decode operation. Call this
        after reading and then writing to file without modification.
        The two traces should be very similar or else something is
        wrong with a factory. Since dynamically-generated factories are
        part of both traces, the easiest way to compare is with
        factory.decoding_element (which is the pymm element)

        In the past, these have mismatched when an element modifies the
        tree prior to encoding. For example, AutomaticEdgeColor colored
        one previously un-colored child of root (which is good, but
        since it added an Edge child to a node, the encode/decode count
        was off by one). To prevent this error from showing up, I
        modified the mindmap to include the missing colored-edge.
        """
        encode_trace = pymm.factory.ConversionHandler.last_encode
        decode_trace = pymm.factory.ConversionHandler.last_decode
        encoded = (factory.decoding_element for factory in encode_trace)
        decoded = (factory.decoding_element for factory in decode_trace)
        encode_count = collections.Counter(encoded)
        decode_count = collections.Counter(decoded)
        self.assertTrue(encode_count == decode_count)

    def test_write_file(self):
        """Test the writing of a mind map"""
        mind_map = Mindmap()
        # just test that no errors are thrown
        pymm.write(self.filename, mind_map)


class TestNativeChildIndexing(unittest.TestCase):
    """Native child indexing iterates over all children
    using native indexing style [0], or [1:4], etc.
    """

    def setUp(self):
        """Create generic objects for use in tests"""
        self.element = mme.BaseElement()
        self.node = mme.Node()
        self.node2 = mme.Node()
        append_elements_to_list(self.element.children, self.node, self.node2)

    def test_append_and_index(self):
        """Test successful appending of node to element"""
        self.element.children.clear()
        self.element.children.append(self.node)
        self.assertIn(self.node, self.element.children)
        self.assertTrue(self.node == self.element.children[0])

    def test_slicing(self):
        """Test proper slicing of children"""
        nodes = self.element.children[0:2]
        self.assertTrue(self.node in nodes)
        self.assertTrue(self.node2 in nodes)
        # should only get node, not node2
        nodes = self.element.children[0:2:2]
        self.assertTrue(len(nodes) == 1)
        self.assertTrue(self.node in nodes)
        self.assertTrue(self.node2 not in nodes)

    def test_remove_and_index(self):
        """Test removal of nodes from element"""
        self.assertFalse(self.node2 == self.element.children[0])
        self.element.children.remove(self.node)
        self.assertTrue(self.node2 == self.element.children[0])
        self.element.children.remove(self.node2)
        # verify elem is child-less
        self.assertFalse(self.element.children)  # verify elem is child-less

    def test_remove_error(self):
        """Ensure proper error handling for erroneous removal of node from
        element
        """
        self.element.children.clear()
        self.assertRaises(ValueError, self.element.children.remove, self.node)
        self.element.children.append(self.node)
        self.assertRaises(ValueError, self.element.children.remove, self.node2)


class TestChildSubset(unittest.TestCase):

    def setUp(self):
        """self.element will have childsubsets nodes, clouds."""
        self.element = mme.BaseElement()
        self.node = mme.Node()
        self.node2 = mme.Node()
        self.cloud = mme.Cloud()
        self.element.nodes = ChildSubset(self.element, tag=r'node')
        self.element.clouds = ChildSubset(self.element, tag_regex=r'cloud')
        append_elements_to_list(
            self.element.children, self.node, self.node2, self.cloud
        )

    def test_specificity(self):
        """test that ChildSubset only returns matching children"""
        self.assertTrue(self.element.clouds[:] == [self.cloud])
        self.assertTrue(self.element.nodes[:] == [self.node, self.node2])

    def test_setup(self):
        """Test that ChildSubset.setup can be applied to existing
        element classes
        """
        mme.BaseElement.nodes = property(*ChildSubset.setup(tag='node'))
        elem = mme.BaseElement()
        self.assertTrue(hasattr(elem, 'nodes'))
        self.assertTrue(elem.nodes[:] == [])
        del mme.BaseElement.nodes  # cleanup
        self.assertFalse(hasattr(elem, 'nodes'))

    def test_attrib_regex(self):
        """Test to ensure proper matching of child elements by regex"""
        self.element.colored = ChildSubset(self.element,
                                           attrib_regex={r'COLOR': '.*'})
        colored = self.element.colored
        node = self.node
        self.assertFalse('COLOR' in node.attrib.keys())
        colored_count = len(colored)
        node.attrib['COLOR'] = 'f0f0ff'
        self.assertTrue(len(colored) == colored_count + 1)
        del node.attrib['COLOR']
        self.assertTrue(len(colored) == colored_count)

    def test_constructor_empty_attrib(self):
        """Test that a child subset cannot be created given an empty
        regex
        """
        elem = self.element
        empties = [[], (), {}, '']
        for empty in empties:
            self.assertRaises(ValueError, ChildSubset, elem, tag_regex=empty)
            self.assertRaises(ValueError, ChildSubset, elem, attrib_regex=empty)
        self.assertRaises(ValueError, ChildSubset,
                          elem, tag_regex='', attrib_regex={})

    def test_constructor_bad_attrib(self):
        """Test that child subset cannot be created with non-regex
        attribute
        """
        self.assertRaises(ValueError, ChildSubset, self.element,
                          attrib_regex=[2, 3])
        self.assertRaises(ValueError, ChildSubset, self.element,
                          tag_regex=r'node', attrib_regex=('sf', 'as'))

    def test_constructor_bad_tag(self):
        """Test that child subset cannot be created with non-regex tag
        """
        self.assertRaises(ValueError, ChildSubset, self.element,
                          tag_regex=['node'])
        self.assertRaises(ValueError, ChildSubset, self.element, tag_regex=5,
                          attrib_regex={'TEXT': '.*'})

    def test_node_added_element_nodes(self):
        """Test that a node added to elem nodes is properly accessible
        """
        elem = self.element
        node = self.node
        elem.nodes.append(node)
        self.assertIn(node, elem.children)
        self.assertIn(node, elem.children[:])
        self.assertIn(node, elem.nodes[:])
        self.assertIn(node, elem.nodes)

    def test_node_is_added_using_append(self):
        """Test node is properly added to element via append method"""
        elem = self.element
        node = self.node
        elem.children.append(node)
        self.assertIn(node, elem.children)
        self.assertIn(node, elem.children[:])
        self.assertIn(node, elem.nodes[:])
        self.assertIn(node, elem.nodes)

    def test_node_added_to_element(self):
        """Test node is added to element via appending to children"""
        elem = self.element
        node = self.node
        elem.children.append(node)
        self.assertIn(node, elem.children)
        self.assertIn(node, elem.children[:])
        self.assertIn(node, elem.nodes[:])
        self.assertIn(node, elem.nodes)

    def test_element_not_in_nodes(self):
        """Test that an element doesn't show up in a list of nodes"""
        elem = self.element
        node = self.node
        node.children.append(elem)
        self.assertIn(elem, node.children)
        self.assertIn(elem, node.children[:])
        self.assertFalse(elem in node.nodes[:])
        self.assertFalse(elem in node.nodes)

    def test_nodes_length_post_addition(self):
        """Test that the length of nodes of an element increases after
        adding a node to that element.
        """
        before = len(self.element.nodes)
        self.element.nodes.append(self.node)
        after = len(self.element.nodes)
        self.assertTrue(before + 1 == after)

    def test_cloud_not_nodes(self):
        """Test that adding a cloud to element doesn't expose cloud in
        nodes
        """
        self.element.children.append(self.cloud)
        self.assertTrue(self.cloud not in self.element.nodes)


class TestSingleChild(unittest.TestCase):
    """Test Element Accessor"""

    def setUp(self):
        """self.element will have singlechild property: firstchild
        which will grab first node in children list
        """
        mme.BaseElement.firstchild = property(
            *SingleChild.setup(tag_regex=r'node')
        )
        self.element = mme.BaseElement()
        self.node = mme.Node()
        self.node2 = mme.Node()
        self.cloud = mme.Cloud()
        append_elements_to_list(
            self.element.children, self.node, self.node2, self.cloud
        )

    def tearDown(self):
        del mme.BaseElement.firstchild

    def test_setup_error(self):
        """verify ValueError is raised if no regexes are passed into
        SingleChild.setup
        """
        self.assertRaises(ValueError, SingleChild.setup)

    def test_singlechild_when_empty(self):
        """test that None is returned when no matches are found.
        Verify that setting child when children list is empty works
        """
        self.element.children.clear()
        self.assertTrue(self.element.firstchild is None)
        self.element.firstchild = self.node

    def test_return_first_match(self):
        """test that first matching child is returned"""
        self.assertTrue(self.element.firstchild is self.node)

    def test_delete_first_match(self):
        """test that first matching child is deleted"""
        self.assertTrue(self.element.firstchild is self.node)
        del self.element.firstchild
        self.assertTrue(self.element.firstchild is self.node2)
        del self.element.firstchild
        self.assertTrue(self.element.firstchild is None)

    def test_replace_first_match(self):
        """test that setting to another node replaces first matching
        child
        """
        self.element.firstchild = self.node2
        self.assertTrue(self.element.children[:2] == [self.node2, self.node2])

    def test_set_to_none(self):
        """test that setting to None deletes first matching child"""
        self.assertTrue(len(self.element.children) == 3)
        self.element.firstchild = None
        self.assertTrue(len(self.element.children) == 2)
        self.assertTrue(self.element.firstchild == self.node2)

    def test_setup(self):
        """test that SingleChild.setup can be applied to an existing
        element class
        """
        mme.BaseElement.rootx = property(*SingleChild.setup(tag_regex=r'node'))
        elem = mme.BaseElement()
        self.assertTrue(hasattr(elem, 'rootx'))
        self.assertTrue(elem.rootx is None)
        del mme.BaseElement.rootx  # cleanup
        self.assertFalse(hasattr(elem, 'rootx'))


class TestIconElement(unittest.TestCase):
    """test Icon-specific features"""

    def test_set_icon(self):
        """verify that set_icon set's correct attrib and that warning
        is generated for out-of-spec icon
        """
        icon = pymm.element.Icon()
        icon.set_icon('yes')
        self.assertTrue(icon.attrib['BUILTIN'] == 'yes')
        self.assertWarns(SyntaxWarning, icon.set_icon, '0x123BAD')


class TestBaseElement(unittest.TestCase):
    """Test BaseElement functions"""

    def setUp(self):
        """Add generic elements for tests"""
        self.element = mme.BaseElement()
        self.node = mme.Node()

    def test_element_to_string(self):
        """test that str(element) returns string representation,
        including any _display_attrib
        """
        string = '0x103'
        self.node.text = string
        self.assertIn(string, str(self.node))
        self.element._display_attrib.append('A')
        self.element.attrib['xA'] = 'xC'
        self.element.attrib['A'] = 'B'
        self.assertIn('B', str(self.element))
        self.assertIn('A', str(self.element))
        self.assertNotIn('xA', str(self.element))
        self.assertNotIn('xC', str(self.element))
        self.element._display_attrib.remove('A')  # cleanup

    def test_element_repr(self):
        """verify that a small portion of string is used in making
        representation (repr) of element
        """
        self.node.text = '3433'
        string = str(self.node)[:8]
        self.assertIn(string, repr(self.node))
        string = str(self.element)[:8]
        self.assertIn(string, repr(self.element))

    def test_element_length_post_append(self):
        """Test length of element increments after adding node"""
        elem = self.element
        before = len(elem.children)
        elem.children.append(self.node)
        after = len(elem.children)
        self.assertTrue(before + 1 == after)

    def test_out_of_spec_attrib_allowed(self):
        """Test that attrib dict handles as a dict regardless of spec"""
        elem = self.element
        key, value = 'hogwash', 'hogvalue'
        self.assertFalse(key in elem.attrib.keys())
        elem.spec[key] = [type(value)]
        elem.attrib[key] = value
        self.assertTrue(key in elem.attrib.keys())

    def test_dictionary_inspec_attr(self):
        """Test that dict won't raise error for inspec attribute
        assignment
        """
        elem = self.element
        elem.spec['string'] = [str]
        elem.spec['integer'] = [int]
        elem.spec['one_or_two'] = [1, 2]
        elem.attrib['string'] = 'good'
        elem.attrib['integer'] = 42
        elem.attrib['one_or_two'] = 1
        try:
            pymm.factory.sanity_check(elem)
        except Warning:
            self.fail('in-spec attributes raised warning')
        elem.attrib['string'] = 5
        self.assertWarns(Warning, pymm.factory.sanity_check, elem)


if __name__ == '__main__':
    unittest.main()
    #mm = pymm.Mindmap('../docs/input.mm')
