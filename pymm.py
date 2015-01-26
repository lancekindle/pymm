import xml.etree.ElementTree as ET
from nodes import *

# to do: generic conversion for all children. Instead of housing "clouds, etc" in separate lists
# house all children of node in same _children list. But when iterating through children, only
# return the nodes. Then calls to getclouds() can instead iterate through all children, picking
# out any that have the tag "cloud" This way it's more similar to xml. Also, instead
# set type to be the actual nodetype. for example, RootNode will have tag "node" but type RootNode

# setting node attributes should be done by basenode, not basenodefactory! simply initalize the
# basenode with the attributes from the element

class FreeplaneFile(object):

    def __init__(self):
        self.xmlTree = ET.ElementTree()

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
        mapF = MapFactory()
        convFactory = ConversionFactory()
        etMapNode = xmlTree.getroot()
        self.mapnode = convFactory.convert_etree_element_and_tree(etMapNode)
        #self.mapnode = mapF.from_etree_element(etMapNode)

    def _revert(self, mapNode):
        #mapF = MapFactory()
        convFactory = ConversionFactory()
        etMapNode = convFactory.revert_node_and_tree(self.mapnode)
        #etMapNode = mapF.to_etree_element(self.mapnode)
        # need to convert mapNode too!
        self.xmlTree._root = etMapNode


# this dictionary will be utilized by all factories to determine which type of factory to initialize
# to handle all the children of an element
tag2class = {'hook': Hook, 'property': Property, 'attribute': Attribute, 'edge': Edge,
                    'icon': Icon, 'font': Font, 'map_styles': MapStyles, 'stylenode': StyleNode,
                    'cloud': Cloud, 'map': Map,'node': Node}

class BaseNodeFactory(object):
    
    def __init__(self, **kwargs):
        self.nodeType = BaseNode

    def from_etree_element(self, element):
        '''converts an xml etree element to a node
        '''
        node = self.nodeType()  # could be anything: Map, Node, etc.
        usedAttribs = []
        for key, value in element.attrib.items():  # sets node text, amongst other things
            key = key.lower()  # lowercase because that's how all our node properties are
##            if hasattr(node, key):
            setattr(node, key, value)  # all xml-node attribs become fp-node attributes
            usedAttribs.append(key)
        node[:] = element[:]  # append all unconverted children to this node!        
        unusedAttribs = {key.lower(): val for (key, val) in element.attrib.items() if key.lower() not in usedAttribs}
        if unusedAttribs:
            print('unused' + str(unusedAttribs))  # for diagnostics: determining if I need to add support for more stuff
        self._additional_conversion(node, element)
        return node

    def _additional_conversion(self, node, element):
        pass  # should be overridden by an inheriting class to perform addtional conversion before returning node

    def to_etree_element(self, node):
        attribs = {key.upper(): value for key, value in vars(node).items() if not key[0] == '_'}  # only use visible variables
        print(node)
        element = ET.Element(node.gettype().lower(), attribs)
        element[:] = node[:]
        self._additional_reversion(element, node)
        return element

    def _additional_reversion(self, element, node):
        if len(element) > 0:  # if element has any children
            element.text = node._tail  # set spacing/tail for written file layout
        element.tail = node._tail


class NodeFactory(BaseNodeFactory):
    def __init__(self, **kwargs):
        self.nodeType = Node

class MapFactory(BaseNodeFactory):
    def __init__(self, **kwargs):
        self.nodeType = Map

class CloudFactory(BaseNodeFactory):
    def __init__(self, **kwargs):
        self.nodeType = Cloud

class HookFactory(BaseNodeFactory):
    def __init__(self, **kwargs):
        self.nodeType = Hook

class MapStylesFactory(BaseNodeFactory):
    def __init__(self, **kwargs):
        self.nodeType = MapStyles

class StyleNodeFactory(BaseNodeFactory):
    def __init__(self, **kwargs):
        self.nodeType = StyleNode

class FontFactory(BaseNodeFactory):
    def __init__(self, **kwargs):
        self.nodeType = Font

class IconFactory(BaseNodeFactory):
    def __init__(self, **kwargs):
        self.nodeType = Icon

class EdgeFactory(BaseNodeFactory):
    def __init__(self, **kwargs):
        self.nodeType = Edge

class AttributeFactory(BaseNodeFactory):
    def __init__(self, **kwargs):
        self.nodeType = Attribute

class PropertyFactory(BaseNodeFactory):
    def __init__(self, **kwargs):
        self.nodeType = Property

class ConversionFactory(object):
    # this factory will just take a list of nodes to convert
    # and will convert by choosing which factory to use in converting a given node
    # it is also tasked with non-recursively converting all nodes contained
    # within the first converted node.
    factories = [BaseNodeFactory, NodeFactory, MapFactory, CloudFactory,
                     HookFactory, MapStylesFactory, StyleNodeFactory, FontFactory, IconFactory,
                     EdgeFactory, AttributeFactory, PropertyFactory]
    ffs = [factory() for factory in factories]  # get an initialized instance of all factories
    tag2factory = {fctry.nodeType()._tag: fctry for fctry in ffs}  # get a dictionary that
                            # matches an elements tag to the factory which can handle that element
    defaultFactory = BaseNodeFactory()
    def __init__(self):
        pass

    def convert_etree_element_and_tree(self, et):
        firstNode = self.convert_etree_element(et)
        hasUnconvertedChildren = [firstNode]
        while hasUnconvertedChildren:
            node = hasUnconvertedChildren.pop()
            unconverted = [c for c in node.iterate('*')]  # need all children. If we use node[:] then it will
                                                                # filter out unconverted children
            children = []
            while unconverted:
                etchild = unconverted.pop()
                child = self.convert_etree_element(etchild)
                children.append(child)
                hasUnconvertedChildren.append(child)
            node[:] = children
        return firstNode
    
    def convert_etree_element(self, et):
        if et.tag in self.tag2factory:
            ff = self.tag2factory[et.tag]
        else:
            ff = self.defaultFactory
        print('using factory' + str(ff))
        node = ff.from_etree_element(et)
        return node

    def revert_node_and_tree(self, node):
        firstET = self.revert_node(node)
        hasUnrevertedChildren = [firstET]
        while hasUnrevertedChildren:
            et = hasUnrevertedChildren.pop()
            unreverted = [c for c in et]
            etchildren  = []
            while unreverted:
                child = unreverted.pop()
                etchild = self.revert_node(child)
                etchildren.append(etchild)
                hasUnrevertedChildren.append(etchild)
            et[:] = etchildren
        return firstET

    def revert_node(self, node):
        if node._tag in self.tag2factory:
            ff = self.tag2factory[node._tag]
        else:
            ff = self.defaultFactory
        print('using factory for reversion' + str(ff))
        et = ff.to_etree_element(node)
        return et
    
if __name__ == '__main__':
    fpf = FreeplaneFile()
    fpf.readfile('input.mm')
    element = fpf.xmlTree.getroot().findall('node')[0]
    n = fpf.getroot()
    nc = n[0][0]
    hs = element.findall('hook')  # hooks for maps???
    hs[0].attrib  # prints off 'NAME' : 'MapStyle'
    try:
        fpf.writefile('output.mm')
    except:
        m = fpf.xmlTree._root
        raise
    finally:
        m = fpf.xmlTree._root

