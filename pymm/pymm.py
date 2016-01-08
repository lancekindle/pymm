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
    similar in structure but has different syntax aimed at making development
    easy and clear to those new and experienced with Freeplane.
"""
import xml.etree.ElementTree as ET
import os
import warnings
import types
from . import Elements
from . import Factories

# import most-likely to be used Elements
from .Elements import Node, Cloud, Icon, Edge, ArrowLink


def sanity_check(pymm_element):
    """checks for common errors in pymm element and issues warnings
    for out-of-spec attrib
    """
    unchecked = [pymm_element]
    while unchecked:
        elem = unchecked.pop(0)
        unchecked.extend(elem.children)
        attrib = elem.attrib
        for key, allowed_values in elem.specs.items():
            if key in attrib:
                attribute = attrib[key]
                for allowed in allowed_values:
                    if attribute == allowed or isinstance(attribute, allowed):
                        break
                    # allow attribute if specs contains converter fxn
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


def read(file_or_filename):
    """convert the file/filename into a pymm tree. User should expect to use
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
    tree = ET.parse(file_or_filename)
    et_elem = tree.getroot()
    mm_elem = convert(et_elem)  # should return MindMap instance
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
    et_elem = revert(mm_element)
    xmltree = ET.ElementTree(et_elem)
    xmltree.write(file_or_filename)


def convert(et_element):
    """Convert ElementTree Element to pymm Element. Temporarily sets
    converter factory to use MindMap instead of Elements.Map

    :param et_element: Element Tree Element -> generally an element from
                       python's xml.etree.ElementTree module
    :return: Pymm hierarchical tree. Usually MindMap instance but may return
             BaseElement-inheriting element if et_element was not complete
             mindmap hierarchy.
    """
    mmc = Factories.MindMapConverter()
    mm_factory = Factories.MapFactory()
    mm_factory.elementType = MindMap
    mmc.add_factory(mm_factory)
    return mmc.convert_etree_element_and_tree(et_element)


def revert(mm_element):
    """Revert pymm Element to ElementTree Element

    :param mm_element: pymm Element from pymm.Elements module
    :return: xml.etree version of passed pymm tree
    """
    if not isinstance(mm_element, Elements.BaseElement):
        raise ValueError('cannot revert mm_element: it is not a pymm element')
    mmc = Factories.MindMapConverter()
    return mmc.revert_mm_element_and_tree(mm_element)


class MindMap(Elements.Map):
    """Interface to Freeplane structure. Allow reading and writing of xml
    mindmap formats (.mm)

    some properties inherited from Elements.Map that will prove useful:
    root - set/get the MindMap's only child node
    """
    filename = None
    mode = 'r'
    _load_default_mindmap_flag = True

    def __new__(cls, *args, **attrib):
        """FreeplaneFile acts as an interface to intrepret
        xml-based .mm files into a tree of Nodes.
        if MindMap is created with no arguments, a default hierarchy
        will be loaded. Otherwise it may load the specified file
        """
        if not args:
            if cls._load_default_mindmap_flag:
                return cls._load_default_mindmap(**attrib)
        else:
            # we assume that user has passed in file-reading options
            if len(args) > 3:
                raise ValueError(
                    'MindMap expects at most 2 arguments specifying filename' +
                    ' and mode. Got ' + str(len(args))
                )
            # use default filemode if none supplied
            filename, mode, *_ = list(args) + [cls.mode]
            if 'r' in mode and 'w' in mode:
                raise ValueError('must have exactly one of read/write mode')
            if 'r' in mode:
                self = read(filename)
            elif 'w' in mode:
                self = cls._load_default_mindmap(**attrib)
            else:
                raise ValueError('unknown mode: ' + str(mode))
            self.filename = filename
            self.mode = mode
            return self
        return super().__new__(cls)

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def _load_default_mindmap(cls, **attrib):
        """create default hierarchy for mindmap -- including map_styles and
        Automatic node coloring hook
        """
        try:
            cls._load_default_mindmap_flag = False
            filepath = os.path.realpath(__file__)
            path, _ = os.path.split(filepath)
            filename = os.path.join(path, 'defaultmm')
            self = cls.__new__(cls, filename, **attrib)
            cls._load_default_mindmap_flag = True
        except:
            cls._load_default_mindmap_flag = True
            raise
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        for arg in args:
            if arg is not None:  # then we have an error????
                return  # skip saving step then
        # write self tree to file when exiting if filemode indicates
        # 'write-mode'
        if 'w' in self.mode:
            write(self.filename, self)

