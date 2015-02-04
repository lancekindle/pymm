import xml.etree.ElementTree as ET
from Elements import *

class BaseElementFactory(object):

    elementType = BaseElement
    childOrder = [BaseElement.tag, Cloud.tag, Edge.tag, Properties.tag, MapStyles.tag, Icon.tag,
            Attribute.tag, Hook.tag, Font.tag, StyleNode.tag]  # order in which children will be written to file
    lastChildOrder = [Node.tag] # order of nth to last for children. First node listed will be last child.
    # xml etree appears to correctly convert html-safe to ascii: &lt; = <

    def convert_from_etree_element(self, element):
        '''converts an xml etree element to a node
        '''
        node = self.elementType()  # could be anything: Map, Node, etc.
        self.childOrder = list(self.childOrder) + []  # make list instance so we don't modify class variable
        self.lastChildOrder = list(self.lastChildOrder) + []
        usedAttribs = []
        for key, value in element.attrib.items():
            node[key] = value  # attribs of a node are stored dictionary style in the node
            usedAttribs.append(key)
        node[:] = element[:]  # append all unconverted children to this node!
        if not node.tag == element.tag:
            warnings.warn('element "' + str(element.tag) + '" does not have a corresponding conversion factory. ' +
                          'Element will import and export correctly, but manipulation will be more difficult',
                          UserWarning, stacklevel=2)
            node.tag = element.tag
        return node

    def additional_conversion(self, node):  # should be called full tree conversion
        return node  # should be overridden by an inheriting class to perform addtional conversion before returning node

    def revert_to_etree_element(self, node):
        attribs = {key: value for key, value in node.items()  # unfortunately, you cannot make these attribs ordered
                       if value is not None}  # without some serious hackjobs. Possible, but NOT worth it.
        self.sort_element_children(node)
        element = ET.Element(node.tag, **attribs)
        element[:] = node[:]
        return element

    def additional_reversion(self, element):  # call after full tree reversion
        if len(element) > 0:  # if element has any children
            element.text = '\n'  # set spacing/tail for written file layout
        element.tail = '\n'
        return element

    def sort_element_children(self, element):  # for reverting to etree element. Organizes children for file readability
        for tag in self.childOrder:
            children = element.findall(tag)
            for e in children:
                element.remove(e)
                element.append(e)
        for tag in reversed(self.lastChildOrder):  # nodes you want to show last
            children = element.findall(tag)
            for e in children:
                element.remove(e)
                element.append(e)


class NodeFactory(BaseElementFactory):
    elementType = Node

    def additional_conversion(self, node):
        if 'TEXT' in node:
            node.settext(node['TEXT'])  # if not, we may expect a richcontent child then....
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