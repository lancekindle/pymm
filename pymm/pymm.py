import xml.etree.ElementTree as ET
from . import Factories
from .Elements import Node  # keep this import; developer will mostly likely want access to Node more than anything.


class FreeplaneFile(object):

    def __init__(self):
        self.xmlTree = ET.ElementTree()
        self.mmf = Factories.MindMapFactory()

    def readfile(self, filename):
        self.xmlTree.parse(filename)
        self._convert(self.xmlTree)

    def writefile(self, filename):
        self._revert(self.mapnode)
        self.xmlTree.write('output.mm')

    def getroot(self):
        #return self.mapnode[0]  # map has one child -> the root  # NOT TRUE! #there can be an attribute_registry here
        return self.mapnode.findall('node')[0]

    def getmap(self):
        return self.mapnode
    
    def _convert(self, xmlTree):
        etMapNode = xmlTree.getroot()
        self.mapnode = self.mmf.convert_etree_element_and_tree(etMapNode)

    def _revert(self, mapNode):
        #mapF = MapFactory()
        etMapNode = self.mmf.revert_node_and_tree(self.mapnode)
        #etMapNode = mapF.to_etree_element(self.mapnode)
        # need to convert mapNode too!
        self.xmlTree._root = etMapNode