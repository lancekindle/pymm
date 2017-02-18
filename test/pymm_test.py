"""
    This is the testing module for pymm. It tests that import and export
    work correctly, as well as that element features like child subsets
    and node attributes work correctly.
"""
from __future__ import print_function
import sys
# append parent directory so that import finds pymm
sys.path.append('../')
import warnings
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
    raise ImportError('you must run pymm_test from test directory')

# pylint: disable=R0904
# pylint: disable=no-self-use


class TestElementRegistry(unittest.TestCase):
    """Element registry keeps track of all element classes defined
    within the pymm module.
    """

    def test_register_new_class(self):
        """This tests that Elements.registry registers a new element
        class when created (it must inherit from BaseElement). Order of
        elements also matters, so this verifies that newly created test
        class is the last one in the list.
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
        """Order of elements matters. Older elements (as far as when
        they were created) should be first in list, with newer-defined
        classes being at the end of the list. Verify BaseElement is
        first
        """
        factories = pymm.element.registry.get_elements()
        self.assertTrue(pymm.element.BaseElement == factories[0])

    def test_unclaimed_functions(self):
        """when element.registry creates a new element, it correlates
        all the currently @decode and @encode decorated functions into a
        dictionary so that factory can easily create factories that use
        @decode/@encode decorated functions. Decorated fxns should
        always be created within the element's class declaration.
        Therefore each time registry creates an element class, it should
        auto-correlate every decorated function currently unclaimed. If
        some functions are NOT found when creating the element, then we
        throw a RuntimeError.
        """
        @pymm.encode.get_children
        def unclaimed_function():
            pass
        unclaimed_function()  # run it for coverage
        with self.assertRaises(RuntimeError):
            class InnocentElement(pymm.element.BaseElement):
                pass


class TestFactoryRegistry(unittest.TestCase):
    """Factory registry keeps track of all new factories created. Prior
    to encoding/decoding, all factories are noted, and compared with
    elements registry. Any elements that do not have a corresponding
    factory are "unclaimed". Factories are then generated for each
    unclaimed element, in order of oldest to newest unclaimed elements
    """

    def test_factory_exists_for_each_element(self):
        """When calling get_factories(), the existing list of factories
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

    def test_inheritance(self):
        """Verify factory inheritance mimics element inheritance:
                     /= B <= BB
                /= A <============== C
        BaseElement <========== Base
        """
        A = pymm.element.AutomaticEdgeColor
        class B(A):
            pass
        class BB(B):
            pass
        class Base(pymm.element.BaseElement):
            pass
        class C(A):
            pass
        ch = pymm.factory.ConversionHandler()
        a = A()
        b = B()
        bb = BB()
        base = Base()
        c = C()
        f_a = ch.find_encode_factory(a)
        f_b = ch.find_encode_factory(b)
        f_bb = ch.find_encode_factory(bb)
        f_base = ch.find_encode_factory(base)
        f_c = ch.find_encode_factory(c)
        self.assertTrue(issubclass(f_b, f_a))
        self.assertFalse(f_b == f_a)
        self.assertTrue(issubclass(f_bb, f_b))
        self.assertFalse(f_bb == f_b)
        self.assertTrue(issubclass(f_c, f_a))
        self.assertFalse(issubclass(f_c, f_b))


class TestConversionHandler(unittest.TestCase):
    """ConversionHandler is responsible for non-recursively encoding or
    decoding an element and its tree hierarchy (all its children and
    children's children, etc.).
    """

    def setUp(self):
        self.ch = pymm.factory.ConversionHandler()
        class FakeNode0x123(pymm.Node):
            pass
        self.fake_element = FakeNode0x123

    def tearDown(self):
        pymm.element.registry._elements.remove(self.fake_element)

    def test_unknown_element(self):
        """Test that AFTER a ConversionHandler instance is made, a new
        pymm element will still be matched to a factory (specifically
        DefaultFactory) when encoding.
        """
        fake = self.fake_element()
        self.assertTrue(
            self.ch.find_encode_factory(fake) == pymm.factory.DefaultFactory
        )
        factory = self.ch.find_decode_factory(fake)

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
        """verify that decoding a pymm element raises TypeError. Verify
        that encoding a non-pymm element raises TypeError (because you
        decode other -> pymm, and encode pymm -> other
        """
        self.assertRaises(TypeError, pymm.factory.decode, self.fake_element())
        self.assertRaises(TypeError, pymm.factory.encode, pymm.ET.Element('d'))


class TestAttribSpec(unittest.TestCase):
    """Element.spec contains a key/value pair that describes an
    attribute (key) and a list of alloweable values. These allowable
    values can be specific elements (like a 1, or '1') or a class (like
    str or int) or a function that converts the attrib. If an allowable
    value presents a function, then any attribute for that specific key
    is allowed
    """

    def setUp(self):
        self.elements = pymm.element.registry.get_elements()

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
    cloud. Node.text gets/sets Node.attrib['TEXT'], etc. This is to
    verify these different properties work as expected
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
    """Nodes have attributes that are a name, value pair visually stored
    beneath the node in freeplane. They are implemented as a dictionary
    within Node, such that node[key] = value is a valid assignment.
    During reading of a file, "Attribute" Element removes itself from
    the hierarchy and adds itself to the node's implicit attribute
    dictionary. Test that decode and encode correctly removes and adds
    Attribute to hierarchy.
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
        mm = pymm.read(self.filename)
        for key, val in self.attributes.items():
            mm.root[key] = val
        pymm.write(self.filename, mm)
        self.assertTrue(mm.root.items() == self.attributes.items())
        mm = None
        mm = pymm.read(self.filename)
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
        self.elements = pymm.element.registry.get_elements()

    def test_unique_mutable_vars(
            self, filt=None,
            filter_out=[
                'spec', '_display_attrib', 'identifier', 'colors',
            ]):
        """Test each element's mutable variable(s) and confirm it does not
        share the same memory address as the class-wide variables
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
            uses_same_memory_address = [
                key for key in mutables if \
                id(getattr(elem, key)) == id(getattr(elem_class, key))
            ]
            err_msg = str(elem_class) + ' does not copy mutable variables ' + \
                      str(uses_same_memory_address)
            self.assertFalse(uses_same_memory_address, err_msg)

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


class MindmapSetup(unittest.TestCase):
    """provide setUp and tearDown functions for testing Mindmap.
    Also provide shared variables for easier debugging
    """

    def setUp(self):
        self.filename = 'test_context_manager.mm'
        pymm.write(self.filename, pymm.Mindmap())

    def tearDown(self):
        try:
            os.remove(self.filename)
        except FileNotFoundError:
            pass


class TestMindmapFeatures(MindmapSetup):
    """test context manager. Test loading-default hierarchy"""

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


class TestConversionDecoration(unittest.TestCase):
    """test that certain features of @decode/@encode functions work
    as expected
    """

    def test_super(self):
        """verify that super() within a decorated function works:
        calling parent function of element, NOT of factory
        """
        attr = 'x01234'
        value = 'asdf'
        self.assertFalse(hasattr(pymm.element.Node, attr))
        class Fake(pymm.element.Node):
            @pymm.decode.post_decode
            def call_super(self, parent):
                super().tostring()  # just call any function on parent element
                setattr(pymm.element.Node, attr, value)
        self.assertFalse(hasattr(pymm.element.Node, attr))
        mm = pymm.Mindmap()
        self.assertTrue(hasattr(pymm.element.Node, attr))
        self.assertTrue(getattr(pymm.element.Node, attr) == value)
        # cleanup
        delattr(pymm.element.Node, attr)
        self.assertFalse(hasattr(pymm.element.Node, attr))
        class FakeOverride(pymm.element.Node):
            pass


class TestConversionProcess(MindmapSetup):
    """test that the conversion process does not skip elements if an
    element removes itself during the conversion process
    """

    def test_pre_encode_removal(self):
        """create an element that removes itself from the hierarchy
        before encoding. Verify that multiple of these elements in
        a row are removed. This indicates no skipping of elemets.
        """
        class Fake(pymm.element.BaseElement):
            @pymm.encode.pre_encode
            def remove_self(self, parent):
                parent.children.remove(self)

        mm = pymm.read(self.filename)
        mm.root.children = [Fake() for i in range(11)]
        self.assertTrue(mm.root.children)
        pymm.write(self.filename, mm)
        self.assertFalse(mm.root.children)
        # verify written file is affected
        mm = pymm.read(self.filename)
        self.assertFalse(mm.root.children)

    def test_post_encode_removal(self):
        """create an element that removes itself from hierarchy
        after encoding. Verify that multiple of thes elements in a row
        are removed which indicates no skipping of elements.
        Additionally, the encoded mindmap file SHOULD have these
        elements (since they were removed post-encode)
        """
        class Fake(pymm.element.BaseElement):
            @pymm.encode.post_encode
            def remove_self(self, parent):
                parent.children.remove(self)

        mm = pymm.read(self.filename)
        mm.root.children = [Fake() for i in range(11)]
        self.assertTrue(mm.root.children)
        pymm.write(self.filename, mm)
        self.assertFalse(mm.root.children)
        ch = pymm.factory.ConversionHandler()
        factory = ch.find_encode_factory(Fake())
        # verify written file is NOT affected
        mm = pymm.read(self.filename)
        self.assertTrue(mm.root.children)
        for child in mm.root.children:
            self.assertTrue(isinstance(child, Fake))
        pymm.write(self.filename, mm)

    def test_post_decode_removal(self):
        """test that base elements remove themselves from hierarchy
        after decoding. Verify that before self-removing-element is
        created, mindmap looks normal. After self-removing-element is
        created, mindmap should have no children
        """
        self.test_post_encode_removal()  # root.children = [BaseElement(),...]
        mm = pymm.read(self.filename)
        self.assertTrue(mm.root.children)

        class SelfRemover(pymm.element.BaseElement):
            @pymm.decode.post_decode
            def remove_self(self, parent):
                parent.children.remove(self)

        mm = pymm.read(self.filename)
        self.assertFalse(mm.root.children)
        # now test that the nodes can remove themselves if inheriting
        # from a self-destructive Node
        class SelfNodeRemover(pymm.element.Node):
            @pymm.decode.post_decode
            def remove_nodeself(self, parent):
                parent.children.remove(self)

        mm = pymm.read(self.filename)
        self.assertFalse(mm.root)

    def tearDown(self):
        """create a new class that inherits from BaseElement & Node so
        that previous "bad" elements created do not interfere with other
        tests (all elements created are stored in an internal registry.
        Newer elements are used in place of old ones). So this ensures
        that the newer used element does contain destructive encoding /
        decoding behavior
        """
        class SafeBaseElement(pymm.element.BaseElement):
            """create a non-destructive element for pymm to prefer"""
            pass
        class SafeNode(pymm.Node):
            """create a non-destructive Node for pymm to prefer"""
            pass
        super().tearDown()


class TestElementVariants(unittest.TestCase):
    """Elements are generally uniquely identified through their tag,
    such as "node" or "edge". But some tags are used in conjunction
    with attrib to specify the type of element. For example, the tag
    'hook' is used for multiple elements, such as MapConfig, Equation,
    EmbeddedImage, AutomaticeEdgeColor, and Hook. All of which use the
    tag 'hook'. Therefore factories are also built to distinguish which
    element to use based on attrib regex matching. This is built-in to
    the "identifier" property. This tests that these elements are
    correctly identified
    """

    def setUp(self):
        """create variant children. Must be in order from least
        specific to most specific. Hook must come before an element
        that inherits from Hook, for example
        """
        self.variants = [mme.Hook, mme.RichContent, mme.NodeNote, mme.Equation,
                         mme.EmbeddedImage, mme.MapConfig, mme.NodeDetails,
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
        """Check that the root contains one child for each variant
        element type
        """
        root = self.second_mind_map.root
        variants = self.variants.copy()
        for variant in variants:
            child_is_variant = [
                child for child in root.children if isinstance(child, variant)
            ]
            err_msg = 'no child of type: ' + str(variant)
            self.assertTrue(child_is_variant, err_msg)
            child = child_is_variant[0]
            root.children.remove(child)
        self.assertFalse(root.children) # verify no more children


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


class ChildrenSetup(unittest.TestCase):

    def setUp(self):
        """create two nodes and add to self.element.children"""
        self.element = mme.BaseElement()
        self.node = mme.Node()
        self.node2 = mme.Node()
        self.element.children.extend((self.node, self.node2,))


class TestNativeChildIndexing(ChildrenSetup):
    """Native child indexing iterates over all children
    using native indexing style [0], or [1:4], etc.
    """

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


class TestChildSubset(ChildrenSetup):
    """ChildSubset identifies a subset of children on an element
    based on one or more of their tag and/or attrib properties. In
    order to be more flexible, tag_regex or attrib_regex can also
    be used
    """

    def setUp(self):
        """self.element will have childsubsets nodes, clouds."""
        mme.BaseElement.nodes = property(*ChildSubset.setup(tag='node'))
        mme.BaseElement.clouds = property(*ChildSubset.setup(tag='cloud'))
        super().setUp()
        self.cloud = mme.Cloud()
        self.element.children.append(self.cloud)

    def tearDown(self):
        try:
            del mme.BaseElement.nodes
        except:
            pass
        try:
            del mme.BaseElement.clouds
        except:
            pass

    def test_setup_error(self):
        """verify that no identifiers passed to setup raises error.
        Verify that identifiers that do not include one of tag,
        tag_regex, or attrib_regex will raise error. Verify that empty
        identifier values will raise error. Verify that use of two
        conflicting identifiers (tag and tag_regex) raises error
        """
        empty = [
            {'tag': ''}, {'tag_regex': ''}, {'attrib_regex': {}}
        ]
        invalid = [
            {'tagg': 't'}, {'3attrib_regex': {'k': 'v'}}, {'attrib': 'dfs'}
        ]
        incompatible = {'tag': 't', 'tag_regex': 'tr'}
        self.assertRaises(KeyError, ChildSubset.setup, **{})
        self.assertRaises(KeyError, ChildSubset.setup, **incompatible)
        for identifier in empty:
            self.assertRaises(ValueError, ChildSubset.setup, **identifier)
        for identifier in invalid:
            self.assertRaises(KeyError, ChildSubset.setup, **identifier)

    def test_valid_setup(self):
        """verify three arguments (tag, tag_regex, attrib_regex) are
        accepted by setup. Also verify that all other combinations
        aside from tag/tag_regex can be mixed,
        """
        valid = [
            {'tag': 't'}, {'tag_regex': 'r'}, {'attrib_regex': {'k': 'v'}}
        ]
        for identifier in valid:
            ChildSubset.setup(**identifier)
        attrib_identifier = identifier
        ChildSubset.setup(tag='n', **attrib_identifier)
        ChildSubset.setup(tag_regex='n', **attrib_identifier)

    def test_specificity(self):
        """test that ChildSubset only returns matching children"""
        self.assertTrue(self.element.clouds[:] == [self.cloud])
        self.assertTrue(self.element.nodes[:] == [self.node, self.node2])

    def test_property_setup(self):
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

    def test_constructor_bad_attrib(self):
        """Test that child subset cannot be created with non-dictionary
        attribute
        """
        self.assertRaises(ValueError, ChildSubset, self.element,
                          attrib_regex=[2, 3])
        self.assertRaises(ValueError, ChildSubset, self.element,
                          tag_regex=r'node', attrib_regex=('sf', 'as'))

    def test_constructor_bad_tag(self):
        """Test that child subset cannot be created with non-string tag
        """
        self.assertRaises(ValueError, ChildSubset, self.element,
                          tag_regex=['node'])
        self.assertRaises(ValueError, ChildSubset, self.element, tag_regex=5,
                          attrib_regex={'TEXT': '.*'})

    def test_append(self):
        """Test node is properly added to element via append method"""
        elem = self.element
        node = self.node
        elem.nodes.append(node)
        self.assertIn(node, elem.children)
        self.assertIn(node, elem.children[:])
        self.assertIn(node, elem.nodes[:])
        self.assertIn(node, elem.nodes)

    def test_extend(self):
        """test adding multiple nodes via extend works"""
        elem = self.element
        node = self.node
        elements = [node, node]
        num = len(elem.nodes)
        elem.nodes.extend(elements)
        self.assertIn(node, elem.nodes)
        self.assertTrue(len(elem.nodes) == num + 2)

    def test_remove(self):
        """verify remove method on nodes"""
        self.element.nodes.remove(self.node)
        self.assertRaises(ValueError, self.element.nodes.remove, self.node)

    def test_pop(self):
        """verify pop method on nodes"""
        node1 = self.element.nodes.pop()
        node2 = self.element.nodes.pop()
        self.assertRaises(IndexError, self.element.nodes.pop)

    def test_get_set_index(self):
        """verify can replace elements at specific index"""
        nodes = self.element.nodes
        node2 = nodes[1]
        nodes[0] = node2
        self.assertTrue(list(nodes) == [node2, node2])

    def test_slicing(self):
        """verify slicing correctly sets nodes"""
        nodes = self.element.nodes
        node0 = nodes[0]
        node1 = nodes[1]
        self.assertTrue(nodes[:] == [node0, node1])
        self.assertTrue(nodes[:5] == [node0, node1])
        # remove first node
        nodes[:1] = []
        self.assertTrue(nodes == [node1])
        # remove all nodes
        nodes.append(node0)
        nodes[:] = []
        self.assertTrue(nodes == [])
        # add both nodes back
        nodes[:] = [node0, node1]
        self.assertTrue(nodes == [node0, node1])

    def test_delete(self):
        """verify deleting index or slice"""
        nodes = self.element.nodes
        self.assertTrue(len(nodes) == 2)
        del nodes[1:2]
        self.assertTrue(len(nodes) == 1)
        del nodes[3:6]
        self.assertTrue(len(nodes) == 1)
        del nodes[0]
        self.assertTrue(len(nodes) == 0)
        nodes.append(self.node)
        self.assertTrue(len(nodes) == 1)
        del nodes[:]
        self.assertTrue(len(nodes) == 0)

    def test_comparisons(self):
        """test <, >, >=, ==, != comparisons mimic list behavior.
        Comparison only works if elements are in exact order, since
        comparison of Elements is by identity (memory address) only.
        So if the first two elements of children were anything other
        than the first two children in .nodes, this would fail. (as it
        would normally fail if comparing lists of elements)
        """
        nodes = self.element.nodes
        children = self.element.children
        self.assertTrue(nodes < children)
        self.assertTrue(nodes <= children)
        self.assertFalse(nodes > children)
        self.assertFalse(nodes >= children)
        self.assertFalse(nodes == children)
        self.assertTrue(nodes == list(nodes))
        self.assertTrue(nodes == nodes)
        self.assertTrue(nodes != children)
        self.assertFalse(nodes != list(nodes))

    def test_comparisons_error(self):
        """test <, >, >=, ==, != raise error if compared to dict"""
        nodes = self.element.nodes
        children = self.element.children
        for operator in ['<', '<=', '>', '>=', '==', '!=']:
            with self.assertRaises(TypeError):
                eval('nodes ' + operator + ' {}')

    def test_set_list(self):
        """set nodes to an empty list, verify it correctly removes all
        nodes
        """
        elem = self.element
        nodes = len(elem.nodes)
        children = len(elem.children)
        self.assertTrue(nodes > 0)
        elem.nodes = []
        self.assertTrue(len(elem.nodes) == 0)
        self.assertTrue(len(elem.children) == children - nodes)

    def test_nonmatching_element(self):
        """Test that a non-node doesn't show up in a list of nodes"""
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
        self.assertTrue(self.cloud in self.element.clouds)


class TestSingleChild(ChildrenSetup):
    """Test Element Accessor"""

    def setUp(self):
        """self.element will have singlechild property: firstchild
        which will grab first node in children list
        """
        mme.BaseElement.firstchild = property(
            *SingleChild.setup(tag='node')
        )
        super().setUp()
        self.cloud = mme.Cloud()
        self.element.children.append(self.cloud)

    def tearDown(self):
        del mme.BaseElement.firstchild

    def test_setup_error(self):
        """verify KeyError is raised if no regexes are passed into
        SingleChild.setup
        """
        self.assertRaises(KeyError, SingleChild.setup)

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
        """verify that icon's .icon property correctly sets icon in
        attrib. Verify out-of-spec icon generates warning when encoding
        """
        icon = pymm.element.Icon()
        icon.icon = 'yes'
        self.assertTrue(icon.attrib['BUILTIN'] == 'yes')
        # verify icon 'yes' does NOT generate warning
        warnings.filterwarnings('error')
        with warnings.catch_warnings():
            pymm.factory.encode(icon)
        # verify icon '0x123BAD' does create warning
        icon.icon = '0x123BAD'
        self.assertWarns(Warning, pymm.factory.encode, icon)


class TestBaseElement(ChildrenSetup):
    """Test BaseElement functions"""

    def setUp(self):
        """Add generic elements for tests"""
        super().setUp()
        cloud = mme.Cloud()
        self.element.children.append(cloud)

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

    def test_findall(self):
        """test that findall always returns a list, and correctly
        matches elements
        """
        matching = self.element.findall(tag='nonexistant')
        self.assertTrue(matching == [])
        nodes = [e for e in self.element.children if isinstance(e, mme.Node)]
        matching = self.element.findall(tag='node')
        self.assertTrue(nodes == matching)
        clouds = self.element.findall(attrib_regex={'COLOR': '.*'})
        self.assertTrue(clouds)
        self.assertTrue(isinstance(clouds[0], mme.Cloud))

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
        assignment, but will raise warning when attempting to encode
        """
        elem = self.element
        elem.spec['string'] = [str]
        elem.spec['integer'] = [int]
        elem.spec['one_or_two'] = [1, 2]
        elem.attrib['string'] = 'good'
        elem.attrib['integer'] = 42
        elem.attrib['one_or_two'] = 1
        warnings.filterwarnings('error')  # throw warning as exception
        with warnings.catch_warnings():
            pymm.factory.encode(elem)
        elem.attrib['integer'] = 'X'
        self.assertWarns(Warning, pymm.factory.encode, elem)


if __name__ == '__main__':
    unittest.main()
    #mm = pymm.Mindmap('../docs/input.mm')
