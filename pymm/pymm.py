"""
    Pymm is a module dedicated towards easing the development and parsing of
    mindmaps built with or for Freeplane. Freeplane is a graphical
    "spider-diagram" interface that allows one to build mindmaps; a
    hierarchical tree of nodes, where each node contains some text, and parent
    nodes can be "folded" to hide their child nodes. Pymm can read or write
    Freeplane's file format: an xml-file with a .mm extension. Because
    Freeplane's files are xml formatted, Pymm uses Python's built-in
    xml.etree library to parse the file, and then decodes the generated tree
    structure into Pymm's version of the tree, using Pymm's Elements instead.
    The structure of the Pymm's tree (as opposed to xml.etree's version) is
    similar but has different syntax aimed at making development
    easy and clear to those new and experienced with Freeplane.
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


def read(file_or_filename):
    """decode the file/filename into a pymm tree. User should expect to use
    this module-wide function to decode a freeplane file (.mm) into a pymm
    tree. If file specified is a fully-formed mindmap, the user should expect
    to receive a Mindmap instance. Calling .getroot() on that should get
    the user the first node in the tree structure.

    :param file_or_filename: string path to file or file instance of mindmap
    :return: If the file passed was a full mindmap, will return Mindmap
             instance, otherwise if file represents an incomplete mindmap, it
             will pass the instance of the top-level element, which could be
             BaseElement or any inheriting element in the Elements module.
    """
    # must lock default_mindmap_filename
    with file_locked(file_or_filename), \
            file_locked(Mindmap.default_mindmap_filename):
        tree = ET.parse(file_or_filename)
        et_elem = tree.getroot()
        pymm_elem = decode(et_elem)
    return pymm_elem


def write(file_or_filename, pymm_element):
    """Writes mindmap/element to file. Element must be pymm element.
    Will write element and children hierarchy to file.
    Writing any element to file works, but in order to be opened
    in Freeplane, the Mindmap element should be passed.

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
    configure a pymm element post-decode. If called with an element, instead
    decode the supplied element and return it's decoded state
    """

    def __new__(cls, et_element):
        """decode ElementTree Element to pymm Element.

        :param et_element: Element Tree Element -> generally an element from
                           python's xml.etree.ElementTree module
        :return: Pymm hierarchical tree. Usually Mindmap instance but may return
                 BaseElement-inheriting element if et_element was not complete
                 mindmap hierarchy.
        """
        if isinstance(et_element, element.BaseElement):
            raise ValueError('cannot decode a pymm element')
        return factory.decode(et_element)

    @classmethod
    def post_decode(cls, fxn):
        return _decode.post_decode(fxn)


class encode:
    """function-like class that allows decorating of functions to
    configure a pymm element post-decode. If called with an element, instead
    decode the supplied element and return it's decoded state
    """

    def __new__(cls, pymm_element):
        """encode pymm Element to ElementTree Element

        :param mm_element: pymm Element from pymm.Elements module
        :return: xml.etree version of passed pymm tree
        """
        if not isinstance(pymm_element, element.BaseElement):
            raise ValueError('encoding requires a pymm element')
        return factory.encode(pymm_element)
    
    @classmethod
    def pre_encode(cls, fxn):
        return _encode.pre_encode(fxn)

    @classmethod
    def post_encode(cls, fxn):
        return _encode.post_encode(fxn)

    @classmethod
    def get_attrib(cls, fxn):
        return _encode.get_attrib(fxn)

    @classmethod
    def get_children(cls, fxn):
        return _encode.get_children(fxn)


class file_locked:
    """function-like class to allow boolean checking if a given
    filename is locked or not. If used as a context manager, file is
    marked as locked until context exit. This is intended to be used by
    pymm.read to signify when reading from file, and by Mindmap to load
    it's default hierarchy only if a file is not currently loading
    """
    locked = defaultdict(bool)
    file_to_lock = None

    def __init__(self, file_to_lock):
        self.file_to_lock = file_to_lock

    def __bool__(self):
        return self.locked[self.file_to_lock]

    def __enter__(self, *_):
        """set lock on file to True"""
        self.locked[self.file_to_lock] = True
        return self

    def __exit__(self, *error):
        """reset lock on file to False"""
        self.locked[self.file_to_lock] = False


class Mindmap(element.Map):
    """Interface to Freeplane structure. Allow reading and writing of xml
    mindmap formats (.mm)

    some properties inherited from Elements.Map that will prove useful:
    root - set/get the Mindmap's only child node
    """
    filename = None
    mode = 'r'
    # identify default mindmap filename
    filepath = os.path.realpath(__file__)
    path, _ = os.path.split(filepath)
    filename = os.path.join(path, 'defaultmm')
    default_mindmap_filename = filename
    del _, path, filepath

    def __new__(cls, *args, **attrib):
        """FreeplaneFile acts as an interface to intrepret
        xml-based .mm files into a tree of Nodes.
        if Mindmap is created with no arguments, a default hierarchy
        will be loaded. Any non-keyword arguments are assumed to be
        filename and mode, respectively. Mindmap will load the file
        specified. If mode is 'w', A default hierarchy will be loaded.
        Opening a file in write mode is only useful as if Mindmap is
        used as a context manager. The file will be written after
        context manager exits, if no errors caused an early exit.
        with Mindmap(filename, 'w') as mm:
            etc...
        # mm written to filename
        """
        if not args:
            if not file_locked(cls.default_mindmap_filename):
                return cls.default_mindmap(**attrib)
        else:
            # we assume that user has passed in file-reading options
            if len(args) > 2:
                raise ValueError(
                    'Mindmap expects at most 2 arguments specifying filename' +
                    ' and mode. Got ' + str(len(args))
                )
            # use default filemode (read) if none supplied
            filename, mode, *_ = list(args) + ['r']
            if 'r' in mode and 'w' in mode:
                raise ValueError('must have exactly one of read/write mode')
            if 'r' in mode:
                self = read(filename)
            elif 'w' in mode:
                self = cls.default_mindmap(**attrib)
            else:
                raise ValueError('unknown mode: ' + str(mode))
            self.filename = filename
            self.mode = mode
            return self
        return super().__new__(cls)

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def default_mindmap(cls, **attrib):
        """load default hierarchy for mindmap -- including map_styles
        and automatic node coloring hook. Loads file by re-initiating
        class with arguments to load default hierarchy file.
        """
        return cls.__new__(cls, cls.default_mindmap_filename, **attrib)

    def __enter__(self):
        """allow user to use Mindmap as context-manager, in which Mindmap can
        take filename and a mode as seen in __init__. If set to write mode 'w',
        then upon exit Mindmap will write to file given
        """
        return self

    def __exit__(self, *error):
        """on context-manager exit, write to file REGARDLESS of errors
        if mode is 'w'
        """
        if 'w' in self.mode:
            write(self.filename, self)
