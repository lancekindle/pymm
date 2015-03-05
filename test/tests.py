import unittest
from pymm import mindmapElements as mme

class TestElementAccessor(unittest.TestCase):
    '''
        Test Element Accessor
    '''
    def setUp(self):
        self.element = mme.BaseElement()
        self.node = mme.Node()
        self.element.nodes = mme.ElementAccessor(self.element, ['node'])

    def test_constructor_allows_string(self):
        elem = self.element
        elem.nodes = mme.ElementAccessor(elem, 'node')

    def test_constructor_fails_on_nonlist_nonstring(self):
        elem = self.element
        empties = [[], (), {}, '']
        for empty in empties:
            self.assertRaises(ValueError, mme.ElementAccessor(elem, empty), msg='failed on "' + str(empty) + '"')
        others = [{5:6}]
        for other in others:
            self.assertRaises(ValueError, mme.ElementAccessor(elem, empty), msg='failed on "' + str(other) + '"')

    def test_alternative_constructor(self):
        elem = self.element
        elem.nodes = mme.ElementAccessor.constructor('node')
        elem.nodes = elem.nodes()
        self.assertIsInstance(elem.nodes, mme.ElementAccessor)

    def test_node_is_added_to_element(self):
        elem = self.element
        node = self.node
        elem.nodes.append(node)
        self.assertIn(node, elem)
        self.assertIn(node, elem[:])
        self.assertIn(node, elem.nodes)
        self.assertIn(node, elem.nodes[:])

    def test_length_of_elements_change_appropriately(self):
        elem = self.element
        before1, before2 = len(elem.nodes), len(elem)
        node = self.node
        elem.nodes.append(node)
        add1, add2 = len(elem.nodes), len(elem)
        self.assetTrue(add1 == before1 + 1)
        self.assertTrue(add2 == before2 + 1)
        elem.nodes.remove(node)
        after1, after2 = len(elem.nodes), len(elem)
        self.assetTrue(after1 == before1)
        self.assertTrue(after2 == before2)

if __name__ == '__main__':
    unittest.main()