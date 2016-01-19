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
from . import Elements


def decode(element):
    converter = ConversionHandler()
    return converter.convert_element_hierarchy(element, 'decode')


def encode(element):
    converter = ConversionHandler()
    return converter.convert_element_hierarchy(element, 'encode')


class ConversionHandler:

    def __init__(self):
        """Lock in set of factories for handling elements. If you
        create another element after instantiating ConversionHandler,
        get another instance to auto-generate a factory for that
        element. Otherwise, DefaultFactory will be used
        """
        self.factories = registry.get_factories()

    def find_encode_factory(self, element):
        for factory in reversed(self.factories):
            if factory.can_encode(element):
                return factory
        return DefaultFactory

    def find_decode_factory(self, element):
        """Return factory that can handle given element.
        Default to DefaultFactory
        """
        for factory in reversed(self.factories):
            if factory.can_decode(element):
                return factory
        return DefaultFactory

    def convert_element_hierarchy(self, element, convert):
        """encode or decode element and its hierarchy. Each element
        will be completely converted before its children begin the
        process
        """
        queue = [(None, [element])]  # parent, children
        root = None
        while queue:
            parent, children = queue.pop(0)
            if root is None and parent is not None:
                root = parent
            for child in children:
                if convert == 'encode':
                    factory_class = self.find_encode_factory(child)
                    factory = factory_class()
                    child, grandchildren = factory.encode(parent, child)
                elif convert == 'decode':
                    factory_class = self.find_decode_factory(child)
                    factory = factory_class()
                    child, grandchildren = factory.decode(parent, child)
                else:
                    raise ValueError('pass in "decode" or "encode"')
                # if convert fxn returns no decoded child, drop from hierarchy
                if child is not None:
                    queue.append((child, grandchildren))
        return root


class registry(type):
    """Metaclass to hold all factories created
    """
    _factories = []
    verbose = False
    # variable to keep track of generated factory name (don't add to factories)
    _generated_factory_name = ''

    @classmethod
    def get_factories(cls):
        factories = list(tuple(cls._factories))
        generated = cls.create_factories_for_unclaimed_elements(factories)
        return factories + generated

    def __new__(cls, clsname, bases, attr_dict):
        FactoryClass = super().__new__(cls, clsname, bases, attr_dict)
        if clsname != cls._generated_factory_name:
            cls._factories.append(FactoryClass)
        return FactoryClass

    @classmethod
    def create_factories_for_unclaimed_elements(cls, factories):
        """iterate all elements inheriting from Elements.BaseElement.
        For each element with no corresponding factory, create a factory
        to handle it, inheriting from closest-matching factory.
        Closest-matching factory is determined as the newest factory to
        use a decoding-element of which the unclaimed element is a
        subclass.

        Return list of all factories created in this way
        """
        generated = []
        for element in Elements.registry.get_elements():
            closest_match = DefaultFactory
            for factory in factories:
                if issubclass(element, factory.decoding_element):
                    closest_match = factory
                if factory.decoding_element == element:
                    break
            else:
                # create factory for unclaimed element
                if cls.verbose:
                    print(
                        'unclaimed element:', element,
                        '\n\t tag:', element.tag,
                        '\n\t identifier:', element.identifier,
                        '\n\t closest matching factory:', closest_match,
                    )
                name = 'Dynamic-'+ element.tag + '-Factory@' + uuid4().hex
                cls._generated_factory_name = name
                inherit_from = (closest_match,)
                variables = {'decoding_element': element}
                new_factory = type(name, inherit_from, variables)
                generated.append(new_factory)
        cls._accept_new_factories = True
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
        element = element_class(**attrib)
        if parent is not None:
            parent.children.append(element)
        element.tag = getattr(src_element, 'tag', element_class.tag)
        element._text = getattr(src_element, 'text', '')
        element._tail = getattr(src_element, 'tail', '\n')
        return element

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
        element = element_class(tag, **attrib)
        if parent is not None:
            parent.append(element)
        element.text = getattr(src_element, '_text', '')
        element.tail = getattr(src_element, '_tail', '\n')
        # add spacing if element has child (makes file more readable)
        if len(element) and not element.text:
            element.text = '\n'
        return element


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
            if isinstance(entry, type):  # bool, str, int, etc...
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
                        key + ': ' + value + 'not of type ' + str(entry)
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
            return arg.decode()
        except:
            return str(arg)


class DefaultGetAttributesFactory:
    """expose methods to get attrib and children from elements. This
    does NOT encode or decode the attrib or children, but instead
    simply returns the unaltered attribute (attrib or children)
    """

    def decode_getchildren(self, element):
        """return list of children from xml.etree element"""
        return list(element)

    def encode_getchildren(self, element):
        """return list of children from pymm element. It is recommended
        to return a copied list of children, so that any modification
        to the list does not change the original element's children
        """
        return list(element.children)

    def decode_getattrib(self, element):
        """return attrib dict from xml.etree element"""
        return dict(element.attrib)

    def encode_getattrib(self, element):
        """return attrib dict from pymm element"""
        return dict(element.attrib)



class DefaultChildFactory:
    """expose methods for retrieving list of children to encode/decode"""
    # order in which children will be written to file
    child_order = [
        Elements.BaseElement, Elements.ArrowLink, Elements.Cloud,
        Elements.Edge, Elements.Properties, Elements.MapStyles, Elements.Icon,
        Elements.AttributeLayout, Elements.Attribute, Elements.Hook,
        Elements.Font, Elements.StyleNode, Elements.RichContent, Elements.Node
    ]
    # order of nth to last for children. First node listed will be last child.
    reverse_child_order = []

    
class DefaultFactory(
        DefaultAttribFactory, DefaultElementFactory,
        DefaultGetAttributesFactory, metaclass=registry):
    """Factory with default methods for encoding and decoding between
    xml.ElementTree and pymm
    """
    decoding_element = Elements.BaseElement
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
        element = self.decode_element(
            parent, src_element, dst_element, attrib, children
        )
        return element, children

    def encode(self, parent, src_element):
        """control encode order from pymm element to xml.etree element.
        Typical encoding order looks like:
        get_children, get_attrib, encode_attrib, decode_element
        """
        dst_element = self.encoding_element
        children = self.encode_getchildren(src_element)
        unaltered_attrib = self.encode_getattrib(src_element)
        attrib = self.encode_attrib(unaltered_attrib, src_element, dst_element)
        element = self.encode_element(
            parent, src_element, dst_element, attrib, children
        )
        return element, children

    @classmethod
    def can_decode(cls, element):
        """return False is element.tag does not equal decoding
        element's tag.
        If decoding_element has identifier, only
        return True if all key/value pairs of identifier regex match
        attrib key/value pair
        """
        if element.tag != cls.decoding_element.tag:
            return False
        for key_id, val_id in cls.decoding_element.identifier.items():
            # return False if identifying key/val is not found in attrib
            for key, val in element.attrib.items():
                if re.fullmatch(key_id, key) and re.fullmatch(val_id, val):
                    break
            else:
                return False
        return True

    @classmethod
    def can_encode(cls, element):
        if isinstance(element, cls.decoding_element):
            return True
        return False


class NodeFactory(DefaultFactory):
    decoding_element = Elements.Node
    child_order = [
        Elements.BaseElement, Elements.ArrowLink, Elements.Cloud,
        Elements.Edge, Elements.Font, Elements.Hook, Elements.Properties,
        Elements.RichContent, Elements.Icon, Elements.Node,
        Elements.AttributeLayout, Elements.Attribute
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

    def encode_getchildren(self, element):
        """add attributes into children"""
        children = super().encode_getchildren(element)
        for name, value in element.items():
            child = Elements.Attribute(NAME=name, VALUE=value)
            children.append(child)
        return children


class MapFactory(DefaultFactory):
    decoding_element = Elements.Map

    def encode_element(
            self, parent, src_element, element_class, attrib, children):
        element = super().encode_element(
            parent, src_element, element_class, attrib, children)
        comment = ET.Comment(
            'To view this file, download free mind mapping software '
            + 'Freeplane from http://freeplane.sourceforge.net'
        )
        comment.tail = '\n'
        element.append(comment)
        return element

class AttributeFactory(DefaultFactory):
    """Attribute is a visual 2-wide cell beneath a node. It has a name
    and value. We want to instead push this into the parent node as if
    it were a dictionary: parent[name] = value
    """
    decoding_element = Elements.Attribute

    def decode_element(
            self, parent, src_element, element_class, attrib, children):
        if not isinstance(parent, Elements.Node):
            return super().encode_element(
                parent, src_element, element_class, attrib, children)
        if 'NAME' in attrib and 'VALUE' in attrib:
            name = attrib['NAME']
            value = attrib['VALUE']
            parent[name] = value
        return None  # stop decoding this element and its children


class RichContentFactory(DefaultFactory):
    decoding_element = Elements.RichContent

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
        element = dst_element_class()
        element.append(ET.fromstring(parent.text))
        parent.append(element)
        element.text = '\n'
        return element


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
