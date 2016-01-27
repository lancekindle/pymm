"""Factories are responsible for decoding xml.etree Elements into pymm
Elements and encoding pymm Elements back to xml.etree Elements. Factories are
where to specify how the encoding and decoding of an element is handled. Attrib
encoding/decoding is handled here as well
"""
import xml.etree.ElementTree as ET
import warnings
import copy
import re
import types
from uuid import uuid4
from . import element


def decode(elem):
    """This is the general function to call when you wish to decode an
    element and all its children and sub-children.
    Decode in this context means to convert from xml.etree.ElementTree
    elements to pymm elements.
    Typically this is called by pymm.read()
    """
    converter = ConversionHandler()
    return converter.convert_element_hierarchy(elem, 'decode')


def encode(elem):
    """This is the general function to call when you wish to encode an
    element and all its children and sub-children.
    Encode in this context means to convert from pymm elements to
    xml.etree.ElementTree elements.
    Typically this is called by pymm.write()
    """
    converter = ConversionHandler()
    return converter.convert_element_hierarchy(elem, 'encode')


class ConversionHandler:
    """Handle conversion of element and its children hierarchy. Will
    fully encode or decode a hierarchical tree of elements in a non-
    recursive manner (to avoid python recursion limits). Keep track of
    last-used factory-classes during encode/decode so that conversion
    errors may be noticeable.
    """
    last_encode = []
    last_decode = []

    def __init__(self):
        """Lock in set of factories for handling elements. If you
        create another element after instantiating ConversionHandler,
        get another instance to auto-generate a factory for that
        element. Otherwise, DefaultFactory will be used
        """
        self.factories = registry.get_factories()

    def find_encode_factory(self, elem):
        """return factory to handle given element. Since at init time
        of ConversionHandler, a factory is made for each pymm element,
        DefaultFactory will only be returned if there is an unhandled
        etree element, or a new pymm element is created after init-ing
        ConversionHandler. Factories is iterated from last to first,
        because the last factory is the newest and usually more
        specific factory.
        """
        for factory in reversed(self.factories):
            if factory.can_encode(elem):
                return factory
        return DefaultFactory

    def find_decode_factory(self, elem):
        """Return factory that can handle given element.
        Default to DefaultFactory
        """
        for factory in reversed(self.factories):
            if factory.can_decode(elem):
                return factory
        return DefaultFactory

    def convert_element_hierarchy(self, elem, convert):
        """encode or decode element and its hierarchy. Each element
        will be completely converted before its children begin the
        process
        """
        if convert == 'encode':
            self.last_encode.clear()
        if convert == 'decode':
            self.last_decode.clear()
        queue = [(None, [elem])]  # parent, children
        root = None
        while queue:
            parent, children = queue.pop(0)
            if root is None and parent is not None:
                root = parent
            for child in children:
                if convert == 'encode':
                    if not isinstance(child, element.BaseElement):
                        raise TypeError('cannot encode non-pymm element')
                    factory_class = self.find_encode_factory(child)
                    factory = factory_class()
                    child, grandchildren = factory.encode(parent, child)
                    self.last_encode.append(factory_class)
                elif convert == 'decode':
                    if isinstance(child, element.BaseElement):
                        raise TypeError('cannot decode pymm element')
                    factory_class = self.find_decode_factory(child)
                    factory = factory_class()
                    child, grandchildren = factory.decode(parent, child)
                    self.last_decode.append(factory_class)
                else:
                    raise ValueError('pass in "decode" or "encode"')
                # if convert fxn returns no decoded child, drop from hierarchy
                if child is not None:
                    queue.append((child, grandchildren))
        return root


class registry(type):
    """Metaclass to register all Factories created, and assist in
    creating new factories for unclaimed elements (elements without a
    corresponding factory
    """
    _factories = []
    verbose = False
    _skip_registration = ''

    @classmethod
    def get_factories(cls):
        factories = list(tuple(cls._factories))
        generated = cls.create_unclaimed_element_factories(factories)
        return factories + generated

    def __new__(mcs, clsname, bases, attr_dict):
        """create Factory-class, and register it in list of factories
        """
        FactoryClass = super().__new__(mcs, clsname, bases, attr_dict)
        # do not register factory if it was generated by this metaclass
        if clsname != mcs._skip_registration:
            mcs._factories.append(FactoryClass)
        return FactoryClass

    @classmethod
    def create_unclaimed_element_factories(cls, factories):
        """iterate all elements inheriting from Elements.BaseElement.
        For each element with no corresponding factory, create a factory
        to handle it, inheriting from closest-matching factory.
        Closest-matching factory is determined as the newest factory to
        use a decoding-element of which the unclaimed element is a
        subclass.

        Return list of all factories created in this way
        """
        generated = []
        for elem in element.registry.get_elements():
            closest_match = DefaultFactory
            for factory in factories:
                if issubclass(elem, factory.decoding_element):
                    closest_match = factory
                if factory.decoding_element == elem:
                    break
            else:
                # create factory for unclaimed element
                if cls.verbose:
                    print(
                        'unclaimed element:', elem,
                        '\n\t tag:', elem.tag,
                        '\n\t identifier:', elem.identifier,
                        '\n\t closest matching factory:', closest_match,
                    )
                element_name = getattr(elem, '__name__', elem.tag)
                name = element_name + '-Factory@' + uuid4().hex
                inherit_from = (closest_match,)
                variables = {'decoding_element': elem}
                cls._skip_registration = name
                new_factory = type(name, inherit_from, variables)
                generated.append(new_factory)
        return generated


class DefaultElementFactory:
    """Expose methods to construct encoding / decoding element class
    given attrib and children. At this point in the conversion process,
    the attribs are converted but the children are not.
    It is the responsibility of this factory to add the converted
    element to it's parent.
    """

    def decode_element(
            self, parent, src_element, element_class, attrib, children):
        """create decoded element using element_class and decoded
        attrib. The children are not yet decoded, however.
        DO NOT ADD CHILDREN TO ELEMENT! The children are not yet
        decoded. Instead you should add the newly instantiated element
        to the parent's children list
        """
        elem = element_class(**attrib)
        if parent is not None:
            parent.children.append(elem)
        elem.tag = getattr(src_element, 'tag', element_class.tag)
        elem._text = getattr(src_element, 'text', '')
        elem._tail = getattr(src_element, 'tail', '\n')
        return elem

    def encode_element(
            self, parent, src_element, element_class, attrib, children):
        """create encoded element using element_class and pre-encoded
        arguments attrib & children. This is the function in which
        to create an xml.etree Element
        DO NOT ADD CHILDREN TO ELEMENT! the children are not yet
        encoded. Instead you should add the newly encoded element as a
        child to the parent
        """
        tag = getattr(src_element, 'tag', 'unknown_element')
        elem = element_class(tag, **attrib)
        if parent is not None:
            parent.append(elem)
        elem.text = getattr(src_element, '_text', '')
        elem.tail = getattr(src_element, '_tail', '\n')
        # add spacing if element has child (makes file more readable)
        if len(elem) and not elem.text:
            elem.text = '\n'
        return elem


class DefaultAttribFactory:
    """expose methods to encode/decode attrib"""

    def decode_attrib(self, attrib, src_element, dst_element_class):
        """Decode attrib (from etree element) to match the spec in
        pymm element. Warn user (but still allow attrib) if attrib
        key/value pair is not valid.
        """
        spec = dst_element_class.spec
        decoded_attrib = {}
        # decoding from et element: assume all keys and values are strings
        for key, value in attrib.items():
            key = self.stringify(key)
            value = self.stringify(value)
            value = self.decode_attrib_value(key, value, spec)
            decoded_attrib[key] = value
        return decoded_attrib

    def decode_attrib_value(self, key, value, spec):
        """Spec values are lists that contain expected attrib values OR
        expected type of value (such as bool, int, or a custom class).
        Convert to expected type or verify that value matches one of
        corresponding spec value. If spec does not contain key, return
        value unaltered. Generate warning if value matched none of the
        spec values and/or could not be cast to type specified
        """
        entries = spec.get(key)
        if entries is None:
            return value
        if not isinstance(entries, list):
            raise ValueError('spec value must be a list of choices/types')
        # break out of for loop if match found
        for entry in entries:
            if entry == value:
                break
            if isinstance(entry, type):  # bool, str, int, custom class, etc...
                # special handling for finding false bool
                if issubclass(entry, bool):
                    if value in ['0', 'false', 'False', 'FALSE']:
                        value = False
                        break
                try:
                    value = entry(value)  # decode value to new type
                    break
                except:
                    warnings.warn(
                        key + ': ' + value + ' not of type ' + str(entry)
                    )
                    continue  # try next entry
        else:
            warnings.warn(key + ': ' + value + ' does not match spec')
        return value

    def encode_attrib(self, attrib, src_element, dst_element_class):
        """using src_element (pymm element) spec, decode (again)
        attrib to expected type. Then cast each key: value pair to
        string. If a particular value in spec is None, the key: value
        will be dropped from the encoded attrib.

        :param mmElement - pymm element containing attrib to be
        encoded
        """
        attrib = {
            key: value for key, value in attrib.items() if \
            value is not None
        }
        spec = src_element.spec
        encoded_attrib = {}
        for key, value in attrib.items():
            if key in spec:
                value = self.decode_attrib_value(key, value, spec)
            value = self.stringify(value)
            key = self.stringify(key)
            encoded_attrib[key] = value
        return encoded_attrib

    def stringify(self, arg):
        """If possible, decode into string, else cast arg to string"""
        if isinstance(arg, str):
            return arg
        try:
            return arg.decode('utf-8')
        except:
            return str(arg)


class DefaultGetAttributesFactory:
    """expose methods to get attrib and children from elements. This
    does NOT encode or decode the attrib or children, but instead
    simply returns the unaltered attribute (attrib or children)
    """

    def decode_getchildren(self, elem):
        """return list of children from xml.etree element"""
        return list(elem)

    def encode_getchildren(self, elem):
        """return list of children from pymm element. It is recommended
        to return a copied list of children, so that any modification
        to the list does not change the original element's children
        """
        return list(elem.children)

    def decode_getattrib(self, elem):
        """return attrib dict from xml.etree element"""
        return dict(elem.attrib)

    def encode_getattrib(self, elem):
        """return attrib dict from pymm element"""
        return dict(elem.attrib)



class DefaultChildFactory:
    """expose methods for retrieving list of children to encode/decode"""
    # order in which children will be written to file
    child_order = [
        element.BaseElement, element.Arrow, element.Cloud,
        element.Edge, element.Properties, element.MapStyles, element.Icon,
        element.AttributeLayout, element.Attribute, element.Hook,
        element.Font, element.StyleNode, element.RichContent, element.Node
    ]
    # order of nth to last for children. First node listed will be last child.
    reverse_child_order = []

    
class DefaultFactory(
        DefaultAttribFactory, DefaultElementFactory,
        DefaultGetAttributesFactory, metaclass=registry):
    """Factory with default methods for encoding and decoding between
    xml.ElementTree and pymm
    """
    decoding_element = element.BaseElement
    encoding_element = ET.Element

    def decode(self, parent, src_element):
        """control decode order from from xml.etree element to pymm
        element. Typical decoding order looks like:
        get_attrib, decode_attrib, get_children, decode_element
        """
        dst_element = self.decoding_element
        unaltered_attrib = self.decode_getattrib(src_element)
        attrib = self.decode_attrib(unaltered_attrib, src_element, dst_element)
        children = self.decode_getchildren(src_element)
        elem = self.decode_element(
            parent, src_element, dst_element, attrib, children
        )
        return elem, children

    def encode(self, parent, src_element):
        """control encode order from pymm element to xml.etree element.
        Typical encoding order looks like:
        get_children, get_attrib, encode_attrib, decode_element
        """
        dst_element = self.encoding_element
        children = self.encode_getchildren(src_element)
        unaltered_attrib = self.encode_getattrib(src_element)
        attrib = self.encode_attrib(unaltered_attrib, src_element, dst_element)
        elem = self.encode_element(
            parent, src_element, dst_element, attrib, children
        )
        return elem, children

    @classmethod
    def can_decode(cls, elem):
        """return False is element.tag does not equal decoding
        element's tag.
        If decoding_element has identifier, only
        return True if all key/value pairs of identifier regex match
        attrib key/value pair
        """
        if elem.tag != cls.decoding_element.tag:
            return False
        for key_id, val_id in cls.decoding_element.identifier.items():
            # return False if identifying key/val is not found in attrib
            for key, val in elem.attrib.items():
                if re.fullmatch(key_id, key) and re.fullmatch(val_id, val):
                    break
            else:
                return False
        return True

    @classmethod
    def can_encode(cls, elem):
        """return whether the factory can encode a given pymm element.
        Since there is always a factory made for each pymm element, we
        check that the factory exactly specifies the given element type
        """
        if elem.__class__ == cls.decoding_element:
            return True
        return False


class Node(DefaultFactory):
    decoding_element = element.Node
    child_order = [
        element.BaseElement, element.Arrow, element.Cloud,
        element.Edge, element.Font, element.Hook, element.Properties,
        element.RichContent, element.Icon, element.Node,
        element.AttributeLayout, element.Attribute
    ]

    def decode_attrib(self, attrib, src_element, dst_element_class):
        """Replace undesired parts of attrib with desired parts.
        specifically: look for occasional LOCALIZED_TEXT attrib which
        is supposed to be TEXT
        """
        swapout = [('TEXT', 'LOCALIZED_TEXT')]
        for desired, undesired in swapout:
            if desired not in attrib and undesired in attrib:
                attrib[desired] = attrib[undesired]
                del attrib[undesired]
        return super().decode_attrib(attrib, src_element, dst_element_class)

    def encode_getchildren(self, elem):
        """add attributes into children"""
        children = super().encode_getchildren(elem)
        for name, value in elem.items():
            child = element.Attribute(NAME=name, VALUE=value)
            children.append(child)
        return children


class Map(DefaultFactory):
    decoding_element = element.Map

    def encode_element(
            self, parent, src_element, element_class, attrib, children):
        elem = super().encode_element(
            parent, src_element, element_class, attrib, children)
        comment = ET.Comment(
            'To view this file, download free mind mapping software '
            + 'Freeplane from http://freeplane.sourceforge.net'
        )
        comment.tail = '\n'
        elem.append(comment)
        return elem

class Attribute(DefaultFactory):
    """Attribute is a visual 2-wide cell beneath a node. It has a name
    and value. We want to instead push this into the parent node as if
    it were a dictionary: parent[name] = value
    """
    decoding_element = element.Attribute

    def decode_element(
            self, parent, src_element, element_class, attrib, children):
        if not isinstance(parent, element.Node):
            return super().decode_element(
                parent, src_element, element_class, attrib, children)
        if 'NAME' in attrib and 'VALUE' in attrib:
            name = attrib['NAME']
            value = attrib['VALUE']
            parent[name] = value
        return None  # stop decoding this element and its children


class RichContent(DefaultFactory):
    decoding_element = element.RichContent

    def disabled_decode_element(
            self, parent, src_element, dst_element_class, attrib, children):
        html = ''
        for html_element in children:
            html_string = ET.tostring(html_element)
            if not isinstance(html_string, str):
                # I have once got back <class 'bytes'> when the string was a
                # binary string. weird...
                html_string = html_string.decode('ascii')
            html += html_string
        parent.text = html
        return None

    def disabled_encode_element(
            self, parent, src_element, dst_element_class, attrib, children):
        """until parent node creates a RichContent child, this will
        never trigger
        """
        elem = dst_element_class()
        elem.append(ET.fromstring(parent.text))
        parent.append(elem)
        elem.text = '\n'
        return elem


def sanity_check(pymm_element):
    """checks for common errors in pymm element and issues warnings
    for out-of-spec attrib
    """
    unchecked = [pymm_element]
    while unchecked:
        elem = unchecked.pop(0)
        unchecked.extend(elem.children)
        attrib = elem.attrib
        for key, allowed_values in elem.spec.items():
            if key in attrib:
                attribute = attrib[key]
                for allowed in allowed_values:
                    if attribute == allowed or isinstance(attribute, allowed):
                        break
                    # allow attribute if spec contains a function
                    if isinstance(allowed, types.BuiltinMethodType) or \
                            isinstance(allowed, types.LambdaType) or \
                            isinstance(allowed, types.MethodType) or \
                            isinstance(allowed, types.FunctionType) or \
                            isinstance(allowed, types.BuiltinFunctionType):
                        break
                else:
                    warnings.warn(
                        'out-of-spec attribute "' + str(attribute) +
                        ' in element: ' + str(elem.tag)
                    )
