from uuid import uuid4


class BaseElement(object):
    # BaseElement for basic child access functionality
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self._tag = 'invalid'  # must set to cloud, hook, edge, etc.
        self._children = []  # all child elements including nodes

    def __iter__(self):  # why was I incorrect in thinking it was iteritem?
        for child in self._children:
            yield child

    def __contains__(self, key):
        if key in self._children:
            return True
        return False

    def findall(self, tag):
        if tag =='*':
            return self._children
        matching = []
        for element in self:
            if element.gettag() == tag:
                matching.append(element)
        return matching
            
    def __len__(self):
        return len(self[:])

    def __getitem__(self, key):
        return self._children[key]

    def __setitem__(self, key, value):
        self._children[key] = value

    def __delitem__(self, key):
        del self._children[key]  # this permanently deletes the child! be careful

    def append(self, node):
        self._children.append(node)
        self._separate_children()

    def extend(self, nodes):
        self._children.extend(nodes)

    def gettag(self):
        return self._tag

    def __str__(self):
        return self.gettag()

    def __repr__(self):
        return '<' + str(self)[:13] + '...'*(len(str(self))>13) +' @' + hex(id(self)) + '>'

    def gethooks(self):
        pass#return self._hooks[:]

    def getclouds(self):
        pass#return self._clouds[:]

    def geticons(self):
        pass#return self._icons[:]

    def getattributes(self):
        pass# return self._attributes.copy()  # not guarenteed to be immutable


class Node(BaseElement):
    
    def __init__(self, **kwargs):
        self.text = ''
        self.id = 'ID_' + str(uuid4().time)[:-1]
        super(Node, self).__init__(**kwargs)
        self._tag = 'node'
        self._recognizableNodeTags = ['node']  # any element with matching tag will be accessible with node.nodes()
            # So if you wish add a new nodetype, simply add it using node.getRecognizableNodeTags().add(tag)

    def __str__(self):
        return self.gettag() + ': ' + str(self.text)

    def getRecognizableNodeTags(self):
        return self._recognizableNodeTags

    def nodes(self):  # returns an iterator for going through nodes
        for child in self:
            if child.gettag() in self.getRecognizableNodeTags():
                yield child


class Map(BaseElement):

    def __init__(self, **kwargs):
        self.version = 'freeplane 1.3.0'  # version supported
        super(Map, self).__init__(**kwargs)
        self._tag = 'map'
        self._supportedVersions = ['freeplane 1.3.0']

    def setroot(self, root):
        pass

    def getroot(self):
        pass


class Cloud(BaseElement):
    
    def __init__(self, **kwargs):
        self.color = '#333ff'
        self.shape = 'ARC'
        super(Cloud, self).__init__(**kwargs)
        self._tag = 'cloud'

    def __str__(self):
        return self.gettag() + ': color:' + str(self.color) + ' shape:' + str(self.shape)


class Hook(BaseElement):

    def __init__(self, **kwargs):
        self.name = ''
        super(Hook, self).__init__(**kwargs)
        self._tag = 'hook'

class MapStyles(BaseElement):

    def __init__(self, **kwargs):
        super(MapStyles, self).__init__(**kwargs)
        self._tag = 'map_styles'


class StyleNode(BaseElement):

    def __init__(self, **kwargs):
        self.localized_text = ''
        super(StyleNode, self).__init__(**kwargs)
        self._tag = 'stylenode'


class Font(BaseElement):

    def __init__(self, **kwargs):
        self.size = None
        self.bold = None
        self.italic = None
        super(Font, self).__init__(**kwargs)
        self._tag = 'font'


class Icon(BaseElement):

    def __init__(self, **kwargs):
        super(Icon, self).__init__(**kwargs)
        self._tag = 'icon'


class Edge(BaseElement): 

    def __init__(self, **kwargs):
        super(Edge, self).__init__(**kwargs)
        self._tag = 'edge'

    
class Attribute(BaseElement):

    def __init__(self, **kwargs):
        self.name = ''
        self.value = ''
        super(Attribute, self).__init__(**kwargs)
        self._tag = 'attribute'


class Properties(BaseElement):

    def __init__(self, **kwargs):
        super(Properties, self).__init__(**kwargs)
        self._tag = 'properties'
