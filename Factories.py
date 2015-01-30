import xml.etree.ElementTree as ET
from Elements import *

class BaseElementFactory(object):

    elementType = BaseElement

    def convert_from_etree_element(self, element):
        '''converts an xml etree element to a node
        '''
        node = self.elementType()  # could be anything: Map, Node, etc.
        usedAttribs = []
        for key, value in element.attrib.items():
            node[key] = value  # attribs of a node are stored dictionary style in the node
            usedAttribs.append(key)
        node[:] = element[:]  # append all unconverted children to this node!
        unusedAttribs = {key: val for (key, val) in element.attrib.items() if key not in usedAttribs}
        if unusedAttribs:
            print('unused' + str(unusedAttribs))  # for diagnostics: determining if I need to add support for more stuff
        return node

    def additional_conversion(self, node):  # should be called full tree conversion
        return node  # should be overridden by an inheriting class to perform addtional conversion before returning node

    def revert_to_etree_element(self, node):
        attribs = {key: value for key, value in node.items()  # unfortunately, you cannot make these attribs ordered
                       if value is not None}  # without some serious hackjobs. Possible, but not worth it.
        element = ET.Element(node.gettag(), **attribs)
        element[:] = node[:]
        return element

    def additional_reversion(self, element):  # call after full tree reversion
        if len(element) > 0:  # if element has any children
            element.text = '\n'  # set spacing/tail for written file layout
        element.tail = '\n'
        return element


class NodeFactory(BaseElementFactory):
    elementType = Node

    def additional_conversion(self, node):
        node.settext(node['TEXT'])
        #del node['TEXT']  # remove text so that you can access the text of the node using node.gettext()
        return node

    def revert_to_etree_element(self, node):
        node['TEXT'] = node.gettext()
        return super(NodeFactory, self).revert_to_etree_element(node)

class MapFactory(BaseElementFactory):
    elementType = Map

class CloudFactory(BaseElementFactory):
    elementType = Cloud

class HookFactory(BaseElementFactory):
    elementType = Hook

class MapStylesFactory(BaseElementFactory):
    elementType = MapStyles

class StyleNodeFactory(BaseElementFactory):
    elementType = StyleNode

class FontFactory(BaseElementFactory):
    elementType = Font

class IconFactory(BaseElementFactory):
    elementType = Icon

class EdgeFactory(BaseElementFactory):
    elementType = Edge

class AttributeFactory(BaseElementFactory):
    elementType = Attribute

class PropertiesFactory(BaseElementFactory):
    elementType = Properties