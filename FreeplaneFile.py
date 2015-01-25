import xml.etree.ElementTree as ET
from uuid import uuid4

class FreeplaneFile(object):

    def __init__(self):
        self.xmlTree = ET.ElementTree()

    def readfile(self, filename):
        self.xmlTree.parse(filename)

    def writefile(self, filename):
        self._revert()

    def getroot(self):
        fpmap = self.xmlTree.getroot()
        return fpmap[0]  # map has one child -> the root

    def getmap(self):
        return self.xmlTree.getroot()
    
    def _convert(self):
        rootnodeFactory = RootNodeFactory()
        #mapFactory = MapFactory()
        #fpmap = mapFactory.from_etree_element(self.file.getroot())
        fpmap = self.xmlTree.getroot()
        self.root = rootnodeFactory.from_etree_element(fpmap[0])

    def _revert(self):
        rootnodeF = RootNodeFactory()
        fpmap = self.xmlTree.getroot()
        elementRoot = rootnodeF.to_etree_element(self.root)
        fpmap[0] = elementRoot
        self.xmlTree._root = fpmap
        self.xmlTree.write('output.mm')



class BaseNode(object):
    # BaseNode for basic child access functionality
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self._type = 'BaseNode'
        self._children = []  # to get or set children, use node[:]
        self._attributes = {}  # accessed similarly to children! Only use strings as keys to attributes
        self._unsupportedAttributes = {}
        self._hooks = []
        self._clouds = []
        self._icons = []  # we use _icons, _hooks, etc, because we cannot guarentee that the node
                                # won't have some attrib() value that overwrites non-_-items

    def __iteritem__(self):
        for child in self._children:
            yield child

    def items(self):  # to iterate over the dictionary items!
        for key, value in self._attributes.items():
            yield (key, value)

    def __contains__(self, key):
        if key in self._attributes:
            return True
        if key in self._children:
            return True
        return False

    def __len__(self):
        return len(self._children)

    def __getitem__(self, key):
        if isinstance(key, str):  # access node attributes instead
            return str(self._attributes[key])
        return self._children[key]

    def __setitem__(self, key, value):
        if isinstance(key, str):
            self._attributes[key] = str(value)
        else:
            self._children[key] = value

    def __delitem__(self, key):
        if isinstance(key, str):
            del self._attributes[key]
        else:
            del self._children[key]  # this permanently deletes the child! be careful

    def append(self, node):
        self._children.append(node)

    def __str__(self):
        return self.gettype()

    def __repr__(self):
        return '<' + str(self)[:13] + '...'*(len(str(self))>13) +' @' + hex(id(self)) + '>'

    def sethooks(self, hooks):
        self._hooks[:] = hooks  # we use ._hooks[:] so that the user is forced to
                                            # pass a list of hooks, not just one hook

    def gethooks(self):
        return self._hooks[:]

    def setclouds(self, clouds):
        self._clouds[:] = clouds

    def getclouds(self):
        return self._clouds[:]

    def seticons(self, icons):
        self._icons[:] = icons

    def geticons(self):
        return self._icons[:]

    def settype(self, typeStr):
        self._type = str(typeStr)

    def gettype(self):
        return str(self._type)

    def setattributes(self, attributes):  # you can also set attributes using node['attribute'] = 'value'
        self._attributes = {key: value for key, value in attributes.items()}

    def getattributes(self):
        return self._attributes.copy()  # not guarenteed to be immutable


class Map(BaseNode):

    def __init__(self, **kwargs):
        super(Map, self).__init__(**kwargs)
        self.settype('Map')
        self.version = 'freeplane 1.3.0'  # version supported
        self._supportedVersions = ['freeplane 1.3.0']
        self._root = None

    def setroot(self, root):
        self._root = root

    def getroot(self):
        return self._root


class MapStyle(BaseNode):

    def __init__(self, **kwargs):
        super(MapStyle, self).__init__()
        self.settype('MapStyle')
        self.zoom = 1
        self._properties = []

    def setproperties(self, properties):
        self._properties[:] = properties

    def getproperties(self, properties):
        return self._properties[:]

class Node(BaseNode):
    
    def __init__(self, **kwargs):
        self.text = ''
        self.id = 'ID_' + str(uuid4().time)[:-1]
        super(Node, self).__init__()
        self.settype('Node')
        self._edges = []

    def __str__(self):
        return self.gettype() + ': ' + str(self.text)


class RootNode(Node):
    # root node is just a Node. However, there will only be one of them in the map
    # and a rootnode has a MapStyle. No other node has a map style
    def __init__(self, **kwargs):
        super(RootNode, self).__init__(**kwargs)
        self.settype('Node')  # MUST BE NODE! - freeplane only recognizes node types

    def getmapstyle(self):  # get mapstyle from list of hooks
        for hook in self.gethooks():
            if hook.name == 'MapStyle':
                return hook

    def setmapstyle(self, mapstyleHook):
        hooks = []
        for hook in self.gethooks():
            if hook.name == 'MapStyle':
                hooks.append(mapstyleHook)
            else:
                hooks.append(hook)
        self.sethooks(hooks)


class Cloud(BaseNode):
    
    def __init__(self, **kwargs):
        super(Cloud, self).__init__(**kwargs)
        self.settype('Cloud')
        self.color = '#333ff'
        self.shape = 'ARC'

    def __str__(self):
        return self.gettype() + ': color:' + str(self.color) + ' shape:' + str(self.shape)


class Hook(BaseNode):

    def __init__(self, **kwargs):
        self.name = ''
        super(Hook, self).__init__(**kwargs)
        self.settype('Hook')


class Attribute(BaseNode):

    def __init__(self, **kwargs):
        self.name = ''
        self.value = ''
        super(Attribute, self).__init__(**kwargs)
        self.settype('Attribute')  # all attributes will overwrite this with their own "name" aka key value

        
class BaseNodeFactory(object):
    
    def __init__(self, **kwargs):
        self.nodeType = BaseNode

    def from_etree_element(self, element):
        '''converts an xml etree element to a node
        '''
        node = self.nodeType()  # could be anything: Map, Node, etc.
        usedAttribs = []
        for key, value in element.attrib.items():  # sets node text, amongst other things
            key = key.lower()  # lowercase because that's how all our node properties are
            if hasattr(node, key):
                setattr(node, key, value)  # all xml-node attribs become fp-node attributes
                usedAttribs.append(key)
        unusedAttribs = {key.lower(): val for (key, val) in element.attrib.items() if key.lower() not in usedAttribs}
        if unusedAttribs:
            print(unusedAttribs)  # for diagnostics: determining if I need to add support for more stuff
        self._additional_conversion(node, element)
        return node

    def _additional_conversion(self, node, element):
        pass  # should be overridden by an inheriting class to perform addtional conversion before returning node

    def to_etree_element(self, node):
        attribs = {key.upper(): value for key, value in vars(node).items() if not key[0] == '_'}  # only use visible variables
        print(node)
        element = ET.Element(node.gettype().lower(), attribs)
        self._additional_reversion(element, node)
        return element

    def _additional_reversion(self, element, node):
           pass # should be overridden by inheriting class for additional reversion to ET element


class NodeFactory(BaseNodeFactory):

    def __init__(self, **kwargs):
        self.nodeType = Node

    def _additional_conversion(self, node, element):
        self.add_node_attributes(node, element)
        self.add_et_children(node, element)
        self.add_hooks(node, element)
        self.add_clouds(node, element)
        if not hasattr(self, '_notFirstNodeCreated'):   # this is first node created, so we need to convert children!
            print('first node! converting children')
            self._convert_full_node_tree(node)

    def add_node_attributes(self, node, element):
        attributeFactory = AttributeFactory()
        attributes = {}
        for attrNode in attributeFactory.get_child_attributes_from_etree_element(element):
            for key, value in attrNode.items():
                attributes[key] = value
        node.setattributes(attributes)

    def add_et_children(self, node, element):
        for child in element.findall('node'):
            node.append(child)  # these are unconverted, etree Element children - need to be converted later

    def add_hooks(self, node, element):
        hookFactory = HookFactory()
        hooks = []
        for hook in hookFactory.get_child_hooks_from_etree_element(element): 
            hooks.append(hook)  # these are hooks which may constitute a node property like 'edge', etc...
        node.sethooks(hooks)

    def add_clouds(self, node, element):
        cloudFactory = CloudFactory()
        clouds = []
        for cloud in cloudFactory.get_child_clouds_from_etree_element(element):
            clouds.append(cloud)
        node.setclouds(clouds)

    def _convert_full_node_tree(self, node):
        '''called only by the nodeFactory creating the first node. Go through each node and
            convert all its children to nodes non-recursively, until the full node tree is converted.
        '''
        nodeFactory = NodeFactory()
        nodeFactory._notFirstNodeCreated = True  # now we will not convert children. This prevents recursion in creating node children 
        hasUnconvertedChildren = [node]
        while hasUnconvertedChildren:
            node = hasUnconvertedChildren.pop()
            unconvertedChildren = node[:]
            node[:] = [] # remove all unconverted children
            for etChild in unconvertedChildren:
                child = nodeFactory.from_etree_element(etChild)
                node.append(child)
                hasUnconvertedChildren.append(child)
        # no need to return node. It is held in reference

    def _additional_reversion(self, element, node):
        cloudF = CloudFactory()
        attributeF = AttributeFactory()
        hookF = HookFactory()
        for cloud in node.getclouds():
            element.append(cloudF.to_etree_element(cloud))
        for attributeItem in node.getattributes().items():
            element.append(attributeF.to_etree_element(attributeItem))
        for hook in node.gethooks():
            element.append(hookF.to_etree_element(hook))
        for child in node:
            element.append(child)  # unreverted nodes! These will be converted only if this is first node being reverted
        if not hasattr(self, '_notFirstNodeReverted'):   # this is first node created, so we need to convert children!
            print('first node! reverting children')
            self._revert_full_node_tree(element)

    def _revert_full_node_tree(self, element):
        ''' called only by the nodeFactory reverting the first node. Go through each node and revert
            all its children to elements non-recursively, until the full etree is reverted
        '''
        nodeF = NodeFactory()
        nodeF._notFirstNodeReverted = True
        hasUnrevertedChildren = [element]
        while hasUnrevertedChildren:
            element = hasUnrevertedChildren.pop()
            unrevertedChildren = element[:]
            element[:] = []  # remove reference to children. will re-add soon
            for node in unrevertedChildren:
                if isinstance(node, BaseNode):  # an unreverted node
                    etChild = nodeF.to_etree_element(node)
                else:
                    etChild = node  # the "node" was already reverted! Probably a cloud, edge, or hook
                element.append(etChild)
                hasUnrevertedChildren.append(etChild)


class RootNodeFactory(NodeFactory):
    def __init__(self, **kwargs):
        self.nodeType = RootNode

    def _additional_conversion(self, node, element):
        super(RootNodeFactory, self)._additional_conversion(node, element)  # which adds hooks already
##        hooks = []
##        for hook in node.getHooks():
##            if hook.gettype() == 'MapStyle':
##                
##        # now add hooks
##        hookFactory = HookFactory()
##        hooks = []
##        for etHook in element.findall('hook'):
##            hook = hookFactory.from_etree_element(etHook)
##            if hook.gettype() == 'MapStyle':
##                mapStyleFactory = MapStyleFactory()
##                mapStyle = mapStyleFactory.from_etree_element(etHook)
##                self.mapStyle = mapStyle
##            else:  # just a normal hook
##                hooks.append(hook)
##        node.setHooks(hook)


class CloudFactory(BaseNodeFactory):
    def __init__(self, **kwargs):
        self.nodeType = Cloud

    def get_child_clouds_from_etree_element(self, element):
        clouds = []
        for etCloud in element.findall('cloud'):
            cloud = self.from_etree_element(etCloud)
            clouds.append(cloud)
        return clouds
        

class MapFactory(BaseNodeFactory):
    def __init__(self, **kwargs):
        self.nodeType = Map


class MapStyleFactory(BaseNodeFactory):
    def __init__(self, **kwargs):
        self.nodeType = MapStyle


class HookFactory(BaseNodeFactory):
    def __init__(self, **kwargs):
        self.nodeType = Hook

    def get_child_hooks_from_etree_element(self, element):
        hooks = []
        for etHook in element.findall('hook'):
            hook = self.from_etree_element(etHook)
            hooks.append(hook)
        return hooks


class AttributeFactory(BaseNodeFactory):
    def __init__(self, **kwargs):
        self.nodeType = Attribute

    def _additional_conversion(self, node, element):
        attributes = {}
        attributes[node.name] = node.value
        node.setattributes(attributes)

    def to_etree_element(self, tupleItem):
        key, value = tupleItem
        element = ET.Element('attribute', {'NAME':key, 'VALUE': value})
        return element

    def get_child_attributes_from_etree_element(self, element):
        attrs = []
        for etAttr in element.findall('attribute'):
            attribute = self.from_etree_element(etAttr)
            attrs.append(attribute)
        return attrs


if __name__ == '__main__':
    fpf = FreeplaneFile()
    fpf.readfile('input.mm')
    fpf._convert()
    element = fpf.xmlTree.getroot().findall('node')[0]
    n = fpf.root
    nc = n[0][0]
    hs = element.findall('hook')  # hooks for maps???
    hs[0].attrib  # prints off 'NAME' : 'MapStyle'
    fpf.writefile('output.mm')

