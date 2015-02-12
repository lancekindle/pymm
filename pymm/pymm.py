import xml.etree.ElementTree as ET
from . import mindmapFactories
from . import mindmapElements

__all__ = ['FreeplaneFile']


class FreeplaneFile(object):

    mmFactory = mindmapFactories.MindMapFactory

    def __init__(self, mapElement=None):
        self.mmFactory = self.mmFactory()  # initialize mindmap factory.
        self.mmMap = mindmapElements.Map()
        self.mmMap.append(mindmapElements.Node())  # set up map and root node
        if mapElement is not None:
            self.mmMap = mapElement  # we make the assumption that this is a mindmap Map

    def readfile(self, file_or_filename):
        etMap = ET.parse(file_or_filename)
        self.mmMap = self.convert(etMap)

    def writefile(self, file_or_filename):
        etMap = self.revert(self.mmMap)  # the user passed in .....
        xmlTree = ET.ElementTree(etMap)
        xmlTree.write(file_or_filename)

    def getroot(self):
        return self.mmMap.nodes[0]

    def setroot(self, root):
        self.mmMap.nodes[0] = root

    def getmap(self):
        return self.mmMap
    
    def convert(self, etElement):
        return self.mmFactory.convert_etree_element_and_tree(etElement)

    def revert(self, mmElement):
        return self.mmFactory.revert_mm_element_and_tree(mmElement)
