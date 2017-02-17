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
from . import element
from .registry import FactoryRegistry as registry


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
    errors may be traceable
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
        """Return factory that can handle given element. Limit
        information passed to can_decode to just tag and attrib.
        Default to DefaultFactory
        """
        tag, attrib = elem.tag, elem.attrib.copy()
        for factory in reversed(self.factories):
            if factory.can_decode(tag, attrib):
                return factory
        return DefaultFactory

    def convert_element_hierarchy(self, elem, convert):
        """encode or decode element and its hierarchy. Each element
        will be completely converted before its children begin the
        process
        """
        is_encoding = False
        if convert == 'encode':
            if not isinstance(elem, element.BaseElement):
                raise TypeError('cannot encode non-pymm element')
            is_encoding = True
            self.last_encode.clear()
            self.convert_notify(elem, 'pre_encode')
        elif convert == 'decode':
            if isinstance(elem, element.BaseElement):
                raise TypeError('cannot decode pymm element')
            self.last_decode.clear()
        else:
            raise ValueError('pass in "decode" or "encode"')
        queue = [(None, [elem])]  # parent, children
        root = None
        while queue:
            parent, children = queue.pop(0)
            if root is None and parent is not None:
                root = parent
            for child in children:
                if is_encoding:
                    if not isinstance(child, element.BaseElement):
                        raise TypeError('cannot encode non-pymm element')
                    factory_class = self.find_encode_factory(child)
                    factory = factory_class()
                    child, grandchildren = factory.encode(parent, child)
                    self.last_encode.append(factory_class)
                else:
                    if isinstance(child, element.BaseElement):
                        raise TypeError('cannot decode pymm element')
                    factory_class = self.find_decode_factory(child)
                    factory = factory_class()
                    child, grandchildren = factory.decode(parent, child)
                    self.last_decode.append(factory_class)
                # if convert fxn returns no decoded child, drop from hierarchy
                if child is not None:
                    grandchildren = list(grandchildren)
                    queue.append((child, grandchildren))
        if is_encoding:
            self.convert_notify(elem, 'post_encode')
        else:
            self.convert_notify(root, 'post_decode')
        return root

    def convert_notify(self, elem, alert_type):
        """alert element and all its children about impending
        conversion. Will trigger pre_encode, post_encode, or
        post_decode on elem and hierarchy, in breadth-first-search
        style. All alerts will be done on pymm elements
        """
        if alert_type == 'pre_encode' or alert_type == 'post_encode' or \
                alert_type == 'post_decode':
            pass
        else:
            raise ValueError('must give a post-or-pre encode/decode string')
        queue = [(None, [elem])]
        while queue:
            parent, children = queue.pop(0)
            for child in children:
                factory_class = self.find_encode_factory(child)
                factory = factory_class()
                default = lambda *x: None
                conversion_notify = getattr(factory, alert_type, default)
                conversion_notify(child, parent)
                # copy prevents .children manipulation from ruining iteration
                # if child removed itself from .children list, the above
                # iteration would abort prematurely
                grandchildren = child.children.copy()
                queue.append((child, grandchildren))


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
            tag = dst_element_class.tag
            value = self.match_attrib_value_to_spec(key, value, spec, tag)
            decoded_attrib[key] = value
        return decoded_attrib

    @staticmethod
    def match_attrib_value_to_spec(key, value, spec, tag=''):
        """Each pymm element has a .spec dict which specifies expected
        types (such as int or str) or expected values of a given attrib
        key/value pair.  This function attempts to conform the attrib
        value to the expected values/types given by spec.  Aka: convert
        value to expected type or verify that value matches one of
        spec's corresponding values.  If spec does not contain key,
        return value unaltered.  Generate warning if value matches none
        of spec's values and/or cannot be cast to available types
        """
        if key not in spec:
            return value
        entries = spec[key]
        if not isinstance(entries, list):
            raise ValueError('spec value must be a list of choices/types')
        for entry in entries:
            if entry == value:
                return value
            if not isinstance(entry, type):
                continue
            # handle special bool conversion, where any non-empty string
            # is considered true, but 'false' or '0' should be false
            if issubclass(entry, bool):
                if value in ['0', 'false', 'False', 'FALSE']:
                    return False
            try:
                # convert value to type
                return entry(value)
            except:
                continue
        key, val = str(key), str(value)
        warnings.warn(tag + '-> ' + key + ': ' + val + " doesn't match spec")
        return value

    def encode_attrib(self, attrib, src_element, dst_element_class):
        """using src_element (pymm element) spec, decode (again)
        attrib to expected type. Then cast each key: value pair to
        string. If a particular value in spec is None, the key: value
        will be dropped from the encoded attrib.

        :param mmElement - pymm element containing attrib to be
        encoded
        """
        attrib = {key: val for key, val in attrib.items() if val is not None}
        spec = src_element.spec
        encoded_attrib = {}
        for key, value in attrib.items():
            tag = src_element.tag
            value = self.match_attrib_value_to_spec(key, value, spec, tag)
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
    def can_decode(cls, tag, attrib):
        """Return whether factory can decode given element. Tag and
        attrib of element are passed to this function. To verify,
        compare tag and attrib to this factory's decoding_element .tag
        and .identifier Return False immediately if element.tag does not
        equal decoding element's tag. Otherwise, only return True if
        each key/value
        pair in decoding_element.identifier can regex-match at least
        one key/value pair from element.attrib
        """
        decodee = cls.decoding_element
        if tag != decodee.tag:
            return False
        for key_regex, val_regex in decodee.identifier.items():
            matching_attrib = (
                re.fullmatch(key_regex, key) and re.fullmatch(val_regex, val) \
                for key, val in attrib.items()
            )
            if not any(matching_attrib):
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
