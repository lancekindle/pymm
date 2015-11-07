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
from . import Elements
from . import Factories

# of all Elements, Node is likely to be most used, so import here
from .Elements import Node


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
    mm_elem = convert(et_elem)
    if isinstance(mm_elem, Elements.Map):
        return MindMap(mm_elem)
    return mm_elem

def write(mm_element, file_or_filename):
    """write nodes / elements to file"""
    et_elem = revert(mm_element)
    xmltree = ET.ElementTree(et_elem)
    xmltree.write(file_or_filename)

def convert(et_element):
    """Convert ElementTree Element to pymm Element

    :param et_element: Element Tree Element -> generally an element from
                       python's xml.etree.ElementTree module
    :return: Pymm hierarchical tree. Usually MindMap instance but may return
             BaseElement-inheriting element if et_element was incomplete
    """
    mmc = Factories.MindMapConverter()
    return mmc.convert_etree_element_and_tree(et_element)

def revert(mm_element):
    """Revert pymm Element to ElementTree Element

    :param mm_element: pymm Element from pymm.Elements module
    :return: xml.etree version of passed pymm tree
    """
    return Factories.MindMapConverter().revert_mm_element_and_tree(mm_element)


class MindMap(Elements.Map):
    """Interface to Freeplane structure. Allow reading and writing of xml
    mindmap formats (.mm)

    some methods inherited from Elements.Map that will prove useful:
    getroot - obtain MindMap's first child - the Root Node
    setroot - set the MindMap's only child node
    """

    def __init__(self, map_element=None):
        """ FreeplaneFile acts as an interface to intrepret xml-based .mm files into a tree of Nodes.

        :param mapElement: (optional) a pymm Map Element from which to copy all
                           attributes

        :return:
        """
        super().__init__()  # init Elements.Map parent. absolutely necessary
        self._create_new_mindmap_hierarchy()
        if isinstance(map_element, Elements.Map):
            self._from_map(map_element)

    def _from_map(self, map_element):
        for var in vars(map_element):
            vars(self)[var] = vars(map_element)[var]

    def write(self, file_or_filename):
        """ writes internal map and linked Nodes to file/filename

        :param file_or_filename: string path to file or file instance of mindmap (.mm)
        :return:
        """
        et_map = revert(self)
        xmltree = ET.ElementTree(et_map)
        xmltree.write(file_or_filename)

    def _create_new_mindmap_hierarchy(self):
        """create default hierarchy for mindmap -- including map_styles and
        Automatic node coloring hook
        """
        self.children.append(Elements.Node())

