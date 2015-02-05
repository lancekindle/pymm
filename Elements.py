from uuid import uuid4
import warnings

# see http://freeplane.sourceforge.net/wiki/index.php/Current_Freeplane_File_Format for file specifications

class ElementAccessor(object):
    # this object is intended to hold a reference to ONE node or element. When initialized with a set of tags,
    # the object will search its reference node for those tags and allow access to them, including indexing,
    # removal, deletion, etc. to iterate, simply use self[:] e.g. node.nodes[:]

    def __init__(self, element, tags=[]):
        self._tags = list(tags[:])
        self._holder = element

    def __call__(self):  # this function will be called when the user is trying to access particular elements for
        return self[:]  # example,node.nodes() where we assume nodes actually points to this instance.

    # for same reason as BaseElement, we must disallow direct iteration. This makes calls much cleaner, and we ensure
    # (reasonably) that when we do iterate, it will not be accidentally over an element's children.
    # again, CLEANER CODE, easier to understand when reading code, and fewer writing mistakes.
    # def __iter__(self):
    #     for child in self._holder[:]:
    #         if child.tag in self._tags:
    #             yield child

    def __getitem__(self, index):
        elements = []
        for tag in self._tags:
            elements.extend(self._holder.findall(tag))
        return elements[index]

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
        return element in self

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
    tag = 'BaseElement'  # must set to cloud, hook, edge, etc.
    parent = None
    _elementText = ''
    _tailText = ''
    _children = []  # all child elements including nodes
    _attribs = {}  # pre-define these (outside of init like this) in other classes to define default element attribs
    _attribSpecs = {}  # list all possible attributes of an element and its choices [...] or value type (str, int, etc.)
    _strConstructors = []  # list of attribs to use in str(self) construction

    def __init__(self, **kwargs):
        self._attribs = self._attribs.copy()  # copy all class lists/dicts into instance
        self._attribSpecs = self._attribSpecs.copy()
        self._strConstructors = list(self._strConstructors) + []
        self._children = list(self._children) + []
        for key, value in kwargs.items():
            self[key] = value

    ## DO NOT use iter. Because it makes it unclear what is added. e.g.: n.append(c), n.extend(c). If the user were to
    ## accidentally call n.extend(c), then it would actually add all of c's children, rather than c itself.
    # by preventing __iter__ we can ensure that the sytax for adding children is cleaner. MUCH CLEANER
    # downside is that child iteration will be slower, on account of it mostly being non-iteration
    # def __iter__(self):  # why was I incorrect in thinking it was iteritem?
    #     for child in self._children:
    #         yield child

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
        for element in self[:]:
            if element.tag == tag:
                matching.append(element)
        return matching
            
    def __len__(self):
        return len(self[:])

    def __getitem__(self, key):
        if isinstance(key, str):
            return self._attribs[key]
        return self._children[key]

    def __setitem__(self, key, value):  # in some cases, __setitem__ can set all children of node without going through append. Which means the node's parent is not set
        if isinstance(key, str):
            self._attribs[key] = value
        else:
            index, child = key, value
            if type(index) == slice:
                if isinstance(child, BaseElement):  # prevent assigning element[:] = c where c is a solitary child
                    raise TypeError('can only assign an iterable')
                children = child  # "child" is actually an iterable of children
                self._children[index] = children
            else:
                self._children[index] = child
                children = [child]
            for child in children:
                if hasattr(child, 'parent'):
                    child.parent = self

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
    _attribSpecs = {'BACKGROUND_COLOR': str, 'COLOR': str, 'FOLDED': bool, 'ID': str, 'LINK': str,
                    'POSITION': ['left', 'right'], 'STYLE': str, 'TEXT': str, 'LOCALIZED_TEXT': str, 'TYPE': str,
                    'CREATED': int, 'MODIFIED': int, 'HGAP': int, 'VGAP': int, 'VSHIFT': int, 'ENCRYPTED_CONTENT': str,
                    'OBJECT': str, 'MIN_WIDTH': int, 'MAX_WIDTH': int}

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
    _attribSpecs = {'version': str}

    def setroot(self, root):
        pass

    def getroot(self):
        pass


class Cloud(BaseElement):
    tag = 'cloud'
    shapeList = ['ARC', 'STAR','RECT','ROUND_RECT']
    _attribs = {'COLOR': '#333ff', 'SHAPE': 'ARC'}  # set defaults
    _attribSpecs = {'COLOR': str, 'SHAPE': shapeList, 'WIDTH': str}
    _strConstructors = ['COLOR', 'SHAPE']  # extra information to send during call to __str__

class Hook(BaseElement):
    tag = 'hook'
    _attribs = {'NAME': 'overwritten'}
    _attribSpecs = {'NAME': str}

class EmbeddedImage(Hook):
    _attribs = {'NAME': 'ExternalObject'}
    _attribSpecs = {'NAME': str, 'URI': str, 'SIZE': float}

class MapConfig(Hook):
    _attribs = {'NAME': 'MapStyle', 'zoom': 1.0}
    _attribSpecs = {'NAME': str, 'max_node_width': int, 'zoom': float}

class Equation(Hook):
    _attribs = {'NAME': 'plugins/latex/LatexNodeHook.properties'}
    _attribSpecs = {'NAME': str, 'EQUATION': str}

class AutomaticEdgeColor(Hook):
    _attribs = {'NAME': 'AutomaticEdgeColor', 'COUNTER': 0}
    _attribSpecs = {'NAME': str, 'COUNTER': int}

class MapStyles(BaseElement):
    tag = 'map_styles'

class StyleNode(BaseElement):
    tag = 'stylenode'
    _attribSpecs = {'LOCALIZED_TEXT': str, 'POSITION': ['left', 'right'], 'COLOR': str, 'MAX_WIDTH': int, 'STYLE': str}

class Font(BaseElement):
    tag = 'font'
    _attribs = {'BOLD': False, 'ITALIC': False, 'NAME': 'SansSerif', 'SIZE': 10}  # set defaults
    _attribSpecs = {'BOLD': bool, 'ITALIC': bool, 'NAME': str, 'SIZE': int}

class Icon(BaseElement):
    tag = 'icon'
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
    _attribs = {'BUILTIN': 'bookmark'}
    _attribSpecs = {'BUILTIN': builtinList}

    def set_icon(self, icon):
        self['BUILTIN'] = icon
        if icon not in self.builtinList:
            warnings.warn('icon "' + str(icon) + '" not part of freeplanes builtin icon list. ' +
                'Freeplane may not display icon. Use an icon from the builtinList instead', SyntaxWarning, stacklevel=2)


class Edge(BaseElement):
    tag = 'edge'
    styleList = ['linear', 'bezier', 'sharp_linear', 'sharp_bezier', 'horizontal', 'hide_edge']
    widthList = ['thin', '1', '2', '4', '8']
    _attribSpecs = {'COLOR': str, 'STYLE': styleList, 'WIDTH': widthList}

    def set_style(self, style):
        self['STYLE'] = style
        if style not in self.styleList:
            warnings.warn('edge style "' + str(style) + '" not part of freeplanes edge styles list. ' +
                'Freeplane may not display edge. Use a style from the styleList instead', SyntaxWarning, stacklevel=2)
    
class Attribute(BaseElement):
    tag = 'attribute'
    _attribs = {'NAME': '','VALUE': ''}
    _attribSpecs = {'NAME': str, 'VALUE': str, 'OBJECT': str}

class Properties(BaseElement):
    tag = 'properties'
    _attribs = {'show_icon_for_attributes': True, 'show_note_icons': True, 'show_notes_in_map': False}
    _attribSpecs = {'show_icon_for_attributes': bool, 'show_note_icons': bool, 'show_notes_in_map': bool}

class ArrowLink(BaseElement):
    tag = 'arrowlink'
    _attribs = {'DESTINATION': ''}
    _attribSpecs = {'COLOR': str, 'DESTINATION': str, 'ENDARROW': str, 'ENDINCLINATION': str, 'ID': str,
                    'STARTARROW': str, 'STARTINCLINATION': str, 'SOURCE_LABEL': str, 'MIDDLE_LABEL': str,
                    'TARGET_LABEL': str, 'EDGE_LIKE': bool}

class RichContent(BaseElement):
    tag = 'richcontent'
    _attribs = {'TYPE': 'NODE'}
    _attribSpecs = {'TYPE': ['NODE', 'NOTE']}
    html = ''  # string version of html code! But we don't include the <html> tag since that's redundant

class AttributeLayout(BaseElement):
    tag = 'attribute_layout'

class AttributeRegistry(BaseElement):
    tag = 'attribute_registry'
    _attribs = {'SHOW_ATTRIBUTES': 'all'}  # if we select 'all' the element should be omitted from file.
    _attribSpecs = {'SHOW_ATTRIBUTES': ['selected', 'all', 'hide']}