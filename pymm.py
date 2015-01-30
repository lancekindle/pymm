import xml.etree.ElementTree as ET
import Factories

# to do: generic conversion for all children. Instead of housing "clouds, etc" in separate lists
# house all children of node in same _children list. But when iterating through children, only
# return the nodes. Then calls to getclouds() can instead iterate through all children, picking
# out any that have the tag "cloud" This way it's more similar to xml. Also, instead
# set type to be the actual nodetype. for example, RootNode will have tag "node" but type RootNode

# setting node attributes should be done by BaseElement, not BaseElementfactory! simply initalize the
# BaseElement with the attributes from the element

class FreeplaneFile(object):

    def __init__(self):
        self.xmlTree = ET.ElementTree()
        self.mmc = MindMapConverter()

    def readfile(self, filename):
        self.xmlTree.parse(filename)
        self._convert(self.xmlTree)

    def writefile(self, filename):
        self._revert(self.mapnode)
        self.xmlTree.write('output.mm')

    def getroot(self):
        return self.mapnode[0]  # map has one child -> the root

    def getmap(self):
        return self.mapnode
    
    def _convert(self, xmlTree):
        etMapNode = xmlTree.getroot()
        self.mapnode = self.mmc.convert_etree_element_and_tree(etMapNode)

    def _revert(self, mapNode):
        #mapF = MapFactory()
        etMapNode = self.mmc.revert_node_and_tree(self.mapnode)
        #etMapNode = mapF.to_etree_element(self.mapnode)
        # need to convert mapNode too!
        self.xmlTree._root = etMapNode


class MindMapConverter(object):
    # this factory will just take a list of nodes to convert
    # and will convert by choosing which factory to use in converting a given node
    # it is also tasked with non-recursively converting all nodes contained
    # within the first converted node.

    def __init__(self, **kwargs):
        F = Factories
        factories = [F.BaseElementFactory, F.NodeFactory, F.MapFactory, F.CloudFactory,
                     F.HookFactory, F.MapStylesFactory, F.StyleNodeFactory, F.FontFactory, F.IconFactory,
                     F.EdgeFactory, F.AttributeFactory, F.PropertiesFactory]
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
        self.tag2factory[element.gettag()] = factory

    def convert_etree_element_and_tree(self, et):
        action1 = self.convert_etree_element
        action2 = self.additional_conversion
        return self._special_vert_full_tree(et, action1, action2)

    def _special_vert_full_tree(self, element, action1, action2):
        # element can be pymm element or etree element
        # e = from (the node / element being converted)
        # convert or revert the element!
        first = action1(element)
        hasUnchangedChildren = [first]
        while hasUnchangedChildren:
            element = hasUnchangedChildren.pop()
            unchanged = [child for child in element[:]]  # this must return all elements for pymm and etree
            children = []
            while unchanged:
                unchangedChild = unchanged.pop()
                child = action1(unchangedChild)
                children.append(child)
                hasUnchangedChildren.append(child)
            element[:] = children
        notFullyChanged = [first]
        while notFullyChanged:
            element = notFullyChanged.pop()
            notFullyChanged.extend(element[:])
            element = action2(element)
        return first
    
    def convert_etree_element(self, et):
        ff = self.get_conversion_factory_for(et)
        node = ff.convert_from_etree_element(et)
        return node

    def additional_conversion(self, et):
        ff = self.get_conversion_factory_for(et)
        return ff.additional_conversion(et)

    def get_conversion_factory_for(self, et):
        tag = None
        if hasattr(et, 'tag'):  # for an etree element
            tag = et.tag
        if hasattr(et, 'gettag'):  # for a node
            tag = et.gettag()
        if tag and tag in self.tag2factory:
            return self.tag2factory[tag]
        return self.defaultFactory

    def revert_node_and_tree(self, node):
        action1 = self.revert_node
        action2 = self.additional_reversion
        return self._special_vert_full_tree(node, action1, action2)

    def revert_node(self, node):
        ff = self.get_conversion_factory_for(node)
        et = ff.revert_to_etree_element(node)
        return et

    def additional_reversion(self, node):
        ff = self.get_conversion_factory_for(node)
        return ff.additional_reversion(node)
    
if __name__ == '__main__':
    fpf = FreeplaneFile()
    fpf.readfile('input.mm')
    element = fpf.xmlTree.getroot().findall('node')[0]
    m = fpf.getmap()
    n = fpf.getroot()
    #nc = n[0][0]
    #hs = element.findall('hook')  # hooks for maps???
    #hs[0].attrib  # prints off 'NAME' : 'MapStyle'
    try:
        fpf.writefile('output.mm')
    except:
        m = fpf.xmlTree._root
        raise
    finally:
        m = fpf.xmlTree._root

