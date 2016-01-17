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
from . import Elements
from . import Factories

# import most-likely to be used Elements
from .Elements import Node, Cloud, Icon, Edge, ArrowLink


def read(file_or_filename):
    """decode the file/filename into a pymm tree. User should expect to use
    this module-wide function to decode a freeplane file (.mm) into a pymm
    tree. If file specified is a fully-formed mindmap, the user should expect
    to receive a MindMap instance. Calling .getroot() on that should get
    the user the first node in the tree structure.

    :param file_or_filename: string path to file or file instance of mindmap
    :return: If the file passed was a full mindmap, will return MindMap
             instance, otherwise if file represents an incomplete mindmap, it
             will pass the instance of the top-level element, which could be
             BaseElement or any inheriting element in the Elements module.
    """
    # must lock default_mindmap_filename
    with file_locked(file_or_filename), \
            file_locked(MindMap.default_mindmap_filename):
        tree = ET.parse(file_or_filename)
        et_elem = tree.getroot()
        mm_elem = decode(et_elem)
    return mm_elem


def write(file_or_filename, mm_element):
    """Writes mindmap/element to file. Element must be pymm element.
    Will write element and children hierarchy to file.
    Writing any element to file works, but in order to be opened
    in Freeplane, the MindMap element should be passed.

    :param mm_element: MindMap or other pymm element
    :param file_or_filename: string path to file or file instance
        of mindmap (.mm)
    :return:
    """
    if not isinstance(mm_element, Elements.BaseElement):
        raise ValueError(
            'pymm.write requires file/filename, then pymm element'
        )
    et_elem = encode(mm_element)
    xmltree = ET.ElementTree(et_elem)
    xmltree.write(file_or_filename)


def decode(et_element):
    """decode ElementTree Element to pymm Element.

    :param et_element: Element Tree Element -> generally an element from
                       python's xml.etree.ElementTree module
    :return: Pymm hierarchical tree. Usually MindMap instance but may return
             BaseElement-inheriting element if et_element was not complete
             mindmap hierarchy.
    """
    return Factories.decode(et_element)


def encode(mm_element):
    """encode pymm Element to ElementTree Element

    :param mm_element: pymm Element from pymm.Elements module
    :return: xml.etree version of passed pymm tree
    """
    if not isinstance(mm_element, Elements.BaseElement):
        raise ValueError('cannot encode mm_element: it is not a pymm element')
    return Factories.encode(mm_element)


class file_locked:
    """function-like class to allow boolean checking if a given
    filename is locked or not. If used as a context manager, file is
    marked as locked until context exit. This is intended to be used by
    pymm.read to signify when reading from file, and by MindMap to load
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


class MindMap(Elements.Map):
    """Interface to Freeplane structure. Allow reading and writing of xml
    mindmap formats (.mm)

    some properties inherited from Elements.Map that will prove useful:
    root - set/get the MindMap's only child node
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
        if MindMap is created with no arguments, a default hierarchy
        will be loaded. Any non-keyword arguments are assumed to be
        filename and mode, respectively. MindMap will load the file
        specified. If mode is 'w', A default hierarchy will be loaded.
        Opening a file in write mode is only useful as if MindMap is
        used as a context manager. The file will be written after
        context manager exits, if no errors caused an early exit.
        with MindMap(filename, 'w') as mm:
            etc...
        # mm written to filename
        """
        if not args:
            if not file_locked(cls.default_mindmap_filename):
                return cls.default_mindmap(**attrib)
        else:
            # we assume that user has passed in file-reading options
            if len(args) > 3:
                raise ValueError(
                    'MindMap expects at most 2 arguments specifying filename' +
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
        """allow user to use MindMap as context-manager, in which MindMap can
        take filename and a mode as seen in __init__. If set to write mode 'w',
        then upon exit MindMap will write to file given
        """
        return self

    def __exit__(self, *error):
        """on context-manager exit, write to file IF no errors occurred and
        mode is 'w'
        """
        if error == (None, None, None):
            if 'w' in self.mode:
                write(self.filename, self)
