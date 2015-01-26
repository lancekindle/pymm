from uuid import uuid4


class BaseNode(object):
    # BaseNode for basic child access functionality
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self._tail = "\n"  # default spacing that gives the written file a clean look
        self._type = 'BaseNode'  # could be Cloud, Hook, Edge, MapStyle, etc
        self._tag = 'invalid'  # must set to cloud, hook, edge, etc.
        self._children = []  # to get or set children, use node[:]
        self._unconvertedChildren = []

    def __iteritem__(self):
        for child in self._children:
            print(child.gettype() in types)
            if child.gettype() in types:
                yield child

    def iterate(self, nodeTypes):  # should really accept a list of acceptable types
        for child in self._children:
            if nodeTypes == '*':
                yield child
            

    def items(self):  # to iterate over the dictionary items!
        for key, value in self._attributes.items():
            yield (key, value)

    def __contains__(self, key):
##        if key in self._attributes:
##            return True
        if key in self[:]:  # use self[:] so that we iterate over child nodes only
            return True
        return False

    def __len__(self):
        return len(self[:])  # so that way it uses the __iteritem__ and restricts to counting child nodes

    # getitem is problematic. If I want all node children to be accessible, __getitem__
    # takes over when I call
    # for n in node:      <-- not what I expected!
    def __getitem__(self, key):
        if isinstance(key, str):  # access node attributes instead
            pass#return str(self._attributes[key])
        return self._children[key]

    def __setitem__(self, key, value):
        if isinstance(key, str):
            pass#self._attributes[key] = str(value)
        else:
            self._children[key] = value

    def __delitem__(self, key):
        if isinstance(key, str):
            pass#del self._attributes[key]
        else:
            del self._children[key]  # this permanently deletes the child! be careful

    def append(self, node):
        self._children.append(node)

    def extend(self, nodes):
        self._children.extend(nodes)

    def __str__(self):
        return self._type

    def __repr__(self):
        return '<' + str(self)[:13] + '...'*(len(str(self))>13) +' @' + hex(id(self)) + '>'

    def gethooks(self):
        pass#return self._hooks[:]

    def getclouds(self):
        pass#return self._clouds[:]

    # there is no more "setclouds" or "seticons" because setting can be achieved simply by node.append
    
    def geticons(self):
        pass#return self._icons[:]

    def gettype(self):
        return str(self._type)

    def getattributes(self):
        pass# return self._attributes.copy()  # not guarenteed to be immutable

    def _gettail(self):
        return str(self._tail)


class Node(BaseNode):
    
    def __init__(self, **kwargs):
        self.text = ''
        self.id = 'ID_' + str(uuid4().time)[:-1]
        super(Node, self).__init__(**kwargs)
        self._type = 'Node'
        self._tag = 'node'

    def __str__(self):
        return self._type + ': ' + str(self.text)


class Map(BaseNode):

    def __init__(self, **kwargs):
        self.version = 'freeplane 1.3.0'  # version supported
        super(Map, self).__init__(**kwargs)
        self._type = 'Map'
        self._tag = 'map'
        self._supportedVersions = ['freeplane 1.3.0']

    def setroot(self, root):
        pass

    def getroot(self):
        pass


class Cloud(BaseNode):
    
    def __init__(self, **kwargs):
        self.color = '#333ff'
        self.shape = 'ARC'
        super(Cloud, self).__init__(**kwargs)
        self._type = 'Cloud'
        self._tag = 'cloud'

    def __str__(self):
        return self._type + ': color:' + str(self.color) + ' shape:' + str(self.shape)


class Hook(BaseNode):

    def __init__(self, **kwargs):
        self.name = ''
        super(Hook, self).__init__(**kwargs)
        self._type = 'Hook'
        self._tag = 'hook'

class MapStyles(BaseNode):

    def __init__(self, **kwargs):
        super(MapStyles, self).__init__(**kwargs)
        self._type = 'MapStyles'
        self._tag = 'map_styles'


class StyleNode(BaseNode):

    def __init__(self, **kwargs):
        self.localized_text = ''
        super(StyleNode, self).__init__(**kwargs)
        self._type = 'StyleNode'
        self._tag = 'stylenode'


class Font(BaseNode):

    def __init__(self, **kwargs):
        self.size = None
        self.bold = None
        self.italic = None
        super(Font, self).__init__(**kwargs)
        self._type = 'Font'
        self._tag = 'font'


class Icon(BaseNode):

    def __init__(self, **kwargs):
        super(Icon, self).__init__(**kwargs)
        self._type = 'Icon'
        self._tag = 'icon'


class Edge(BaseNode): 

    def __init__(self, **kwargs):
        super(Edge, self).__init__(**kwargs)
        self._type = 'Edge'
        self._tag = 'edge'

    
class Attribute(BaseNode):

    def __init__(self, **kwargs):
        self.name = ''
        self.value = ''
        super(Attribute, self).__init__(**kwargs)
        self._type = 'Attribute'
        self._tag = 'attribute'


class Property(BaseNode):

    def __init__(self, **kwargs):
        super(Property, self).__init__(**kwargs)
        self._type = 'Property'
        self._tag = 'property'
