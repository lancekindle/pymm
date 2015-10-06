import sys
sys.path.append('../')  # append parent directory so that import finds pymm
import unittest
import warnings
from uuid import uuid4
import pymm
import xml
from pymm import Elements as mme
from pymm import MindMap

# FAILING: richcontent does not handle itself correctly if html is not set
# (usually if somebody just inits a richcontent node)
# AKA: I have no idea if type variants are used at all in any mindmap

class TestMutableClassVariables(unittest.TestCase):
    """ verify mutable variables are copied / deepcopied in instances. This
    ensures that class variables are not changed when changing an instance's
    variables
    """

    def setUp(self):
        self.base = pymm.Elements.BaseElement
        self.elements = []
        for v in vars(pymm.Elements).values():  # iterate module, find classes
            try:
                if type(v) == type(self.base) and isinstance(v(), self.base):
                    self.elements.append(v)
            except:
                continue

    # so far this catches several variables I'm not concerned about, but which
    # probably should be copied nonetheless. What should I do about it?
    # until I do something, this test will fail
    def test_for_nonduplicate_mutable_variables_in_elements(self):
        is_mutable = lambda x: isinstance(x, dict) or isinstance(x, list)
        baseMutables = [k for k, v in vars(self.base).items() if is_mutable(v)]
        for elemClass in self.elements:
            mutables = [k for k, v in vars(elemClass).items() if is_mutable(v)]
            mutables = list(set(baseMutables + mutables))  # unique mutables
            elemObj = elemClass()
            for key in mutables:  # check if vars have same memory address
                if id(getattr(elemObj, key)) == id(getattr(elemClass, key)):
                    self.fail(str(elemClass) + ' does not copy ' + key)
        

class TestElementChildrenAreDifferentBetweenInstances(unittest.TestCase):
    """ mindmap inherits from map, but I had forgotten to super().__init__ it
    so that when I added a child, it added it class-wide. Now I should check
    all elements to verify that children list is different for 2 instances of
    the same element
    """

    def test_mindmap(self):
        mindmaps = []
        for i in range(2):
            mindmaps.append(pymm.MindMap())
        self.assertFalse(mindmaps[0].children == mindmaps[1].children)

    # I need to test all elements if possible (and I'm not yet...)


class TestIfRichContentFixedYet(unittest.TestCase):
    """ for now I expect this to fail. idk what to do about it """

    @unittest.skip('richcontent fails because it is not fixed')
    def test_richcontent_converts_and_writes_to_file(self):
        rc = mme.RichContent()
        mm = pymm.MindMap()
        mm[0].append(rc)
        mm.write('richcontent_test.mm')


class TestTypeVariants(unittest.TestCase):
    """ test typeVariant attribute of factory to load different objects given
    the same tag. (special attrib values are given that differentiate them)
    """
    def setUp(self):
        self.variants = [mme.Hook,  # I removed richcontent variants because
# they do not work correctly when their html is not set. it causes ET to crash
                mme.EmbeddedImage, mme.MapConfig, mme.Equation,
                mme.AutomaticEdgeColor]
        self.mm = MindMap()
        root = self.mm[0]
        root[:] = []  # clear out children of root
        for variant in self.variants:
            root.append(variant())  # add a child variant element type
        self.filename = uuid4().hex + '.mm'
        self.mm.write(self.filename)  # need to remember to erase file later...
        self.mm2 = pymm.read(self.filename)

    def test_for_variants(self):
        """ check that each of the variants is a child in root node """
        root = self.mm2[0]
        variants = self.variants.copy()
        for variant in variants:
            for child in root[:]:
                if isinstance(child, variant):
                    break
            else:  # we only reach else: if no child matched the given variant
                self.fail('no child of type: ' + str(variant)) 
            root.remove(child)  # remove child after it matches a variant


class TestReadWriteExample(unittest.TestCase):
    """ Test full import export functionality """

    def setUp(self):
        pass

    def test_read_file(self):
        mm = pymm.read('../docs/input.mm')
        self.assertTrue(mm)
        self.assertTrue(mm.getroot())
        mm.write('input_2.mm')

    def test_write_file(self):
        mm = MindMap()
        mm.write('write_test.mm')  # just test that no errors are thrown


class TestNativeChildIndexing(unittest.TestCase):
    """ native child indexing iterates over all children
    using native indexing style [0], or [1:4], etc.
    """

    def setUp(self):
        self.element = mme.BaseElement()
        self.node = mme.Node()
        self.node2 = mme.Node()

    def test_append_and_index(self):
        elem = self.element
        node = self.node
        elem.append(node)
        self.assertIn(node, elem[:])
        self.assertTrue(node == elem[0])

    def test_slicing(self):
        self.element.append(self.node)
        self.element.append(self.node2)
        nodes = self.element[0:2]
        self.assertTrue(self.node in nodes)
        self.assertTrue(self.node2 in nodes)
        nodes = self.element[0:2:2]  # should only get node, not node2
        self.assertTrue(self.node in nodes)
        self.assertTrue(self.node2 not in nodes)

    def test_remove_and_index(self):
        elem = self.element
        node = self.node
        node2 = self.node2
        elem.append(node)
        elem.append(node2)
        self.assertFalse(node2 == elem[0])
        elem.remove(node)
        self.assertTrue(node2 == elem[0])
        elem.remove(node2)
        self.assertFalse(elem[:])  # verify elem is child-less

    def test_remove_error(self):
        self.assertRaises(ValueError, self.element.remove, self.node)
        self.element.append(self.node)
        self.assertRaises(ValueError, self.element.remove, self.node2)


class TestElementAccessor(unittest.TestCase):
    """ Test Element Accessor """

    def setUp(self):
        self.element = mme.BaseElement()
        self.node = mme.Node()
        self.node2 = mme.Node()
        self.element.nodes = mme._elementAccess.Children(self.element, ['node'])

    def test_constructor_allows_string(self):
        elem = self.element
        elem.nodes = mme._elementAccess.Children(elem, 'node')

    def test_constructor_fails_on_nonlist_nonstring(self):
        elem = self.element
        empties = [[], (), {}, '']
        for empty in empties:
            self.assertRaises(ValueError, mme._elementAccess.Children, elem, empty)
        others = [{5: 6}]
        for other in others:
            self.assertRaises(ValueError, mme._elementAccess.Children, elem, empty)

    def test_alternative_constructor(self):
        elem = self.element
        elem.nodes = mme._elementAccess.Children.preconstructor('node')
        elem.nodes = elem.nodes(
            elem)  # why doesn't this work? it should just work w/ elem.nodes(). It works ..inside.. the instance, but not outside?
        self.assertIsInstance(elem.nodes, mme._elementAccess.Children)

    def test_node_is_added_to_element_nodes(self):
        elem = self.element
        node = self.node
        elem.nodes.append(node)
        self.assertIn(node, elem.children)
        self.assertIn(node, elem.children[:])
        self.assertIn(node, elem.nodes[:])
        self.assertIn(node, elem.nodes)

    def test_node_is_added_using_append(self):
        elem = self.element
        node = self.node
        elem.append(node)
        self.assertIn(node, elem.children)
        self.assertIn(node, elem.children[:])
        self.assertIn(node, elem.nodes[:])
        self.assertIn(node, elem.nodes)

    def test_node_is_added_to_element(self):
        elem = self.element
        node = self.node
        elem.children.append(node)
        self.assertIn(node, elem.children)
        self.assertIn(node, elem.children[:])
        self.assertIn(node, elem.nodes[:])
        self.assertIn(node, elem.nodes)

    def test_element_is_not_in_list_of_nodes(self):
        elem = self.element
        node = self.node
        node.append(elem)
        self.assertIn(elem, node.children)
        self.assertIn(elem, node.children[:])
        self.assertFalse(elem in node.nodes[:])
        self.assertFalse(elem in node.nodes)

    def test_length_of_nodes_increases_after_adding_node(self):
        before = len(self.element.nodes)
        self.element.nodes.append(self.node)
        after = len(self.element.nodes)
        self.assertTrue(before + 1 == after)


class TestBaseElement(unittest.TestCase):
    def setUp(self):
        self.element = mme.BaseElement()
        self.node = mme.Node()

    def test_length_of_element_changes_after_adding_node(self):
        elem = self.element
        before = len(elem)
        elem.children.append(self.node)
        after = len(elem)
        self.assertTrue(before + 1 == after)

    def test_dictionary_returns_correctly_if_attribute_present_or_not(self):
        elem = self.element
        key, value = 'hogwash', 'hogvalue'
        self.assertFalse(key in elem.keys())
        elem.specs[key] = type(value)
        elem[key] = value
        self.assertTrue(key in elem.keys())

    def test_set_bad_attribute_warns_user(self):
        elem = self.element
        self.assertWarns(UserWarning, elem.__setitem__, 'invalid attribute should raise warning', None)

    def test_ambiguous_iterate_attributes_raises_error(self):
        """ allowing user to iterate over attributes implicitly has proven to be a trap; user accidentally iterates """
        self.assertRaises(NotImplementedError, self.element.__iter__)

    def test_ambiguous_implicit_contains_call_raises_error(self):
        """ ambiguous __contains__ for either attribute or children. Therefore raise error to
        force user to specify which membership he is testing for
        """
        self.assertRaises(NotImplementedError, self.element.__contains__, self.node)

    def test_ambiguous_pop_call_raises_error(self):
        """ ambiguous pop can refer to attribute or children pop(). Therefore raise error to force user to be specific
        """
        self.assertRaises(NotImplementedError, self.element.pop)

    def test_dictionary_raises_error_for_offspec_attribute_assignment(self):
        elem = self.element
        elem.specs['string'] = str
        elem.specs['integer'] = int
        elem.specs['one_or_two'] = [1, 2]
        self.assertRaises(ValueError, elem.__setitem__, 'string', 13)
        self.assertRaises(ValueError, elem.__setitem__, 'integer', 'this is not an integer')
        self.assertRaises(ValueError, elem.__setitem__, 'one_or_two', 5)

    def test_dictionary_does_not_raise_error_for_in_spec_attribute_assignment(self):
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
    unittest.main()  # comment this out to run the code below
    mm = pymm.MindMap()
    m = mm.getmap()
    converter = pymm.Factories.MindMapConverter()
    tree = converter.revert_mm_element_and_tree(mm.getmap())
    tree.getchildren()  # getchildren IS DEPRECIATED. Which means that... I need a new way to traverse children
    print(len(tree))
