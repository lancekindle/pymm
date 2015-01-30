from uuid import uuid4

class ElementAccessor(object):
    # this object is intended to hold a reference to ONE node or element. When initialized with a set of tags,
    # the object will search its reference node for those tags and allow access to them, including indexing
    # and iteration.

    def __init__(self, element, tags=[]):
        self._tags = list(tags[:])
        self._holder = element

    def __call__(self):  # this function will be called when the user is trying to access particular elements for
        elements = []  # example,node.nodes() where we assume nodes actually points to this instance.
        for tag in self._tags:
            elements.extend(self._holder.findall(tag))
        return elements

    def __iter__(self):
        for child in self._holder:
            if child.gettag() in self._tags:
                yield child

    def __getitem__(self, index):
        return self()[index]

    def __setitem__(self, key, value):  #should we allow the user to set nodes? I think so :)  just need to make it consistnt
        allElements = self()
        for element in allElements:
            self._holder.remove(element)
        allElements[key] = value  # if user chooses node.nodes()[:] = [] for example, only this way would work
        for element in allElements:
            self._holder.append(element)

    def __delitem__(self, key):
        element = self[key]
        index = self._holder.index(element)
        del self._holder[index]

    def __contains__(self, element):
        return element in self()

    def __len__(self):
        return len(self())

    def append(self, element):
        self._holder.append(element)

    def extend(self, elements):
        self._holder.extend(elements)

    def remove(self, element):
        self._holder.remove(element)


class BaseElement(object):
    # BaseElement for basic child access functionality
    # NOTE: It is extremely dangerous to define lists and dictionaries on a class-level.If you forget to initialize it
    # via: self._str = list(self._str...) or self.dict = self.dict.copy() then any changes will affect the CLASS VARS!
    # (because the self.var would actually be pointing to the class variable)
    # this caught me at first, but since I re-initialize them in the init, everything is good.
    tag = 'invalid'  # must set to cloud, hook, edge, etc.
    _attribs = {}  # pre-define these (outside of init like this) in other classes to define default element attribs
    _strConstructors = []  # list of attribs to use in construction __str__

    def __init__(self, **kwargs):
        self._attribs = self._attribs.copy()
        self._strConstructors = list(self._strConstructors) + []
        self._children = []  # all child elements including nodes
        self.parent = None  # set to something when it is added as a child.
        for key, value in kwargs.items():
            self[key] = value

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
        if isinstance(key, str):
            return self._attribs[key]
        return self._children[key]

    def __setitem__(self, key, value):
        if isinstance(key, str):
            self._attribs[key] = value
        else:
            self._children[key] = value

    def __delitem__(self, key):
        if isinstance(key, str):
            del self._attribs[key]
        else:
            del self._children[key]

    def index(self, item):
        return self._children.index(item)

    def append(self, element):
        self._children.append(element)

    def extend(self, elements):
        self._children.extend(elements)

    def remove(self, element):
        self._children.remove(element)

    def items(self):
        return self._attribs.items()

    def keys(self):
        return self._attribs.keys()

    def gettag(self):
        return self.tag

    def __str__(self):
        extras = [' ' + prop + ': ' + value for prop, value in self.items() if prop in self._strConstructors]
        s = self.gettag()
        for descriptor in extras:
            s += descriptor
        return s

    def __repr__(self):
        return '<' + str(self)[:13] + '...'*(len(str(self))>13) +' @' + hex(id(self)) + '>'

    def gethooks(self):
        pass#return self._hooks[:]


class Node(BaseElement):
    tag = 'node'
    _attribs = {'ID': 'ID_' + str(uuid4().time)[:-1], 'TEXT': ''}

    def __init__(self, **kwargs):
        super(Node, self).__init__(**kwargs)
        self.text = '' # should initialize some html editor instance. That allows you to edit an html document
        # or just write it in plain text.
        self.nodes = ElementAccessor(self, ['node'])

    def __str__(self):
        return self.gettag() + ': ' + str(self.gettext())

    def getRecognizableNodeTags(self):
        return self._recognizableNodeTags

    def gettext(self):
        return self.text

    def settext(self, text):
        if isinstance(text, str):  # may either be html or just words.
            self.text = text

    def getclouds(self):
        pass#return self._clouds[:]

    def geticons(self):
        pass#return self._icons[:]

    def getattributes(self):
        pass# return self._attributes.copy()  # not guarenteed to be immutable

    def _additional_conversion(self):
        pass  # need to convert text to html if some richcontent module is found


class Map(BaseElement):
    tag = 'map'
    _attribs = {'version': 'freeplane 1.3.0'}

    def setroot(self, root):
        pass

    def getroot(self):
        pass


class Cloud(BaseElement):
    tag = 'cloud'
    _attribs = {'COLOR': '#333ff', 'SHAPE': 'ARC'}  # set defaults
    _strConstructors = ['COLOR', 'SHAPE']  # extra information to send during call to __str__

class Hook(BaseElement):
    tag = 'hook'

class MapStyles(BaseElement):
    tag = 'map_styles'

class StyleNode(BaseElement):
    tag = 'stylenode'

class Font(BaseElement):
    tag = 'font'
    _attribs = {'BOLD': 'false', 'ITALIC': 'false', 'NAME': 'SansSerif', 'SIZE': '10'}  # set defaults

class Icon(BaseElement):
    tag = 'icon'

class Edge(BaseElement):
    tag = 'edge'
    
class Attribute(BaseElement):
    tag = 'attribute'

class Properties(BaseElement):
    tag = 'properties'