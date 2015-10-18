import xml.etree.ElementTree as ET
from . import Elements
from . import Factories  # python3 relative imports (doesn't work in python2)
from . import when
from .Elements import Node

# reorganizing so that MindMap is a fancy version of Map
# also working on methods open, write, convert, and revert to be directly
# accessible from pymm imports. Aka pymm.open, pymm.write, pymm.convert,
# pymm.revert
# this way the functionality of MindMap is similar to navigating all of 
# pymm's elements.

def read(file_or_filename):
    """ converts the file/filename into a pymm tree

    :param file_or_filename: string path to file or file instance of mindmap (.mm)
    :return: FreeplaneFile instance with file read
    """
    tree = ET.parse(file_or_filename)
    etElem = tree.getroot()
    mmElem = convert(etElem)
    if isinstance(mmElem, Elements.Map):
        return MindMap(mmElem)
    return mmElem

def write(mmElement, file_or_filename):
    """ write nodes / anything to file. Need to just write to file (but realize it may not be a mindmap)
    """
    etElem = revert(mmElement)
    xmlTree = ET.ElementTree(etElem)
    xmlTree.write(file_or_filename)

def convert(etElement):
    """ Convert ElementTree Element to pymm Element

    :param etElement: Element Tree Element -> generally an element from python's xml.etree.ElementTree module
    :return:
    """
    return Factories.MindMapConverter().convert_etree_element_and_tree(etElement)

def revert(mmElement):
    """ Revert pymm Element to ElementTreee Element

    :param mmElement: pymm Element from pymm.mindmapElements module
    :return:
    """
    return Factories.MindMapConverter().revert_mm_element_and_tree(mmElement)


class MindMap(Elements.Map):
    """ Interface to Freeplane structure. Allow reading and writing of xml mindmap formats (.mm)

    readfile - reads file/filename and converts to structural tree with Map as first node
    writefile - writes full structural tree to file/filename
    getroot - skip the Map element and obtain its first child - the Root Node
    setroot - set the Map's only child node
    getmap - obtain the Map element. At present, this Map contains just the Root Node. Recommend just using get/setroot
    convert - generally implemented internally. Will convert an ElementTree Element into a Freeplane-compatible element
    revert - generally implemented internally. Will revert a Freeplane-compatible element to an ElementTree Element
    """

    def __init__(self, mapElement=None):
        """ FreeplaneFile acts as an interface to intrepret xml-based .mm files into a tree of Nodes.

        :param mapElement: (optional) a pymm Map Element. Obtained from another FreeplaneFile's getmap() method
        :return:
        """
        super().__init__()  # init real Map stuff. absolutely necessary
        self._create_new_mindmap_hierarchy()  # initialize a new instance
        if isinstance(mapElement, Elements.Map):
            self._from_map(mapElement)  # we make the assumption that this is a mindmap Map

    def _from_map(self, mapElement): # copy everything from mapElement
        for v in vars(mapElement):
            vars(self)[v] = vars(mapElement)[v]

    def write(self, file_or_filename):
        """ writes internal map and linked Nodes to file/filename

        :param file_or_filename: string path to file or file instance of mindmap (.mm)
        :return:
        """
        etMap = revert(self)
        xmlTree = ET.ElementTree(etMap)
        xmlTree.write(file_or_filename)

    def _create_new_mindmap_hierarchy(self):
        ''' create default hierarchy for mindmap -- including map_styles and Automatic node coloring hook '''
        self.append(Elements.Node())  # add root node to self (self is map)

