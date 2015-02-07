import xml.etree.ElementTree as ET
import Factories
from collections import namedtuple
from Factories import RemoveElementAndChildrenFromTree
from copy import deepcopy


class FreeplaneFile(object):

    def __init__(self):
        self.xmlTree = ET.ElementTree()
        self.mmtc = MindMapTreeConverter()

    def readfile(self, filename):
        self.xmlTree.parse(filename)
        self._convert(self.xmlTree)

    def writefile(self, filename):
        self._revert(self.mapnode)
        self.xmlTree.write('output.mm')

    def getroot(self):
        #return self.mapnode[0]  # map has one child -> the root  # NOT TRUE! #there can be an attribute_registry here
        return self.mapnode.findall('node')[0]

    def getmap(self):
        return self.mapnode
    
    def _convert(self, xmlTree):
        etMapNode = xmlTree.getroot()
        self.mapnode = self.mmtc.convert_etree_element_and_tree(etMapNode)

    def _revert(self, mapNode):
        #mapF = MapFactory()
        etMapNode = self.mmtc.revert_node_and_tree(self.mapnode)
        #etMapNode = mapF.to_etree_element(self.mapnode)
        # need to convert mapNode too!
        self.xmlTree._root = etMapNode


class MindMapTreeConverter(object):
    # pass this factory a node to convert
    # and it will convert by choosing which factory to use in converting a given node
    # it is also tasked with non-recursively converting all nodes contained
    # within the first converted node.

    def __init__(self, **kwargs):
        F = Factories
        factories = [F.BaseElementFactory, F.NodeFactory, F.MapFactory, F.CloudFactory,
                     F.HookFactory, F.MapStylesFactory, F.StyleNodeFactory, F.FontFactory, F.IconFactory,
                     F.EdgeFactory, F.AttributeFactory, F.PropertiesFactory, F.RichContentFactory,
                     F.AttributeRegistryFactory]
        fff = [factory() for factory in factories]  # get an initialized instance of all factories
        self.tag2factory = {}
        for f in fff:            # get a dictionary that
            self.add_factory(f)  # matches an elements tag to the factory which can handle that element
        self.defaultFactory = F.BaseElementFactory()
        del F  # remove reference. We can still always use Factories
        pass

    def add_factory(self, factory):
        if not isinstance(factory, object):  # if we are passed a non-initialized factory, create factory instance
            factory = factory()
        element = factory.elementType()
        self.tag2factory[element.tag] = factory

    def _special_vert_full_tree(self, element, action1, action2):
        # element can be pymm element or etree element
        # e = from (the node / element being converted)
        # convert or revert the element!
        cap = namedtuple('ChildAndParent', ['child','parent'])
        first = action1(element, None)
        hasUnchangedChildren = [first]
        while hasUnchangedChildren:
            element = hasUnchangedChildren.pop(0)
            unchanged = [cap(child, element) for child in element[:]]
            children = []
            while unchanged:
                unchangedChild, parent = unchanged.pop(0)  # pop from first index to preserve child order
                try:
                    child = action1(unchangedChild, parent)
                except RemoveElementAndChildrenFromTree:
                    continue  # removes element from tree being built by not adding it to children(s) list
                children.append(child)
                hasUnchangedChildren.append(child)
            element[:] = children
        notFullyChanged = [cap(first, None)]
        while notFullyChanged:
            element, parent = notFullyChanged.pop(0)
            try:
                element = action2(element, parent)
            except RemoveElementAndChildrenFromTree:
                parent.remove(element)
                continue
            parentsAndChildren = [cap(child, element) for child in element[:]]
            notFullyChanged.extend(parentsAndChildren)
        return first

    def convert_etree_element_and_tree(self, et):
        et = deepcopy(et)
        action1 = self.convert_etree_element
        action2 = self.additional_conversion
        node = self._special_vert_full_tree(et, action1, action2)
        self.defaultFactory.display_any_warnings()  # get this out so the developer is warned.
        return node
    
    def convert_etree_element(self, et, parent):
        ff = self.get_conversion_factory_for(et)
        node = ff.convert_from_etree_element(et, parent)
        return node

    def additional_conversion(self, et, parent):
        ff = self.get_conversion_factory_for(et)
        return ff.additional_conversion(et, parent)

    def get_conversion_factory_for(self, et):
        tag = None
        tag = et.tag
        if tag and tag in self.tag2factory:
            return self.tag2factory[tag]
        return self.defaultFactory

    def revert_node_and_tree(self, node):
        node = deepcopy(node)
        action1 = self.revert_node
        action2 = self.additional_reversion
        return self._special_vert_full_tree(node, action1, action2)

    def revert_node(self, node, parent):
        ff = self.get_conversion_factory_for(node)
        return ff.revert_to_etree_element(node, parent)

    def additional_reversion(self, node, parent):
        ff = self.get_conversion_factory_for(node)
        return ff.additional_reversion(node, parent)
    
if __name__ == '__main__':
    fpf = FreeplaneFile()
    fpf.readfile('input.mm')
    element = fpf.xmlTree.getroot().findall('node')[0]
    m = fpf.getmap()  # map node
    n = fpf.getroot()  # root node
    try:
        fpf.writefile('output.mm')
    except:
        raise
    finally:
        e = fpf.xmlTree._root  # the ET root
    #print(ET.tostring(e[1][-2]))
