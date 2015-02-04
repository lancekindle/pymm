from uuid import uuid4
import warnings

class ElementAccessor(object):
    # this object is intended to hold a reference to ONE node or element. When initialized with a set of tags,
    # the object will search its reference node for those tags and allow access to them, including indexing,
    # iteration, removal, deletion, etc.

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
            if child.tag in self._tags:
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

    def __str__(self):
        return 'Accessor for: ' + str(self._tags)

    def __repr__(self):
        return '<' + str(self)[:15] + '...'*(len(str(self))>15) +' @' + hex(id(self)) + '>'




class BaseElement(object):
    # BaseElement for basic child access functionality
    # NOTE: It is extremely dangerous to define lists and dictionaries on a class-level.If you forget to initialize it
    # via: self._str = list(self._str...) or self.dict = self.dict.copy() then any changes will affect the CLASS VARS!
    # (because the self.var would actually be pointing to the class variable)
    # this caught me at first, but since I re-initialize them in the init, everything is good.
    tag = 'invalid'  # must set to cloud, hook, edge, etc.
    parent = None
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
        if isinstance(key, str):
            return key in self._attribs
        if key in self._children:
            return True
        return False

    def findall(self, tag):
        if tag =='*':
            return self._children
        matching = []
        for element in self:
            if element.tag == tag:
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
            if hasattr(value, 'parent'): # if we can set parent attribute of element
                value.parent = self

    def __delitem__(self, key):
        if isinstance(key, str):
            del self._attribs[key]
        else:
            element = self._children[key]
            if hasattr(element, 'parent'):
                element.parent = None
            del self._children[key]

    def index(self, item):
        return self._children.index(item)

    def append(self, element):
        self._children.append(element)
        if hasattr(element, 'parent'):
            element.parent = self

    def extend(self, elements):
        for element in elements:
            self.append(element)  # we call here so that we can set parent attribute. Unfortunately means its slowish

    def remove(self, element):
        self._children.remove(element)
        if hasattr(element, 'parent'):
            element.parent = None

    def items(self):
        return self._attribs.items()

    def keys(self):
        return self._attribs.keys()

    def __str__(self):
        extras = [' ' + prop + ': ' + value for prop, value in self.items() if prop in self._strConstructors]
        s = self.tag
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
        return self.tag + ': ' + str(self.gettext())

    def gettext(self):
        return self.text

    def settext(self, text):
        if isinstance(text, str):  # may either be html or just words.
            self.text = str(text)  # we call str() on text to convert to printable characters.


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
    _attribs = {'BUILTIN': 'bookmark'}
    _strConstructors = ['BUILTIN']
    builtinList = ['help', 'bookmark', 'yes', 'button_ok', 'button_cancel', 'idea', 'messagebox_warning', 'stop-sign',
                   'closed', 'info', 'clanbomber', 'checked', 'unchecked', 'wizard', 'gohome', 'knotify', 'password',
                   'pencil', 'xmag', 'bell', 'launch', 'broken-line', 'stop', 'prepare', 'go', 'very_negative',
                   'negative', 'neutral', 'positive', 'very_positive', 'full-1', 'full-2', 'full-3', 'full-4', 'full-5',
                   'full-6', 'full-7', 'full-8', 'full-9', 'full-0', '0%', '25%', '50%', '75%', '100%', 'attach',
                   'desktop_new', 'list', 'edit', 'kaddressbook', 'pencil', 'folder', 'kmail', 'Mail', 'revision',
                   'video', 'audio', 'executable', 'image', 'internet', 'internet_warning', 'mindmap', 'narrative',
                   'flag-black', 'flag-blue', 'flag-green', 'flag-orange', 'flag-pink', 'flag', 'flag-yellow', 'clock',
                   'clock2', 'hourglass', 'calendar', 'family', 'female1', 'female2', 'females', 'male1', 'male2',
                   'males', 'fema', 'group', 'ksmiletris', 'smiley-neutral', 'smiley-oh', 'smiley-angry','smiley_bad',
                   'licq', 'penguin', 'freemind_butterfly', 'bee', 'forward', 'back', 'up', 'down', 'addition',
                   'subtraction', 'multiplication', 'division']  # you can add additional icons right here if one is
        # missing by simply appending to the class builtin list: Icon.builtinList.append(icon-name)

    def set_icon(self, icon):
        self['BUILTIN'] = icon
        if icon not in self.builtinList:
            warnings.warn('icon "' + str(icon) + '" not part of freeplanes builtin icon list. ' +
                'Freeplane may not display icon. Use an icon from the builtinList instead', SyntaxWarning, stacklevel=2)


class Edge(BaseElement):
    tag = 'edge'
    styleList = ['linear', 'bezier', 'sharp_linear', 'sharp_bezier', 'horizontal', 'hide_edge']
    widthList = ['thin', '1', '2', '4', '8']

    def set_style(self, style):
        self['STYLE'] = style
        if style not in self.styleList:
            warnings.warn('edge style "' + str(style) + '" not part of freeplanes edge styles list. ' +
                'Freeplane may not display edge. Use a style from the styleList instead', SyntaxWarning, stacklevel=2)
    
class Attribute(BaseElement):
    tag = 'attribute'
    _attribs = {'NAME': '','VALUE': ''}

class Properties(BaseElement):
    tag = 'properties'