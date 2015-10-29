from __future__ import print_function
import sys
# append parent directory so that import finds pymm
sys.path.append('../')
from uuid import uuid4
import unittest
import inspect
import os
try:
    import pymm
    from pymm import Elements as mme
    from pymm import MindMap
    from pymm._elementAccess import ChildSubset
except ImportError:
    print('Error: I think you are editting file NOT from the test directory')
    print('please cd to test/ and rerun tests.py')
    raise

# pylint: disable=R0904
# pylint: disable=no-self-use


# FAILING: richcontent does not handle itself correctly if html is not set
# (usually if somebody just inits a richcontent node)
# AKA: I have no idea if type variants are used at all in any mindmap
class TestMutableClassVariables(unittest.TestCase):
    """ verify mutable variables are copied / deepcopied in instances. This
    ensures that class variables are not changed when changing an instance's
    variables
    """

    def setUp(self):
        """Gather all the `element` classes into `self.elements`"""
        self.base = pymm.Elements.BaseElement
        # List of the element classes
        self.elements = [self.base, pymm.MindMap]

        def is_element_cls(obj):
            """Checks that x is an object representing a class which inherits
            from BaseElement."""
            return inspect.isclass(obj) and isinstance(obj(), self.base)

        for _, cls in inspect.getmembers(pymm.Elements, is_element_cls):
            self.elements.append(cls)

    def test_for_unique_mut_vars(self, filt=None):
        """ searches for mutable variables within an Element, and verifies it
        gets copied to a new memory address in each element instance.
        """
        is_mutable_var = lambda k, v: (isinstance(v, dict) or
                                       isinstance(v, list))\
                                      and not k.endswith('__')
        base_mutables = [k for k, v in vars(self.base).items()
                         if is_mutable_var(k, v)]
        for elem_class in self.elements:
            mutables = [k for k, v in vars(elem_class).items()
                        if is_mutable_var(k, v)]
            # unique mutables
            mutables = list(set(base_mutables + mutables))
            # optional filter to search only for known attributes
            if filt:
                mutables = [m for m in mutables if m in filt]
            element = elem_class()
            # check if vars have same memory address
            for key in mutables:
                if id(getattr(element, key)) == id(getattr(elem_class, key)):
                    self.fail(str(elem_class) + ' does not copy ' + key)

    def test_specific_nonduplicates(self):
        """ test that children, attrib, _descriptors, and specs are all copied
        to a new list/dict instance in every element when instantiated as an
        instance. This, for example, tests that an instance of MindMap would
        not add children to the MindMap class accidentally, because the class
        attribute children is a different from the instance attribute children.
        """
        filt = ['children', 'attrib', '_descriptors', 'specs']
        self.test_for_unique_mut_vars(filt)


class TestIfRichContentFixedYet(unittest.TestCase):
    """ for now I expect this to fail. idk what to do about it """

    @unittest.expectedFailure
    def test_convert_and_write(self):
        """Test that a RichContent object will convert and write."""
        rich_content = mme.RichContent()
        mind_map = pymm.MindMap()
        mind_map[0].append(rich_content)
        mind_map.write('richcontent_test.mm')


class TestTypeVariants(unittest.TestCase):
    """ test typeVariant attribute of factory to load different objects given
    the same tag. (special attrib values are given that differentiate them)
    """
    def setUp(self):
        # I removed richcontent variants because they do not work correctly
        # when their html is not set. it causes ET to crash
        self.variants = [mme.Hook,
                         mme.EmbeddedImage, mme.MapConfig, mme.Equation,
                         mme.AutomaticEdgeColor]
        self.mind_map = MindMap()
        root = self.mind_map[0]
        # clear out children of root
        root[:] = []
        for variant in self.variants:
            # add a child variant element type
            root.append(variant())
        self.filename = uuid4().hex + '.mm'

        self.mind_map.write(self.filename)
        self.second_mind_map = pymm.read(self.filename)

    def tearDown(self):
        """Clean up the previously created temp files."""
        os.remove(self.filename)

    def test_for_variants(self):
        """Check that the root contains at least one child for each variant
        element type."""
        root = self.second_mind_map[0]
        variants = self.variants.copy()
        for variant in variants:
            for child in root[:]:
                if isinstance(child, variant):
                    break
            # we only reach `else` if no child matched the given variant
            else:
                self.fail('no child of type: ' + str(variant))
            # remove child after it matches a variant
            root.remove(child)


class TestReadWriteExample(unittest.TestCase):
    """ Test full import export functionality """

    def setUp(self):
        pass

    def test_read_file(self):
        """Test the reading and writing of a mind map."""
        # Since this test could be run outside of it's directory, derive the
        # path to the doc file in a more portable way.
        this_path = os.path.dirname(os.path.realpath(__file__))
        mm_path = os.path.join(this_path, '../docs/input.mm')
        mind_map = pymm.read(mm_path)
        self.assertTrue(mind_map)
        self.assertTrue(mind_map.getroot())
        mind_map.write('input_2.mm')
        os.remove('input_2.mm')

    def test_write_file(self):
        """Test the writing of a mind map."""
        mind_map = MindMap()
        # just test that no errors are thrown
        mind_map.write('write_test.mm')
        os.remove('write_test.mm')


class TestNativeChildIndexing(unittest.TestCase):
    """ native child indexing iterates over all children
    using native indexing style [0], or [1:4], etc.
    """

    def setUp(self):
        """Create generic objects for use in tests."""
        self.element = mme.BaseElement()
        self.node = mme.Node()
        self.node2 = mme.Node()

    def test_append_and_index(self):
        """Test successful appending of node to element."""
        elem = self.element
        node = self.node
        elem.append(node)
        self.assertIn(node, elem[:])
        self.assertTrue(node == elem[0])

    def test_slicing(self):
        """Test proper slicing behavior of element."""
        self.element.append(self.node)
        self.element.append(self.node2)
        nodes = self.element[0:2]
        self.assertTrue(self.node in nodes)
        self.assertTrue(self.node2 in nodes)
        # should only get node, not node2
        nodes = self.element[0:2:2]
        self.assertTrue(self.node in nodes)
        self.assertTrue(self.node2 not in nodes)

    def test_remove_and_index(self):
        """Test removal of nodes from element."""
        elem = self.element
        node = self.node
        node2 = self.node2
        elem.append(node)
        elem.append(node2)
        self.assertFalse(node2 == elem[0])
        elem.remove(node)
        self.assertTrue(node2 == elem[0])
        elem.remove(node2)
        # verify elem is child-less
        self.assertFalse(elem[:])

    def test_remove_error(self):
        """Ensure proper error handling for erroneous removal of node from
        element."""
        self.assertRaises(ValueError, self.element.remove, self.node)
        self.element.append(self.node)
        self.assertRaises(ValueError, self.element.remove, self.node2)


class TestElementAccessor(unittest.TestCase):
    """ Test Element Accessor """

    def setUp(self):
        """Create placeholder objects for tests."""
        self.element = mme.BaseElement()
        self.node = mme.Node()
        self.node2 = mme.Node()
        self.cloud = mme.Cloud()
        self.element.nodes = ChildSubset(self.element, tag_regex=r'node')
        self.element.clouds = ChildSubset(self.element, tag_regex=r'cloud')

    def test_add_preconstructed_subset(self):
        """Test that BaseElement properly handles addition of subset."""
        mme.BaseElement.nodes = ChildSubset\
                .class_preconstructor(tag_regex=r'node')
        elem = mme.BaseElement()
        self.assertTrue(hasattr(elem, 'nodes'))
        # be sure to remove this class variable
        del mme.BaseElement.nodes

    def test_attrib_regex(self):
        """Test to ensure proper matching of child elements by regex."""
        self.element.colored = ChildSubset(self.element,
                                           attrib_regex={r'COLOR': '.*'})
        colored = self.element.colored
        node = self.node
        colored.append(node)
        self.assertFalse('COLOR' in node.keys())
        self.assertTrue(len(colored) == 0)
        node['COLOR'] = 'f0f0ff'
        self.assertTrue(len(colored) == 1)
        del node['COLOR']
        self.assertTrue(len(colored) == 0)

    def test_constructor_empty_attrib(self):
        """Test that a child subset cannot be created given an empty regex."""
        elem = self.element
        empties = [[], (), {}, '']
        for empty in empties:
            self.assertRaises(ValueError, ChildSubset, elem, tag_regex=empty)
            self.assertRaises(ValueError, ChildSubset, elem, attrib_regex=empty)
        self.assertRaises(ValueError, ChildSubset,
                          elem, tag_regex='', attrib_regex={})

    def test_constructor_bad_attrib(self):
        """Test that child subset cannot be created with non-regex attribute."""
        self.assertRaises(ValueError, ChildSubset, self.element,
                          attrib_regex=[2, 3])
        self.assertRaises(ValueError, ChildSubset, self.element,
                          tag_regex=r'node', attrib_regex=('sf', 'as'))

    def test_constructor_bad_tag(self):
        """Test that child subset cannot be created with non-regex tag."""
        self.assertRaises(ValueError, ChildSubset, self.element,
                          tag_regex=['node'])
        self.assertRaises(ValueError, ChildSubset, self.element, tag_regex=5,
                          attrib_regex={'TEXT': '.*'})

    def test_alternative_constructor(self):
        """Test alternative child subset constructor."""
        elem = self.element
        elem.nodes = ChildSubset.class_preconstructor(tag_regex=r'node')
        # why doesn't this work? it should just work w/ elem.nodes(). It works
        # ..inside.. the instance, but not outside?
        elem.nodes = elem.nodes(elem)
        self.assertIsInstance(elem.nodes, ChildSubset)

    def test_node_added_element_nodes(self):
        """Test that a node added to elem nodes is properly accessible."""
        elem = self.element
        node = self.node
        elem.nodes.append(node)
        self.assertIn(node, elem.children)
        self.assertIn(node, elem.children[:])
        self.assertIn(node, elem.nodes[:])
        self.assertIn(node, elem.nodes)

    def test_node_is_added_using_append(self):
        """Test node is properly added to element via append method."""
        elem = self.element
        node = self.node
        elem.append(node)
        self.assertIn(node, elem.children)
        self.assertIn(node, elem.children[:])
        self.assertIn(node, elem.nodes[:])
        self.assertIn(node, elem.nodes)

    def test_node_added_to_element(self):
        """Test node is added to element via appending to children."""
        elem = self.element
        node = self.node
        elem.children.append(node)
        self.assertIn(node, elem.children)
        self.assertIn(node, elem.children[:])
        self.assertIn(node, elem.nodes[:])
        self.assertIn(node, elem.nodes)

    def test_element_not_in_nodes(self):
        """Test that an element doesn't show up in a list of nodes."""
        elem = self.element
        node = self.node
        node.append(elem)
        self.assertIn(elem, node.children)
        self.assertIn(elem, node.children[:])
        self.assertFalse(elem in node.nodes[:])
        self.assertFalse(elem in node.nodes)

    def test_nodes_length_post_addition(self):
        """Test that the length of nodes of an element increases after adding a
        node to that element."""
        before = len(self.element.nodes)
        self.element.nodes.append(self.node)
        after = len(self.element.nodes)
        self.assertTrue(before + 1 == after)

    def test_cloud_not_nodes(self):
        """Test that adding a cloud to element doesn't expose cloud in nodes."""
        self.element.children.append(self.cloud)
        self.assertTrue(self.cloud not in self.element.nodes)

class TestBaseElement(unittest.TestCase):
    """Test BaseElement."""
    def setUp(self):
        """Add generic elements for tests."""
        self.element = mme.BaseElement()
        self.node = mme.Node()

    def test_element_length_post_append(self):
        """Test length of element increments after adding node."""
        elem = self.element
        before = len(elem)
        elem.children.append(self.node)
        after = len(elem)
        self.assertTrue(before + 1 == after)

    def test_dictionary_attribut_return(self):
        """Test that dict returns correctly if attribute is or isn't present"""
        elem = self.element
        key, value = 'hogwash', 'hogvalue'
        self.assertFalse(key in elem.keys())
        elem.specs[key] = type(value)
        elem[key] = value
        self.assertTrue(key in elem.keys())

    def test_bad_attr_warning(self):
        """Test that setting a bad attribute raises a user warning."""
        elem = self.element
        self.assertWarns(UserWarning, elem.__setitem__,
                         'invalid attribute should raise warning', None)

    def test_ambiguous_iterate_error(self):
        """ allowing user to iterate over attributes implicitly has proven to
        be a trap; user accidentally iterates """
        self.assertRaises(NotImplementedError, self.element.__iter__)

    def test_ambiguous_contains_error(self):
        """ ambiguous __contains__ for either attribute or children. Therefore
        raise error to force user to specify which membership he is testing for
        """
        self.assertRaises(NotImplementedError,
                          self.element.__contains__, self.node)

    def test_ambiguous_pop_error(self):
        """ ambiguous pop can refer to attribute or children pop(). Therefore
        raise error to force user to be specific """
        self.assertRaises(NotImplementedError, self.element.pop)

    def test_dict_error_offspec_attr(self):
        """Test dictionary will raise error for offspec attribute assignment"""
        elem = self.element
        elem.specs['string'] = str
        elem.specs['integer'] = int
        elem.specs['one_or_two'] = [1, 2]
        self.assertRaises(ValueError, elem.__setitem__, 'string', 13)
        self.assertRaises(ValueError, elem.__setitem__,
                          'integer', 'this is not an integer')
        self.assertRaises(ValueError, elem.__setitem__, 'one_or_two', 5)

    def test_dictionary_inspec_attr(self):
        """Test that dict won't raise error for inspec attribute assignment."""
        elem = self.element
        elem.specs['string'] = str
        elem.specs['integer'] = int
        elem.specs['one_or_two'] = [1, 2]
        try:
            elem['string'] = 'good'
            elem['integer'] = 42
            elem['one_or_two'] = 1
        except ValueError:
            self.fail('setting element attribute raised incorrect error')


if __name__ == '__main__':
    unittest.main()
