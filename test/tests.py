import sys
sys.path.append('../')  # append parent directory so that import finds pymm
import unittest
import warnings
from uuid import uuid4
import xml
try:
    import pymm
    from pymm import Elements as mme
    from pymm import MindMap
    from pymm._elementAccess import ChildSubset
except ImportError:
    print('Error: I think you are editting file NOT from the test directory')
    print('please cd to test/ and rerun tests.py')
    raise

# FAILING: richcontent does not handle itself correctly if html is not set
# (usually if somebody just inits a richcontent node)
# AKA: I have no idea if type variants are used at all in any mindmap

class TestNodeImplicitAttributes(unittest.TestCase):

    def setUp(self):
        self.attributes = {'requires': 'maintenance', 'serial#': 'XJ3V2'}
        self.n = mme.Node()
        for k, v in self.attributes.items():
            self.n[k] = v

    def test_iter_raises_exception(self):
        self.assertRaises(NotImplementedError, iter, self.n)

    def test_items(self):
        self.assertTrue(self.n.items() == self.attributes.items())

    def test_setitem(self):
        val = 'a new value'
        for key, _ in self.n.items():
            break
        self.n[key] = val
        self.assertTrue((key, val) in self.n.items())

    def test_getitem(self):
        for key, value in self.n.items():
            self.assertTrue(self.n[key] == value)

    def test_delitem(self):
        for key, value in self.n.items():
            break
        del self.n[key]
        self.assertFalse((key, value) in self.n.items())


class TestMutableClassVariables(unittest.TestCase):
    """ verify mutable variables are copied / deepcopied in instances. This
    ensures that class variables are not changed when changing an instance's
    variables
    """

    def setUp(self):
        self.base = pymm.Elements.BaseElement
        self.elements = [self.base, pymm.MindMap]  #list of all elements 
            # inheriting from BaseElement
        for v in vars(pymm.Elements).values():  # iterate module, find classes
            try:
                if type(v) == type(self.base) and isinstance(v(), self.base):
                    self.elements.children.append(v)
            except:
                continue

    def test_for_nonduplicate_mutable_variables_in_elements(self, filter=None):
        """ searches for mutable variables within an Element, and verifies it
        gets copied to a new memory address in each element instance.
        """
        is_mutable_var = lambda k, v: (isinstance(v, dict) or 
                                isinstance(v, list)) and not k.endswith('__')
        baseMutables = [k for k, v in vars(self.base).items() 
                        if is_mutable_var(k, v)]
        for elemClass in self.elements:
            mutables = [k for k, v in vars(elemClass).items()
                        if is_mutable_var(k, v)]
            mutables = list(set(baseMutables + mutables))  # unique mutables
            if filter:  # optional filter to search only for known attributes
                mutables = [m for m in mutables if m in filter]
            elemObj = elemClass()
            for key in mutables:  # check if vars have same memory address
                if id(getattr(elemObj, key)) == id(getattr(elemClass, key)):
                    self.fail(str(elemClass) + ' does not copy ' + key)
        
    def test_for_specific_nonduplicate_mutable_variables(self):
        """ test that children, attrib, _descriptors, and specs are all copied
        to a new list/dict instance in every element when instantiated as an
        instance. This, for example, tests that an instance of MindMap would
        not add children to the MindMap class accidentally, because the class
        attribute children is a different from the instance attribute children.
        """
        filter = ['children', 'attrib', '_descriptors', 'specs']
        self.test_for_nonduplicate_mutable_variables_in_elements(filter)


class TestIfRichContentFixedYet(unittest.TestCase):
    """ for now I expect this to fail. idk what to do about it """

    @unittest.expectedFailure
    def test_richcontent_converts_and_writes_to_file(self):
        rc = mme.RichContent()
        mm = pymm.MindMap()
        mm.getroot().children.append(rc)
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
        root = self.mm.getroot()
        root.children.clear()
        for variant in self.variants:
            root.children.append(variant())  # add a child variant element type
        self.filename = uuid4().hex + '.mm'
        self.mm.write(self.filename)  # need to remember to erase file later...
        self.mm2 = pymm.read(self.filename)

    def test_for_variants(self):
        """ check that each of the variants is a child in root node """
        root = self.mm2.getroot()
        variants = self.variants.copy()
        for variant in variants:
            for child in root.children:
                if isinstance(child, variant):
                    break
            else:  # we only reach else: if no child matched the given variant
                self.fail('no child of type: ' + str(variant)) 
            root.children.remove(child)  # remove child after it matches a variant


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


class TestChildIndexing(unittest.TestCase):

    def setUp(self):
        self.element = mme.BaseElement()
        self.node = mme.Node()
        self.node2 = mme.Node()

    def test_append_and_index(self):
        elem = self.element
        node = self.node
        elem.children.append(node)
        self.assertIn(node, elem.children)
        self.assertTrue(node == elem.children[0])

    def test_slicing(self):
        self.element.children.append(self.node)
        self.element.children.append(self.node2)
        nodes = self.element.children[0:2]
        self.assertTrue(self.node in nodes)
        self.assertTrue(self.node2 in nodes)
        nodes = self.element.children[0:2:2]  # should only get node, not node2
        self.assertTrue(self.node in nodes)
        self.assertTrue(self.node2 not in nodes)

    def test_remove_and_index(self):
        elem = self.element
        node = self.node
        node2 = self.node2
        elem.children.append(node)
        elem.children.append(node2)
        self.assertFalse(node2 == elem.children[0])
        elem.children.remove(node)
        self.assertTrue(node2 == elem.children[0])
        elem.children.remove(node2)
        self.assertFalse(elem.children)  # verify elem is child-less

    def test_remove_error(self):
        self.assertRaises(ValueError, self.element.children.remove, self.node)
        self.element.children.append(self.node)
        self.assertRaises(ValueError, self.element.children.remove, self.node2)


class TestElementAccessor(unittest.TestCase):
    """ Test Element Accessor """

    def setUp(self):
        self.element = mme.BaseElement()
        self.node = mme.Node()
        self.node2 = mme.Node()
        self.cloud = mme.Cloud()
        self.element.nodes = ChildSubset(self.element, tag_regex=r'node')
        self.element.clouds =ChildSubset(self.element, tag_regex=r'cloud')

    def test_add_preconstructed_subset_to_element_class(self):
        mme.BaseElement.nodes = ChildSubset.class_preconstructor(tag_regex=r'node')
        e = mme.BaseElement()
        self.assertTrue(hasattr(e, 'nodes'))
        del mme.BaseElement.nodes  # be sure to remove this class variable

    def test_attrib_regex(self):
        self.element.colored = ChildSubset(self.element, attrib_regex={r'COLOR': '.*'})
        colored = self.element.colored
        node = self.node
        colored.append(node)
        self.assertFalse('COLOR' in node.attrib.keys())
        self.assertTrue(len(colored) == 0)
        node.attrib['COLOR'] = 'f0f0ff'
        self.assertTrue(len(colored) == 1)
        del node.attrib['COLOR']
        self.assertTrue(len(colored) == 0)

    def test_constructor_fails_on_empty_regex(self):
        elem = self.element
        empties = [[], (), {}, '']
        for empty in empties:
            self.assertRaises(ValueError, ChildSubset, elem, tag_regex=empty)
            self.assertRaises(ValueError, ChildSubset, elem, attrib_regex=empty)
        self.assertRaises(ValueError, ChildSubset, elem, tag_regex='', attrib_regex={})

    def test_constructor_fails_on_wrong_attrib_format(self):
        self.assertRaises(ValueError, ChildSubset, self.element,
                attrib_regex=[2,3])
        self.assertRaises(ValueError, ChildSubset, self.element,
                tag_regex=r'node', attrib_regex=('sf', 'as'))

    def test_constructor_fails_on_wrong_tag_format(self):
        self.assertRaises(ValueError, ChildSubset, self.element,
                tag_regex=['node'])
        self.assertRaises(ValueError, ChildSubset, self.element, tag_regex=5,
                attrib_regex={'TEXT': '.*'})

    def test_alternative_constructor(self):
        elem = self.element
        elem.nodes = ChildSubset.class_preconstructor(tag_regex=r'node')
        elem.nodes = elem.nodes(elem)  # why doesn't this work? it should just work w/ elem.nodes(). It works ..inside.. the instance, but not outside?
        self.assertIsInstance(elem.nodes, ChildSubset)

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
        elem.children.append(node)
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
        node.children.append(elem)
        self.assertIn(elem, node.children)
        self.assertIn(elem, node.children[:])
        self.assertFalse(elem in node.nodes[:])
        self.assertFalse(elem in node.nodes)

    def test_length_of_nodes_increases_after_adding_node(self):
        before = len(self.element.nodes)
        self.element.nodes.append(self.node)
        after = len(self.element.nodes)
        self.assertTrue(before + 1 == after)

    def test_nonmatching_cloud_is_not_in_nodes(self):
        self.element.children.append(self.cloud)
        self.assertTrue(self.cloud not in self.element.nodes)

class TestBaseElement(unittest.TestCase):
    def setUp(self):
        self.element = mme.BaseElement()
        self.node = mme.Node()

    def test_length_of_element_changes_after_adding_node(self):
        elem = self.element
        before = len(elem.children)
        elem.children.append(self.node)
        after = len(elem.children)
        self.assertTrue(before + 1 == after)

    def test_dictionary_returns_correctly_if_attribute_present_or_not(self):
        elem = self.element
        key, value = 'hogwash', 'hogvalue'
        self.assertFalse(key in elem.attrib.keys())
        elem.specs[key] = type(value)
        elem.attrib[key] = value
        self.assertTrue(key in elem.attrib.keys())

    # need to rewrite to test that warnings are raised only during sanity_check()
    @unittest.expectedFailure
    def test_set_bad_attribute_warns_user(self):
        elem = self.element
        self.assertWarns(UserWarning, elem.attrib.__setitem__, 'invalid attribute should raise warning', None)

    # need to rewrite to test that warnings are raised only during sanity_check()
    @unittest.expectedFailure
    def test_dictionary_raises_error_for_offspec_attribute_assignment(self):
        elem = self.element
        elem.specs['string'] = str
        elem.specs['integer'] = int
        elem.specs['one_or_two'] = [1, 2]
        self.assertRaises(ValueError, elem.attrib.__setitem__, 'string', 13)
        self.assertRaises(ValueError, elem.attrib.__setitem__, 'integer', 'this is not an integer')
        self.assertRaises(ValueError, elem.attrib.__setitem__, 'one_or_two', 5)

    # need to rewrite to test that warnings are raised only during sanity_check()
    def test_dictionary_does_not_raise_error_for_in_spec_attribute_assignment(self):
        elem = self.element
        elem.specs['string'] = str
        elem.specs['integer'] = int
        elem.specs['one_or_two'] = [1, 2]
        try:
            elem.attrib['string'] = 'good'
            elem.attrib['integer'] = 42
            elem.attrib['one_or_two'] = 1
        except ValueError:
            self.fail('setting element attribute raised incorrect error')


if __name__ == '__main__':
    unittest.main()  # comment this out to run the code below
    mm = pymm.MindMap()
    m = mm.getmap()
    converter = pymm.Factories.MindMapConverter()
    tree = converter.revert_mm_element_and_tree(mm.getmap())
    tree.getchildren()  # getchildren IS DEPRECIATED. Which means that... I need a new way to traverse children
