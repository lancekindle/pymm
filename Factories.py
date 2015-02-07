import xml.etree.ElementTree as ET
from Elements import *
import warnings
from copy import copy


class RemoveElementAndChildrenFromTree(BaseException):
    pass

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
        self.noFactoryWarnings = set()  # collect tags that didn't have factories and use it to send out ONE warning

    def display_any_warnings(self):
        if self.noFactoryWarnings:
            warnings.warn('elements ' + str(self.noFactoryWarnings) + ' do not have conversion factories. ' +
                           'Elements will import and export correctly, but warnings about specs will follow',
                           RuntimeWarning, stacklevel=2)
        self.noFactoryWarnings = set()  # reset warnings so we won't display the same onces

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

    def convert_from_etree_element(self, element, parent):
        '''converts an xml etree element to a node
        :param parent:
        '''
        etype = self.compute_element_type(element)  # choose between self.elementType and otherElementTypes
        node = etype()  # could be anything: Map, Node, etc.
        attribs = self.convert_attribs(node, element.attrib)
        node = etype(**attribs)  # yep, we initialize it a second time, but this time with attribs
        node[:] = element[:]  # append all unconverted children to this node!
        if not node.tag == element.tag:
            self.noFactoryWarnings.add(element.tag)
            node.tag = element.tag
        return node

    def additional_conversion(self, node, parent):  # should be called full tree conversion
        return node  # should be overridden by an inheriting class to perform addtional conversion before returning node

    def revert_to_etree_element(self, node, parent):
        if isinstance(node, ET.Element):  # we expected a pymm element, not an Etree Element
            warnings.warn('program is reverting an ET Element! ' + str(node) + ' which means that it will lose text' +
            ' and tail properties. If you wish to preserve those, consider attaching ET Element as child of an' +
            ' Element in the "additional_reversion" function instead. This message indicates that the Element was ' +
            'added during the "revert_to_etree_element" function call. See RichContentFactory for an example.',
            RuntimeWarning, stacklevel=2)
        attribs = self.revert_attribs(node)
        self.sort_element_children(node)
        element = ET.Element(node.tag, **attribs)  # fyi: impossible to write attribs in specific order.
        element[:] = node[:]                       # ETree always sorts em  PS HERE is where we fail to write text&tail
        return element

    def additional_reversion(self, element, parent):  # call after full tree reversion
        if len(element) > 0 and not element.text:
            element.text = '\n'  # set spacing for written file layout, (but only if it has children!)
        if not element.tail:  # if tail is blank; we'll fill it in!
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
        for key, value in attribs.items():  # converting from et element: assume all keys and values are strings
            try:
                if key in node.specs:
                    vtype = node.specs[key]
                    if isinstance(vtype, list):  # a list for multiple values (always strings)
                        vlist = vtype
                        if value not in vlist:
                            raise ValueError  # do nothing but warn. Do not change value
                    elif vtype == bool:  # boolean logic
                        truefalse = {'true': True,'false': False}
                        if value.lower() in truefalse:
                            value = truefalse[value.lower()]
                        else:
                            raise ValueError
                    else:
                        value = vtype(value)  # float or integer
                elif node.specs:  # if we do have specs but didn't find our key in them, THEN give warning
                    raise ValueError
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
        transfers all attributes from node to element, converting where necessary. If value conversion fails, simply
        convert value to string
        '''
        attribs = {key: value for key, value in node.items() if value is not None}  # drop all None-valued attribs
        revertedAttribs = {}
        for key, value in attribs.items():
            if key in node.specs:  # convert values, defaulting to str(value) if necessary
                vtype = node.specs[key]
                if isinstance(vtype, list):  # a list for multiple values (always strings)
                    pass
                elif vtype == bool:  # boolean logic
                    value = str(value).lower()  # get 'false' or 'true' strings
                else:
                    value = str(vtype(value))  # float or integer
            key, value = str(key), str(value)
            revertedAttribs[key] = value
        return revertedAttribs


class NodeFactory(BaseElementFactory):
    elementType = Node
    childOrder = [BaseElement.tag, ArrowLink.tag, Cloud.tag, Edge.tag, Font.tag, Hook.tag, Properties.tag,
                  RichContent.tag, Icon.tag, Node.tag, AttributeLayout.tag, Attribute.tag]

    def additional_conversion(self, node, parent):
        super(NodeFactory, self).additional_conversion(node, parent)
        node = self.convert_node_text(node)
        return node

    def revert_to_etree_element(self, node, parent):
        node = self.revert_node_text(node)
        return super(NodeFactory, self).revert_to_etree_element(node, parent)

    def revert_node_text(self, node):
        node = copy(node)  # why do this? Because then I can delete node['TEXT'] without affecting original tree
        ntext = NodeText()  # developer / user NEVER needs to create his own RichContent for node html
        ntext.html = node['TEXT']
        if ntext.is_html():
            node.append(ntext)
            del node['TEXT']  # using richcontent, do not leave attribute 'TEXT' for node
        return node

    def convert_node_text(self, node):
        richElements = node.findall('richcontent')
        while richElements:
            richElem = richElements.pop(0)
            if isinstance(richElem, NodeText):
                node['TEXT'] = richElem.html
                node.remove(richElem)  # this NodeText is no longer needed
        return node

class MapFactory(BaseElementFactory):
    elementType = Map

    def additional_reversion(self, element, parent):
        element = super(MapFactory, self).additional_reversion(element, parent)
        comment = ET.Comment('To view this file, download free mind mapping software Freeplane from ' +
                   'http://freeplane.sourceforge.net')
        comment.tail = '\n'
        element[:] = [comment] + element[:]
        return element

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

class AttributeRegistryFactory(BaseElementFactory):
    elementType = AttributeRegistry

class RichContentFactory(BaseElementFactory):
    elementType = RichContent
    otherElementTypes = [(NodeText, 'TYPE', 'NODE'), (NodeNote, 'TYPE', 'NOTE'), (NodeDetails, 'TYPE', 'DETAILS')]

    def convert_from_etree_element(self, element, parent):
        richElement = super(RichContentFactory, self).convert_from_etree_element(element, parent)
        html = ''                        # this makes a critical assumption that there'll be 1 child. If not, upon
        for htmlElement in richElement:  # reversion, ET may complain about "ParseError: junk after document element...
            html += ET.tostring(htmlElement)
        richElement.html = html
        richElement[:] = []  # remove html children to prevent their conversion.
        return richElement

    def revert_to_etree_element(self, richElem, parent):
        html = richElem.html
        element = super(RichContentFactory, self).revert_to_etree_element(richElem, parent)
        element.text = html  # temporarily store html string in element.text  (will convert in additional_reversion)
        return element

    def additional_reversion(self, element, parent):
        html = element.text
        element.text = '\n'
        super(RichContentFactory, self).additional_reversion(element, parent)  # just sets tail...
        element.append(ET.fromstring(html))
        return element