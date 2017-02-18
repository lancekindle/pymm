"""
    Pymm is a module dedicated towards easing the development and
    parsing of mindmaps built with or for Freeplane. Freeplane is a
    graphical "spider-diagram" interface that allows one to build
    mindmaps; a hierarchical tree of nodes, where each node contains
    some text, and parent nodes can be "folded" to hide their child
    nodes. Pymm can read or write Freeplane's file format: an xml-file
    with a .mm extension. Because Freeplane's files are xml formatted,
    Pymm uses Python's built-in xml.etree library to parse the file, and
    then decodes the generated tree structure into Pymm's version of the
    tree, using Pymm's Elements instead. The structure of the Pymm's
    tree (as opposed to xml.etree's version) is similar but has
    different syntax aimed at making development easy and clear to those
    new and experienced with Freeplane.
"""
import xml.etree.ElementTree as ET
import os
import warnings
import types
from collections import defaultdict
from . import element
from . import factory
from . import decode as _decode
from . import encode as _encode

# import most-likely to be used Elements
from .element import Node, Cloud, Icon, Edge, Arrow


class Mindmap:
    """create a new instance of Mindmap to load a default mindmap
    hierarchy. This'll return a Map() instance with a single root node,
    exactly as you'd get when starting with a blank mindmap within
    Freeplane
    """
    # identify default mindmap filename
    filepath = os.path.realpath(__file__)
    path, _ = os.path.split(filepath)
    filename = os.path.join(path, 'defaultmm')
    blank_mindmap_filename = filename
    del _, path, filepath

    def __new__(cls):
        """Instantiate a new, default mindmap by loading the default
        file.
        """
        return read(cls.blank_mindmap_filename)


def read(file_or_filename):
    """decode the file/filename into a pymm tree. User should expect to
    use this module-wide function to decode a freeplane file (.mm) into
    a pymm tree. If file specified is a fully-formed mindmap, the user
    should expect to receive a Map instance. Accessing element.root on
    that should get the user the first node (root node) in the mindmap

    :param file_or_filename: string path to file or file instance of
                             mindmap
    :return: If the file passed was a full mindmap, will return Map
             instance, otherwise if file represents an incomplete
             mindmap, it will pass the instance of the top-level
             element, which could be BaseElement or any inheriting
             element in the Elements module.
    """
    tree = ET.parse(file_or_filename)
    et_elem = tree.getroot()
    pymm_elem = decode(et_elem)
    return pymm_elem


def write(file_or_filename, pymm_element):
    """Writes mindmap/element to file. Element must be pymm element.
    Will write element and children hierarchy to file.
    Writing any element to file works, but in order to be opened
    in Freeplane, the Map element should be passed.

    :param mm_element: Mindmap or other pymm element
    :param file_or_filename: string path to file or file instance
        of mindmap (.mm)
    :return:
    """
    if not isinstance(pymm_element, element.BaseElement):
        raise ValueError(
            'pymm.write requires file/filename, then pymm element'
        )
    et_elem = encode(pymm_element)
    xmltree = ET.ElementTree(et_elem)
    xmltree.write(file_or_filename)


class decode:
    """function-like class that allows decorating of functions to
    configure a pymm element post-decode. If instead called with an
    ElementTree element, decode the supplied element and return it's
    decoded state (as a Pymm Element)
    """

    def __new__(cls, et_element):
        """decode ElementTree Element to pymm Element.

        :param et_element: Element Tree Element -> generally an element
                           from python's xml.etree.ElementTree module
        :return: Pymm hierarchical tree. Usually Mindmap instance but
                 may return BaseElement-inheriting element if
                 et_element was not complete mindmap hierarchy.
        """
        if isinstance(et_element, element.BaseElement):
            raise ValueError('cannot decode a pymm element')
        return factory.decode(et_element)

    @staticmethod
    def post_decode(fxn):
        """each element's function decorated with decode.post_decode
        will be called after a freeplane mindmap has been decoded into
        the pymm hierarchy. The function will be called with the
        element's parent as the only argument (aside from the implicit
        self). An example element with decorated fxn below:

        class custom_node(pymm.Node):
            @pymm.decode.post_decode
            def after_decoding(self, parent):
                blahblahblah

        Since this is called just after decoding and before the element is
        handled by the user, this can be used for correcting small
        deficiencies in an element (such as unexpected attrib key:
        values or undesirable children) before it gets manipulated by
        user code.
        """
        _decode.post_decode(fxn)
        return fxn


class encode:
    """function-like class that allows decorating of functions to
    configure a pymm element post/pre-encode, which includes the ability
    to manipulate which children and/or attrib get encoded into the
    final mindmap file. If called with an element, instead encode the
    supplied element and return it's encoded state
    """

    def __new__(cls, pymm_element):
        """encode pymm Element to ElementTree Element

        :param mm_element: pymm Element from pymm.Elements module
        :return: xml.etree version of passed pymm tree
        """
        if not isinstance(pymm_element, element.BaseElement):
            raise ValueError('encoding requires a pymm element')
        return factory.encode(pymm_element)

    @staticmethod
    def get_children(fxn):
        """each element's function decorated with encode.get_children
        will be called while a pymm hierarchy is being encoded into
        a freeplane file. The function will be called with no arguments
        (aside from the implicit self). An example element with
        decorated fxn below:

        class CloudedNode(pymm.Node):
            @pymm.encode.get_children
            def add_cloud_child(self, parent):
                children = list(self.children)
                return children + [pymm.Cloud()]

        You should return a list of children. Typically this is a
        modified list of self.children. Remember to perform a
        `children = list(self.children)` to create a new temporary list
        with which you may add/remove children without changing the
        element's children
        """
        _encode.get_children(fxn)
        return fxn

    @staticmethod
    def get_attrib(fxn):
        """each element's function decorated with encode.get_attrib
        will be called while a pymm hierarchy is being encoded into
        a freeplane file. The function will be called with no arguments
        (aside from the implicit self). An example element with
        decorated fxn below:

        class BoldedNode(pymm.Node):
            @pymm.encode.get_attrib
            def boldify_text(self, parent):
                attrib = dict(self.attrib)
                text = attrib['TEXT']
                attrib['TEXT'] = '<b>' + text + '</b>'
                return attrib

        You should return a dict of attribs. Typically this is a
        modified dict of self.attrib. Remember to perform a
        `attrib = dict(self.attrib)` to create a new temporary dict
        which you may modify without changing the element's attrib
        """
        _encode.get_attrib(fxn)
        return fxn

    @staticmethod
    def pre_encode(fxn):
        """each element's function decorated with encode.pre_encode
        will be called before a pymm hierarchy is encoded into
        a freeplane file. The function will be called with the
        element's parent as the only argument (aside from the implicit
        self). An example element with decorated fxn below:

        class CustomNode(pymm.Node):
            @pymm.encode.pre_encode
            def before_encoding(self, parent):
                blahblahblah

        Since this is called just before encoding, this can be used (in
        conjunction with post_encode) to add / remove siblings or edit
        nearby element's properties. Just be aware that post/pre_encode
        may or may not get called on these elements depending on
        how/when you add/remove them. If you wish to temporarily edit
        this element's own children or attrib, it's recommended to
        decorate with the more specific @encode.get_children and
        @encode.get_attrib. In each of those, you simply return the
        desired list of children or dict of attributes, respectively.
        """
        _encode.pre_encode(fxn)
        return fxn

    @staticmethod
    def post_encode(fxn):
        """each element's function decorated with encode.post_encode
        will be called after a pymm hierarchy is encoded into
        a freeplane file. The function will be called with the
        element's parent as the only argument (aside from the implicit
        self). An example element with decorated fxn below:

        class CustomNode(pymm.Node):
            @pymm.encode.post_encode
            def after_encoding(self, parent):
                blahblahblah

        Since this is called just after encoding, this can be used (in
        conjunction with pre_encode) to add / remove siblings or edit
        nearby element's properties. Just be aware that post/pre_encode
        may or may not get called on these elements depending on
        how/when you add/remove them. If you wish to temporarily edit
        this element's own children or attrib, it's recommended to
        decorate with the more specific @encode.get_children and
        @encode.get_attrib. In each of those, you simply return the
        desired list of children or dict of attributes, respectively.
        """
        _encode.post_encode(fxn)
        return fxn
