import sys
##sys.path.append('../')  # append parent directory so that import finds pymm
import unittest
import warnings
import pymm
from pymm import Elements as mme
from pymm import MindMap

# FAILING:
# 'show_icon_for_attributes': True is set even when the 'properties' element should have set it to false


class TestReadWriteExample(unittest.TestCase):
    """ Test full import export functionality
    """

    def setUp(self):
        pass

    def test_read_file(self):
        mm = MindMap()
        mm.readfile('../docs/input.mm')
        self.assertTrue(mm)
        self.assertTrue(mm.getroot())
        mm.writefile('input_2.mm')

    def test_write_file(self):
        mm = MindMap()
        mm.writefile('test_write.mm')


class TestElementAccessor(unittest.TestCase):
    '''
        Test Element Accessor
    '''
    def setUp(self):
        self.element = mme.BaseElement()
        self.node = mme.Node()
        self.element.nodes = mme._elementAccess.Children(self.element, ['node'])

    def test_constructor_allows_string(self):
        elem = self.element
        elem.nodes = mme._elementAccess.Children(elem, 'node')

    def test_constructor_fails_on_nonlist_nonstring(self):
        elem = self.element
        empties = [[], (), {}, '']
        for empty in empties:
            self.assertRaises(ValueError, mme._elementAccess.Children, elem, empty)
        others = [{5:6}]
        for other in others:
            self.assertRaises(ValueError, mme._elementAccess.Children, elem, empty)

    def test_alternative_constructor(self):
        elem = self.element
        elem.nodes = mme._elementAccess.Children.preconstructor('node')
        elem.nodes = elem.nodes(elem)  #why doesn't this work?
        self.assertIsInstance(elem.nodes, mme._elementAccess.Children)

    def test_node_is_added_to_element(self):
        elem = self.element
        node = self.node
        elem.nodes.append(node)
        self.assertIn(node, elem.children)
        self.assertIn(node, elem.children[:])
        self.assertIn(node, elem.children[:])
        self.assertIn(node, elem.nodes[:])
        self.assertIn(node, elem.nodes[:])
        self.assertIn(node, elem.nodes)

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
        elem.append(self.node)
        after = len(elem)
        self.assertTrue(before + 1 == after)

    def test_dictionary_returns_correctly_if_attribute_present_or_not(self):
        elem = self.element
        key, value = 'hogwash', 'hogvalue'
        self.assertFalse(key in elem)
        elem.specs[key] = type(value)
        elem[key] = value
        self.assertTrue(key in elem)

    def test_set_bad_attribute_warns_user(self):
        elem = self.element
        self.assertWarns(UserWarning, elem.__setitem__, 'invalid attribute should raise warning', None)

    def test_iterate_attributes_raises_error(self):
        elem = self.element  # allowing user to iterate over attributes implicitly has proven to be a trap; user accidentally iterates
        self.assertRaises(NotImplementedError, elem.__iter__)

    def test_dictionary_raises_error_for_offspec_attribute_assignment(self):
        elem = self.element
        elem.specs['string'] = str
        elem.specs['integer'] = int
        elem.specs['one_or_two'] = [1,2]
        self.assertRaises(ValueError, elem.__setitem__, 'string', 13)
        self.assertRaises(ValueError, elem.__setitem__, 'integer', 'this is not an integer')
        self.assertRaises(ValueError, elem.__setitem__, 'one_or_two', 4)

    def test_dictionary_does_not_raise_error_for_in_spec_attribute_assignment(self):
        elem = self.element
        elem.specs['string'] = str
        elem.specs['integer'] = int
        elem.specs['one_or_two'] = [1,2]
        try:
            elem['string'] = 'good'
            elem['integer'] = 42
            elem['one_or_two'] = 1
        except ValueError:
            self.fail('setting element attribute raised incorrect error')



if __name__ == '__main__':
    unittest.main()
    mm = pymm.MindMap()
    m = mm.getmap()
    converter = pymm.Factories.MindMapConverter()
    tree = converter.revert_mm_element_and_tree(mm.getmap())
    tree.getchildren()  # getchildren IS DEPRECIATED. Which means that... I need a new way to traverse children
    print(len(tree))
