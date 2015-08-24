import xml.etree.ElementTree as ET
from Elements import *
import warnings
import copy

#terminology  ... mme, mmElem, mmElement == MindMap element
            #.... ete, etElem, etElement == ElementTree element
            # element == could be either one. Sometimes it must conform to either one, other times it doesn't yet
                       # conform to a specific element


class ExampleElementFactory:  # an example factory that shows which methods you'll need to
                                                      # override when inheriting from BaseElementFactory
    def revert_to_etree_element(self, mmElement, parent=None):
        etElement = super().revert_to_etree_element(mmElement, parent)  # does all the heavy lifting.
        raise NotImplementedError('DO NOT use ExampleElementFactory. Inherit from BaseElementFactory Instead!')
        return etElement

    def convert_from_etree_element(self, etElement, parent=None):
        mmElem = super().convert_from_etree_element(etElement, parent)
        raise NotImplementedError('DO NOT use ExampleElementFactory. Inherit from BaseElementFactory Instead!')
        return mmElem


class SimpleConverter:  # a super-simple converter that you can use in reverting your custom nodes into another file format.

    def write(self, filename, node_tree):
        with open(filename, 'w') as self.file:
            self.revert_node_tree_depth_first(node_tree)  # SimpleConverter only works with nodes, since it's expected to be
                                                                                               # the only usable part of the mindmap.
    def revert_node_tree_depth_first(self, node):
        self.revert_node(node)
        for child in node.nodes:
            self.revert_node_tree_depth_first(child)

    def revert_node(self, node):  # this is the only method you need to override.
        self.file.writeline(node['TEXT'])
    

class BaseElementFactory:
    ''' Convert between ElementTree elements and pymm elements.

    Conversion from ElementTree element to pymm elements is done by passing the etElement to convert_from_et_element()
    After converting the full tree's worth of elements, re-iterate through the tree (starting at top-level) and pass
    that element into this factory's finish_conversion(). For each conversion / reversion function, convert the full
    xml tree before using the finish_ function. Factory does not keep children. In converting full xml-tree, you will
    have to add the children how you see fit. Generally, it is best to add the children after initial convert / revert
    and then immediately convert / revert those children. This pattern avoids recursion limits in python.
    '''
    elementType = BaseElement
    childOrder = [BaseElement.tag, ArrowLink.tag, Cloud.tag, Edge.tag, Properties.tag, MapStyles.tag, Icon.tag,
                  AttributeLayout.tag, Attribute.tag, Hook.tag, Font.tag, StyleNode.tag, RichContent.tag, Node.tag]
                  # order in which children will be written to file
    reverseChildOrder = []  # order of nth to last for children. First node listed will be last child.
    typeVariants = []  # if same tag can be used for different Elements, list them here, in a tuple with a
                         # distinguishing attribute name and its expected value: (element, attribName, attribValue)
    # xml etree appears to correctly convert html-safe to ascii: &lt; = <

    def __init__(self):
        self.childOrder = list(self.childOrder) + []  # make list instance so we don't modify class variable
        self.reverseChildOrder = list(self.reverseChildOrder) + []
        self.typeVariants = list(self.typeVariants) + []
        self.noFactoryWarnings = set()  # collect tags that didn't have factories and use it to send out ONE warning

    def display_any_warnings(self):
        ''' Display warnings for elements found without a specific factory. Call once after full convert / revert '''
        if self.noFactoryWarnings:
            warnings.warn('elements ' + str(self.noFactoryWarnings) + ' do not have conversion factories. ' +
                           'Elements will import and export correctly, but warnings about specs will follow',
                           RuntimeWarning, stacklevel=2)
        self.noFactoryWarnings = set()  # reset warnings so we won't display the same ones

    def compute_element_type(self, etElement):
        ''' Choose amongst several pymm elements for etree element with same tag using attribute properties

        Used in special cases when user wants to sub-categorize elements with the same tag. For example, RichContent
        has several different types: NODE, NOTE, and DETAILS. Specify which type of element to create by adding
        attribute distinguishers to factory.typeVariants. The same factory will be used, however.
        '''
        etype = self.elementType  # default
        otherChoices = []
        for otherType, key, value in self.typeVariants:
            if key in etElement.attrib and etElement.attrib[key] == value:
                otherChoices.append(otherType)
        if len(otherChoices) > 1:
            warnings.warn(etElement.tag + ' has 2+ possible elements with which to convert with these attribs: ' +
                                       str(etElement.attrib), RuntimeWarning, stacklevel=2)
        for possibleElementType in otherChoices:
            etype = possibleElementType  # choose last of choices, then
        return etype

    def convert_from_etree_element(self, etElement, parent=None):
        '''converts an etree etElement to a pymm element

        :param parent:
        :returns mmElement or None
        If you return None, this etElement and all its children will be dropped from tree.
        '''
        elemClass = self.compute_element_type(etElement)  # choose between self.elementType and typeVariants
        attrib = self.convert_attribs(elemClass(), etElement.attrib)
        mmElem = elemClass(**attrib)  # yep, we initialize it a second time, but this time with attribs  (I don't know why this doesn't work)
        mmElem.children = [c for c in etElement[:]]
        if not mmElem.tag == etElement.tag:
            self.noFactoryWarnings.add(etElement.tag)
            mmElem.tag = etElement.tag
        return mmElem

    def finish_conversion(self, mmElement, parent=None):  # should be called full tree conversion
        ''' Finishes conversion of mindmap element. Call only after convert_from_etree_element() has converted tree

        :return mindmap Element or None
        if return None, it is expected that this element and all its children will be dropped from tree
        '''
        return mmElement

    def revert_to_etree_element(self, mmElement, parent=None):
        # If you return None, this element and all its children will be dropped from tree.
        if isinstance(mmElement, ET.Element):  # we expected a pymm element, not an Etree Element
            warnings.warn('program is reverting an ET Element! ' + str(mmElement) + ' which means that it will lose text' +
            ' and tail properties. If you wish to preserve those, consider attaching ET Element as child of an' +
            ' Element in the "additional_reversion" function instead. This message indicates that the Element was ' +
            'added during the "revert_to_etree_element" function call. See RichContentFactory for an example.',
            RuntimeWarning, stacklevel=2)
        attribs = self.revert_attribs(mmElement)
        self.sort_element_children(mmElement)
        etElem = ET.Element(mmElement.tag, attribs)  # fyi: impossible to write attribs in specific order.
        etElem[:] = mmElement.children  # set children on et element
        etElem.text = mmElement._text
        etElem.tail = mmElement._tail
        return etElem

    def finish_reversion(self, etElement, parent=None):  # call after full tree reversion
        # If you return None, this etElement and all its children will be dropped from tree.
        if len(etElement) > 0 and not etElement.text:
            etElement.text = '\n'  # set spacing for written file layout, (but only if it has children!)
        if not etElement.tail:  # if tail is blank; we'll fill it in!
            etElement.tail = '\n'
        return etElement

    def sort_element_children(self, element):  # for reverting to etree element. Organizes children for file readability
        for tag in self.childOrder:
            children = element.findall(tag)
            for e in children:
                element.remove(e)
                element.append(e)
        for tag in reversed(self.reverseChildOrder):  # nodes you want to show last
            children = element.findall(tag)
            for e in children:
                element.remove(e)
                element.append(e)

    def convert_attribs(self, mmElement, attribs):
        ''' using mmElement (class or instance) as guide, converts attribs (from etree element) to match the specs in mmElement
        warn (but still allow it) if attribute key/value pair is not a valid
        '''
        convertedAttribs = {}
        for key, value in attribs.items():  # converting from et element: assume all keys and values are strings
            try:
                if key not in mmElement.specs:
                    if mmElement.specs:  # give warning if specs is filled out but didn't find key
                        raise ValueError
                entries = mmElement.specs[key]
                value = self.convert_attrib_value_using_spec_entries(value, entries)
            except ValueError:
                warnings.warn('Attrib ' + key + '=' + value + ' not valid <' + mmElement.tag + '> specs', SyntaxWarning,
                                          stacklevel=2)
            finally:
                convertedAttribs[key] = value  # add attribute regardless.
        return convertedAttribs

    def convert_attrib_value_using_spec_entries(self, value, entries):
        # first verify that entries is a list
        if not type(entries) == type(list()):
            entries = [entries]
        for entry in entries:
            if type(entry) == type:  # bool, str, int, etc...
                valueType = entry
                if valueType == bool:  # special handling for bool since bool('false') == True. Therefore we check if value is a false
                    if value in ['false', 'False', 'FALSE', b'false', b'False', b'FALSE']:
                        value = False
                        break
                value = valueType(value)  # convert value to new type
                break
            elif type(entry) == type(lambda x: x):  # if the entry is a function
                valueConverter = entry
                value = valueConverter(value)  # convert value using function
                break
            else:
                valueString = entry
                if valueString == value:
                    break
        else:  # little used else on a for loop: execute only if for loop wasn't broken
            raise ValueError  # value was not matched or converted by any entry
        return value

    def revert_attribs(self, mmElement):
        '''
        :param mmElement - contains the attribs to be reverted:
        using mmElements' specs, reverts attribs to string instances, validating that value are proper type. If a
        specific attribs' value is None, attrib will not be included
        if attrib is not in specs, attrib will not be included
        '''
        attribs = {key: value for key, value in mmElement.items() if value is not None}  # drop all None-valued attribs
        revertedAttribs = {}
        for key, value in attribs.items():
            if key not in mmElement.specs:
                continue  # skip adding attrib that isn't in specs
            entries = mmElement.specs[key]
            value = self.convert_attrib_value_using_spec_entries(value, entries)  # ? lowercase boolean output?
            key, value = str(key), str(value)
            revertedAttribs[key] = value
        return revertedAttribs


class NodeFactory(BaseElementFactory):
    elementType = Node
    childOrder = [BaseElement.tag, ArrowLink.tag, Cloud.tag, Edge.tag, Font.tag, Hook.tag, Properties.tag,
                  RichContent.tag, Icon.tag, Node.tag, AttributeLayout.tag, Attribute.tag]

    def finish_conversion(self, mmElement, parent=None):
        super(NodeFactory, self).finish_conversion(mmElement, parent)
        self.convert_node_text(mmElement)
        return mmElement

    def revert_to_etree_element(self, mmElement, parent=None):
        self.revert_node_text(mmElement)
        return super(NodeFactory, self).revert_to_etree_element(mmElement, parent)

    def revert_node_text(self, mmNode):
        ''' if node text is html, creates html child and appends to node's children '''
        ntext = NodeText()  # developer / user NEVER needs to create his own RichContent for mmNode html
        ntext.html = mmNode['TEXT']
        if ntext.is_html():
            mmNode.children.append(ntext)
            del mmNode['TEXT']  # using richcontent, do not leave attribute 'TEXT' for mmNode

    def convert_node_text(self, mmNode):
        ''' If node has html text, set to TEXT attribute to html object '''
        richElements = mmNode.findall('richcontent')
        while richElements:
            richElem = richElements.pop(0)
            if isinstance(richElem, NodeText):
                mmNode['TEXT'] = richElem.html
                mmNode.remove(richElem)  # this NodeText is no longer needed
                

class MapFactory(BaseElementFactory):
    elementType = Map

    def finish_reversion(self, etElement, parent=None):
        etMap = super(MapFactory, self).finish_reversion(etElement, parent)
        comment = ET.Comment('To view this file, download free mind mapping software Freeplane from ' +
                   'http://freeplane.sourceforge.net')
        comment.tail = '\n'
        etMap[:] = [comment] + etMap[:]
        return etMap

class CloudFactory(BaseElementFactory):
    elementType = Cloud

class HookFactory(BaseElementFactory):
    elementType = Hook
    typeVariants = [(EmbeddedImage, 'NAME', 'ExternalObject'),(MapConfig, 'NAME', 'MapStyle'),
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
    typeVariants = [(NodeText, 'TYPE', 'NODE'), (NodeNote, 'TYPE', 'NOTE'), (NodeDetails, 'TYPE', 'DETAILS')]

    def convert_from_etree_element(self, etElement, parent=None):
        mmRichC = super(RichContentFactory, self).convert_from_etree_element(etElement, parent)
        html = ''                                                       # this makes a critical assumption that there'll be 1 child. If not, upon
        for htmlElement in mmRichC.children:  # reversion, ET may complain about "ParseError: junk after document etRichC...
            htmlString = ET.tostring(htmlElement)
            if not type(htmlString) == str:  # I have once got back <class 'bytes'> when the string was a binary string. weird...
                htmlString = htmlString.decode('ascii')
            html += htmlString
        mmRichC.html = html
        mmRichC.children.clear()  # remove html children to prevent their conversion.
        return mmRichC

    def revert_to_etree_element(self, mmElement, parent=None):
        html = mmElement.html
        element = super(RichContentFactory, self).revert_to_etree_element(mmElement, parent)
        element.text = html  # temporarily store html string in element.text  (will convert in additional_reversion)
        return element

    def finish_reversion(self, etElement, parent=None):
        html = etElement.text
        etElement.text = '\n'
        etRichC = super(RichContentFactory, self).finish_reversion(etElement, parent)  # just sets tail...
        etRichC.append(ET.fromstring(html))  # this etRichC will have additional_reversion() called on it. It Should
        return etRichC                                          # have no effect, however.


class MindMapConverter:
    # pass this Converter a node to convert
    # and it will convert by choosing which factory to use in converting a given node
    # it is also tasked with non-recursively converting all nodes contained
    # within the first converted node.
    # you can add_factory(factory) if you have created a new node type / new factory to handle different features here

    def __init__(self, **kwargs):
        factorieClasses = [BaseElementFactory, NodeFactory, MapFactory, CloudFactory,
                     HookFactory, MapStylesFactory, StyleNodeFactory, FontFactory, IconFactory,
                     EdgeFactory, AttributeFactory, PropertiesFactory, RichContentFactory,
                     AttributeRegistryFactory]
        fff = [factory() for factory in factorieClasses]  # get an initialized instance of all factories
        self.tag2factory = {}
        for f in fff:            # get a dictionary that
            self.add_factory(f)  # matches an elements tag to the factory which can handle that element
        self.defaultFactory = BaseElementFactory()

    def add_factory(self, factory):
        ''' Add or Overwrite factory used for xml element. Specific to a tag specified by the factory's elementType

        :param factory: a pymm element factory
        '''
        if not isinstance(factory, object):  # if we are passed a non-initialized factory, create factory instance
            factory = factory()
        element = factory.elementType()
        self.tag2factory[element.tag] = factory

    def _apply_convert_fxns_to_full_tree(self, element, fxn1, fxn2):
        firstPassRoot = self._apply_first_pass_fxn_to_full_tree(element, fxn1)
        return self._apply_second_pass_fxn_to_full_tree(firstPassRoot, fxn2)

    def _apply_first_pass_fxn_to_full_tree(self, element, fxn1):
        first = fxn1(element, None)
        hasUnchangedChildren = [first]
        while hasUnchangedChildren:
            element = hasUnchangedChildren.pop(0)
            if isinstance(element, BaseElement):
                unchanged = [(child, element) for child in element.children]  # combine child w/ parent into tuple
            else:
                unchanged = [(child, element) for child in element[:]]  # xml.etree format
            children = []
            while unchanged:
                unchangedChild, parent = unchanged.pop(0)  # pop from first index to preserve child order
                child = fxn1(unchangedChild, parent)
                if child is None:
                    continue  # removes element from tree being built by not adding it to children(s) list
                children.append(child)
                hasUnchangedChildren.append(child)
            if isinstance(element, BaseElement):
                element.children = children  # pymm format
            else:
                element[:] = children  # xml.etree format
        return first
    

    def _apply_second_pass_fxn_to_full_tree(self, element, fxn2):
        first = element
        notFullyChanged = [(first, None)]  # child = first. Parent = None
        while notFullyChanged:
            element, parent = notFullyChanged.pop(0)
            elem = fxn2(element, parent)
            if elem is None and parent is not None:  # if you return None during conversion / reversion, this will ensure it is
                self._remove_child_element(elem, parent)  # fully removed from the tree by removing its reference from the
                continue  # parent and not allowing its children to be added
            parentsAndChildren = [(child, elem) for child in elem.getchildren()]  # child w/ parent
            notFullyChanged.extend(parentsAndChildren)
        return first

    def _remove_child_element(self, child, parent):
        if isinstance(parent, BaseElement):
            parent.children.remove(child)  # pymm format
        else:
            parent.remove(child)  # xml.etree format

    def convert_etree_element_and_tree(self, etElement):
        etElement = copy.deepcopy(etElement)
        action1 = self.convert_etree_element
        action2 = self.additional_conversion
        node = self._apply_convert_fxns_to_full_tree(etElement, action1, action2)
        self.defaultFactory.display_any_warnings()  # get this out so the developer is warned.
        return node

    def convert_etree_element(self, etElement, parent):
        ff = self.get_conversion_factory_for(etElement)
        node = ff.convert_from_etree_element(etElement, parent)
        return node

    def additional_conversion(self, mmElement, parent):
        ff = self.get_conversion_factory_for(mmElement)
        return ff.finish_conversion(mmElement, parent)

    def get_conversion_factory_for(self, element):  # intended for etElement or mmElement
        tag = element.tag
        if tag and tag in self.tag2factory:
            return self.tag2factory[tag]
        return self.defaultFactory

    def revert_mm_element_and_tree(self, mmElement):
        mmElement = copy.deepcopy(mmElement)
        action1 = self.revert_mm_element
        action2 = self.additional_reversion
        return self._apply_convert_fxns_to_full_tree(mmElement, action1, action2)

    def revert_mm_element(self, mmElement, parent):
        ff = self.get_conversion_factory_for(mmElement)
        return ff.revert_to_etree_element(mmElement, parent)

    def additional_reversion(self, etElement, parent):
        ff = self.get_conversion_factory_for(etElement)
        return ff.finish_reversion(etElement, parent)
