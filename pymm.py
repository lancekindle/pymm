import xml.etree.ElementTree as ET
from elements import *

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
tag2class = {'hook': Hook, 'properties': Properties, 'attribute': Attribute, 'edge': Edge,
                    'icon': Icon, 'font': Font, 'map_styles': MapStyles, 'stylenode': StyleNode,
                    'cloud': Cloud, 'map': Map,'node': Node}

class BaseElementFactory(object):
    
    def __init__(self, **kwargs):
        self.elementType = BaseElement

    def convert_from_etree_element(self, element):
        '''converts an xml etree element to a node
        '''
        node = self.elementType()  # could be anything: Map, Node, etc.
        usedAttribs = []
        for key, value in element.attrib.items():
            node[key] = value  # attribs of a node are stored dictionary style in the node
            usedAttribs.append(key)
        node[:] = element[:]  # append all unconverted children to this node!
        unusedAttribs = {key.lower(): val for (key, val) in element.attrib.items() if key.lower() not in usedAttribs}
        if unusedAttribs:
            print('unused' + str(unusedAttribs))  # for diagnostics: determining if I need to add support for more stuff
        return node

    def additional_conversion(self, node):  # should be called full tree conversion
        return node  # should be overridden by an inheriting class to perform addtional conversion before returning node

    def revert_to_etree_element(self, node):

        attribs = {key: value for key, value in node.items()
                       if value is not None }  # only use visible variables
        print(node)
        print(node.gettag())
        element = ET.Element(node.gettag(), attribs)
        element[:] = node[:]
        return element

    def additional_reversion(self, element):  # call after full tree reversion
        if len(element) > 0:  # if element has any children
            element.text = '\n'  # set spacing/tail for written file layout
        element.tail = '\n'
        return element


class NodeFactory(BaseElementFactory):
    def __init__(self, **kwargs):
        self.elementType = Node

    def additional_conversion(self, node):
        node.settext(node['TEXT'])
        del node['TEXT']  # remove text so that you can access the text of the node using node.gettext()
        return node

    def revert_to_etree_element(self, node):
        node['TEXT'] = node.gettext()
        return super(NodeFactory, self).revert_to_etree_element(node)

class MapFactory(BaseElementFactory):
    def __init__(self, **kwargs):
        self.elementType = Map

class CloudFactory(BaseElementFactory):
    def __init__(self, **kwargs):
        self.elementType = Cloud

class HookFactory(BaseElementFactory):
    def __init__(self, **kwargs):
        self.elementType = Hook

class MapStylesFactory(BaseElementFactory):
    def __init__(self, **kwargs):
        self.elementType = MapStyles

class StyleNodeFactory(BaseElementFactory):
    def __init__(self, **kwargs):
        self.elementType = StyleNode

class FontFactory(BaseElementFactory):
    def __init__(self, **kwargs):
        self.elementType = Font

class IconFactory(BaseElementFactory):
    def __init__(self, **kwargs):
        self.elementType = Icon

class EdgeFactory(BaseElementFactory):
    def __init__(self, **kwargs):
        self.elementType = Edge

class AttributeFactory(BaseElementFactory):
    def __init__(self, **kwargs):
        self.elementType = Attribute

class PropertiesFactory(BaseElementFactory):
    def __init__(self, **kwargs):
        self.elementType = Properties

class ConversionFactory(object):
    # this factory will just take a list of nodes to convert
    # and will convert by choosing which factory to use in converting a given node
    # it is also tasked with non-recursively converting all nodes contained
    # within the first converted node.
    factories = [BaseElementFactory, NodeFactory, MapFactory, CloudFactory,
                     HookFactory, MapStylesFactory, StyleNodeFactory, FontFactory, IconFactory,
                     EdgeFactory, AttributeFactory, PropertiesFactory]
    ffs = [factory() for factory in factories]  # get an initialized instance of all factories
    tag2factory = {fctry.elementType().gettag(): fctry for fctry in ffs}  # get a dictionary that
                            # matches an elements tag to the factory which can handle that element
    defaultFactory = BaseElementFactory()
    def __init__(self):
        pass

    def convert_etree_element_and_tree(self, et):
        action1 = self.convert_etree_element
        action2 = self.additional_conversion
        return self.special_vert_full_tree(et, action1, action2)

    def special_vert_full_tree(self, element, action1, action2):
        # element can be pymm element or etree element
        # e = from (the node / element being converted)
        # convert or revert the element!
        first = action1(element)
        hasUnchangedChildren = [first]
        print('first: ' + str(first))
        print(first.findall('*'))
        while hasUnchangedChildren:
            element = hasUnchangedChildren.pop()
            unchanged = [child for child in element.findall('*')]  # this must return all elements for pymm and etree
            children = []
            while unchanged:
                unchangedChild = unchanged.pop()
                child = action1(unchangedChild)
                children.append(child)
                hasUnchangedChildren.append(child)
            element[:] = children  # found it! this needs to set ALL children for element. But currently [:] only
            # gets or sets the children of Nodes
            # this requires a full change from what I currently have setup. I think this means that I'll need to set
            # the behavior of the node differently. Obviously, the objective is to make reading nodes easier
            # but if I can't access the nodes using the same syntax as etree elements, then I need to separate the node behavior.

            # ok how about normal children node[1] or node[:] always access children?
            # BUT accessing specifically the nodes of one of those is done by: node.nodes() -> returns iterator
            # and that's a specific function from the basenode. So that way you can get pretty consistent behavior.
            # and accessing nodes is a way to get the nodes as you find them.
        notFullyChanged = [first]
        while notFullyChanged:
            element = notFullyChanged.pop()
            notFullyChanged.extend(element.findall('*'))
            element = action2(element)
        return first
    
    def convert_etree_element(self, et):
        ff = self.get_conversion_factory_for(et)
        print('using factory' + str(ff))
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
        print(node)
        action1 = self.revert_node
        action2 = self.additional_reversion
        return self.special_vert_full_tree(node, action1, action2)

    def revert_node(self, node):
        ff = self.get_conversion_factory_for(node)
        print('using factory for reversion' + str(ff))
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

