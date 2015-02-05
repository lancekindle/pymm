import xml.etree.ElementTree as ET
from Elements import *

class BaseElementFactory(object):

    elementType = BaseElement
    childOrder = [BaseElement.tag, ArrowLink.tag, Cloud.tag, Edge.tag, Properties.tag, MapStyles.tag, Icon.tag,
                  AttributeLayout.tag, Attribute.tag, Hook.tag, Font.tag, StyleNode.tag, RichContent.tag]
                  # order in which children will be written to file
    lastChildOrder = [] # order of nth to last for children. First node listed will be last child.
    attribSpecs = {}  # list attribute and their type (str, bool, integer, decimal)
    # xml etree appears to correctly convert html-safe to ascii: &lt; = <

    def convert_attribs(self, element, node):
        '''
        :param element - attribs from which to be converted:
        :param node - node to which to apply elements:
        :return node:
        transfers all attributes from element to node, converting where necessary.
        '''
        for key, value in element.attrib.items():
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
                    raise ValueError(key +'=' + value + ' not part of ' + node.tag + ' specs')
            except ValueError:
                warnings.warn('Attrib ' + key + '=' + value + ' not valid ' + node.tag + ' specs', SyntaxWarning,
                              stacklevel=2)
            finally:
                node[key] = value
        return node

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
                        if not type(value) == bool:
                            raise ValueError(str(key) + '=' + str(value) + ' not boolean as expected')
                        value = str(value).lower()  # get 'false' or 'true' strings
                else:
                    raise ValueError(key +'=' + value + ' not part of ' + node.tag + ' specs')
            except ValueError:
                key, value = str(key), str(value)
                warnings.warn('Attrib ' + key + '=' + value + ' not valid ' + node.tag + ' specs', SyntaxWarning,
                              stacklevel=2)
            finally:
                key, value = str(key), str(value)
                revertedAttribs[key] = value
        return revertedAttribs

    def convert_from_etree_element(self, element):
        '''converts an xml etree element to a node
        '''
        node = self.elementType()  # could be anything: Map, Node, etc.
        self.childOrder = list(self.childOrder) + []  # make list instance so we don't modify class variable
        self.lastChildOrder = list(self.lastChildOrder) + []
        node = self.convert_attribs(element, node)
        # for key, value in element.attrib.items():
        #     node[key] = value  # attribs of a node are stored dictionary style in the node
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
        attribs = self.revert_attribs(node)
        # attribs = {key: value for key, value in node.items()  # unfortunately, you cannot make these attribs ordered
        #                if value is not None}  # without some serious hackjobs. Possible, but NOT worth it.
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