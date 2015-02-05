import xml.etree.ElementTree as ET
from Elements import *
import warnings

class BaseElementFactory(object):

    elementType = BaseElement
    childOrder = [BaseElement.tag, ArrowLink.tag, Cloud.tag, Edge.tag, Properties.tag, MapStyles.tag, Icon.tag,
                  AttributeLayout.tag, Attribute.tag, Hook.tag, Font.tag, StyleNode.tag, RichContent.tag, Node.tag]
                  # order in which children will be written to file
    lastChildOrder = []  # order of nth to last for children. First node listed will be last child.
    otherElementTypes = []  # if same tag can be used for different Elements, list them here, in a tuple with a
                         # distinguishing attribute name and its expected value: (element, attribName, attribValue)
    # xml etree appears to correctly convert html-safe to ascii: &lt; = <

    def __init__(self):
        self.childOrder = list(self.childOrder) + []  # make list instance so we don't modify class variable
        self.lastChildOrder = list(self.lastChildOrder) + []
        self.otherElementTypes = list(self.otherElementTypes) + []

    def compute_element_type(self, element):
        etype = self.elementType  # default
        otherChoices = []
        for otherType, key, value in self.otherElementTypes:
            if key in element.attrib and element.attrib[key] == value:
                otherChoices.append(otherType)
        if len(otherChoices) > 1:
            warnings.warn(element.tag + ' has 2+ possible elements with which to convert with these attribs: ' +
                          str(element.attrib), RuntimeWarning, stacklevel=2)
        for possibleElementType in otherChoices:
            etype = possibleElementType  # choose last of choices, then
        return etype

    def convert_from_etree_element(self, element):
        '''converts an xml etree element to a node
        '''
        etype = self.compute_element_type(element)  # choose between self.elementType and otherElementTypes
        node = etype()  # could be anything: Map, Node, etc.
        attribs = self.convert_attribs(node, element.attrib)
        for key, value in attribs.items():
            node[key] = value  # attribs of a node are stored dictionary style in the node
        node[:] = element[:]  # append all unconverted children to this node!
        if not node.tag == element.tag:
            warnings.warn('element <' + str(element.tag) + '> does not have a factory. ' +
                          'Element will import and export correctly, but warnings about specs will follow',
                          RuntimeWarning, stacklevel=2)
            node.tag = element.tag
        return node

    def additional_conversion(self, node):  # should be called full tree conversion
        return node  # should be overridden by an inheriting class to perform addtional conversion before returning node

    def revert_to_etree_element(self, node):
        attribs = self.revert_attribs(node)
        self.sort_element_children(node)
        element = ET.Element(node.tag, **attribs)  # fyi: impossible to write attribs in specific order.
        element[:] = node[:]                       # ETree always sorts em
        return element

    def additional_reversion(self, element):  # call after full tree reversion
        if len(element) > 0:
            element.text = '\n'  # set spacing for written file layout, (but only if it has children!)
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

    def convert_attribs(self, node, attribs):
        '''
        :param element - attribs from which to be converted:
        :param node - node to which to apply elements:
        :return node:
        transfers all attributes from element to node, converting where necessary.
        '''
        convertedAttribs = {}
        for key, value in attribs.items():
            #key, value = str(key), str(value)  # converting from et element: assume all keys and values are strings
            try:
                if key in node._attribSpecs:
                    vtype = node._attribSpecs[key]
                    if isinstance(vtype, list):  # a list for multiple values (always strings)
                        vlist = vtype  # the value type is actually a list of possible values
                        if value not in vlist:  # do nothing but warn. Do not change value
                            raise ValueError(key + '=' + value + ' not in ' + str(vlist))
                    # skip checking if vtype == str.. we don't modify in that case
                    elif vtype == float:  # decimal/float
                        value = float(value)
                    elif vtype == int:  # integer
                        value = int(value)
                    elif vtype == bool:  # boolean logic
                        if value.lower() == 'false':
                            value = False
                        elif value.lower() == 'true':
                            value = True
                        else:
                            raise ValueError(key + '=' + value + ' not boolean')
                else:
                    raise ValueError(key +'=' + value + ' not part of <' + node.tag + '> specs')
            except ValueError:
                warnings.warn('Attrib ' + key + '=' + value + ' not valid <' + node.tag + '> specs', SyntaxWarning,
                              stacklevel=2)
            finally:
                convertedAttribs[key] = value
        return convertedAttribs

    def revert_attribs(self, node):
        '''
        :param node - attribs from which to be converted:
        :param element - element to which to apply attribs:
        :return element:
        transfers all attributes from node to element, converting where necessary.
        '''
        attribs = {key: value for key, value in node.items() if value is not None}
        revertedAttribs = {}
        for key, value in attribs.items():
            try:
                if key in node._attribSpecs:
                    vtype = node._attribSpecs[key]
                    if isinstance(vtype, list):  # a list for multiple values (always strings)
                        vlist = vtype  # the value type is actually a list of possible values
                        if value not in vlist:  # do nothing but warn. Do not change value
                            raise ValueError(str(key) + '=' + str(value) + ' not in ' + str(vlist))
                    # skip checking if vtype == str.. we don't modify in that case
                    elif vtype == float:  # decimal/float
                        value = str(float(value))
                    elif vtype == int:  # integer
                        value = str(int(value))
                    elif vtype == bool:  # boolean logic
                        if str(value).lower() not in ['true', 'false']:
                            raise ValueError(str(key) + '=' + str(value) + ' not boolean as expected')
                        value = str(value).lower()  # get 'false' or 'true' strings
                else:
                    raise ValueError(key +'=' + value + ' not part of <' + node.tag + '> specs')
            except ValueError:
                key, value = str(key), str(value)
                warnings.warn('Attrib ' + key + '=' + value + ' not valid <' + node.tag + '> specs', SyntaxWarning,
                              stacklevel=2)
            finally:
                key, value = str(key), str(value)
                revertedAttribs[key] = value
        return revertedAttribs


class NodeFactory(BaseElementFactory):
    elementType = Node
    childOrder = [BaseElement.tag, ArrowLink.tag, Cloud.tag, Edge.tag, Font.tag, Hook.tag, Icon.tag, Node.tag,
                  RichContent.tag, AttributeLayout.tag, Attribute.tag]

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
    otherElementTypes = [(EmbeddedImage, 'NAME', 'ExternalObject'),(MapConfig, 'NAME', 'MapStyle'),
                         (Equation, 'NAME', 'plugins/latex/LatexNodeHook.properties'),
                         (AutomaticEdgeColor, 'NAME', 'AutomaticEdgeColor')]

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

class RichContentFactory(BaseElementFactory):
    elementType = RichContent

    def convert_from_etree_element(self, element):
        node = super(RichContentFactory, self).convert_from_etree_element(element)
        # need to convert child html, head, body to nothing, and get text from rest!
        htmlchildren = element[:]
        parent = element
        while htmlchildren:
            child = htmlchildren.pop(0)
            if child.tag == 'html':
                parent.remove(child)
                node.remove(child)  # once this is gone...
                htmlchildren = child[:]
                parent = child
                continue
            if child.tag == 'head':
                parent.remove(child)
                continue  # we popped off child, so continuing essentially gets rid of it.
            if child.tag == 'body':
                parent.remove(child)
                htmlchildren = child[:]
                break
        html = ''
        for child in htmlchildren:
            html += ET.tostring(child)
        node.html = html
        return node

    def additional_conversion(self, node):
        node = super(RichContentFactory, self).additional_conversion(node)
        if node.parent:
            node.parent.settext(node.html)
        return node