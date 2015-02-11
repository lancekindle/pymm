from uuid import uuid4
import warnings
import re
# see http://freeplane.sourceforge.net/wiki/index.php/Current_Freeplane_File_Format for file specifications
#terminology: elem, element = MindMap Elements (no etree elements allowed! Use a mmFactory to convert those


class ElementAccessor(object):
    # this object is intended to hold a reference to ONE element. When initialized with a set of tags,
    # the object will search its reference element for those tags and allow access to them, including indexing,
    # removal, deletion, etc. to iterate, simply use self[:] e.g. node.nodes[:]

    def __init__(self, element, tags=[]):
        self._tags = list(tags[:])
        self._holder = element

    def __getitem__(self, index):
        elements = []
        for tag in self._tags:
            elements.extend(self._holder.findall(tag))
        return elements[index]

    def __setitem__(self, index, elem):   # removes elements, then re-appends them after modification.
        allElements = self[:]             # sloppy, but it works. And elements are reordered later anyways.
        for element in allElements:       # what really matters is that the order of elements of the same tag are not
            self._holder.remove(element)  # altered.
        allElements[index] = elem
        for element in allElements:
            self._holder.append(element)

    def __delitem__(self, key):
        element = self[key]
        index = self._holder.index(element)
        del self._holder[index]

    def __contains__(self, element):
        return element in self[:]

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

    @classmethod
    def constructor(cls, tags):
        def element_access_construction(element):  # just call self.nodes() or self.clouds(), self.etc... to initialize
            return cls(element, tags)
        return element_access_construction



class BaseElement(object):
    # BaseElement for basic child access functionality
    # NOTE: It is extremely dangerous to define lists and dictionaries on a class-level.If you forget to initialize it
    # via: self._str = list(self._str...) or self.dict = self.dict.copy() then any changes will affect the CLASS VARS!
    # (because the self.var would actually be pointing to the class variable)
    # this caught me at first, but since I re-initialize them in the init, everything is good.
    tag = 'BaseElement'  # must set to cloud, hook, edge, etc.
    parent = None
    _text = ''    # equivalent to ElementTree's .text  -- text between start tag and next element   # I only keep this
    _tail = ''    # equivalent to ElementTree's .tail  -- text after end tag                        # for compatibility
    _children = []  # all child elements including nodes
    _attribs = {}  # pre-define these (outside of init like this) in other classes to define default element attribs
    _strConstructors = []  # list of attribs to use in str(self) construction
    specs = {}  # list all possible attributes of an element and its choices [...] or value type (str, int, etc.)
    #limiters = {}  # For limiting children. requires a tag, an identifying set of specs (optional), and number allowed.

    def __init__(self, attribs={}, **kwargs):
        self._children = list(self._children) + []
        self._attribs = self._attribs.copy()  # copy all class lists/dicts into instance
        self._strConstructors = list(self._strConstructors) + []
        self.specs = self.specs.copy()
        #self.limiters = self.limiters.copy()
        self._attribs.update(attribs)
        self.update(kwargs)  # make this call different than updating _attribs directly because it's more likely that
                             # a developer specifically typed this out. This will error check it

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

    def __setitem__(self, key, value):
        if isinstance(key, str):
            self._setdictitem(key, value)#._attribs[key] = value
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

    def _setdictitem(self, key, value):  # a way to force error checking on setting of attrib values.
        self._attribs[key] = value  # regardless of whether we warn developer, add attribute.
        if key not in self.specs:   # add keywords and arguments to element.specs to address unnecessary warnings
            warnings.warn('<' + self.tag + '> does not have "' + key + '" spec', UserWarning, stacklevel=2)
        else:  # then key IS in attribSpecs
            vtype = self.specs[key]
            try:
                if isinstance(vtype, list):
                    vlist = vtype  # the value type is actually a list of possible string values
                    if value not in vlist:
                        vtype = ' one of ' + str(vtype)  # change vtype to string for warning user. vtype is useless now
                        raise ValueError
                elif not vtype == type(value):
                    raise ValueError
            except ValueError:
                warnings.warn('<' + self.tag + '>[' + key + '] expected ' + str(vtype) + ', got ' + str(value) +
                          ' instead: ' + str(type(value)), UserWarning, stacklevel=2)

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
        if isinstance(elements, BaseElement):
            raise TypeError('can only assign an iterable')
        for element in elements:
            self.append(element)  # we call here so that we can set parent attribute. Unfortunately means its slowish

    def update(self, attribs):
        for k, v in attribs.items():  # add attributes one at a time, which allows element to warn if passed key is
            self[k] = v               # not part of its specs.

    def remove(self, element):
        self._children.remove(element)
        if hasattr(element, 'parent'):
            element.parent = None

    def items(self):
        return self._attribs.items()

    def keys(self):
        return self._attribs.keys()

    def __str__(self):
        extras = [' ' + prop + '=' + value for prop, value in self.items() if prop in self._strConstructors]
        s = self.tag + ':'
        for descriptor in extras:
            s += descriptor
        return s

    def __repr__(self):
        return '<' + str(self)[:13] + '...'*(len(str(self))>13) +' @' + hex(id(self)) + '>'


class Node(BaseElement):
    tag = 'node'
    nodes = ElementAccessor.constructor(['node'])
    _attribs = {'ID': 'ID_' + str(uuid4().time)[:-1], 'TEXT': ''}
    specs = {'BACKGROUND_COLOR': str, 'COLOR': str, 'FOLDED': bool, 'ID': str, 'LINK': str,
                    'POSITION': ['left', 'right'], 'STYLE': str, 'TEXT': str, 'LOCALIZED_TEXT': str, 'TYPE': str,
                    'CREATED': int, 'MODIFIED': int, 'HGAP': int, 'VGAP': int, 'VSHIFT': int, 'ENCRYPTED_CONTENT': str,
                    'OBJECT': str, 'MIN_WIDTH': int, 'MAX_WIDTH': int}

    def __init__(self, **kwargs):
        super(Node, self).__init__(**kwargs)
        self.nodes = self.nodes()

    def __str__(self):
        return self.tag + ': ' + self['TEXT'].replace('\n', '')

class Map(BaseElement):
    tag = 'map'
    _attribs = {'version': 'freeplane 1.3.0'}
    specs = {'version': str}

    def __init__(self, **kwargs):
        super(Map, self).__init__(**kwargs)
        self.nodes = ElementAccessor(self, ['node'])

    def setroot(self, root):
        self.nodes[:] = [root]

    def getroot(self):
        return self.nodes[0]  # there should only be one node on Map!


class Cloud(BaseElement):
    tag = 'cloud'
    shapeList = ['ARC', 'STAR','RECT','ROUND_RECT']
    _attribs = {'COLOR': '#333ff', 'SHAPE': 'ARC'}  # set defaults
    specs = {'COLOR': str, 'SHAPE': shapeList, 'WIDTH': str}
    _strConstructors = ['COLOR', 'SHAPE']  # extra information to send during call to __str__


class Hook(BaseElement):
    tag = 'hook'
    _attribs = {'NAME': 'overwritten'}
    specs = {'NAME': str}


class EmbeddedImage(Hook):
    _attribs = {'NAME': 'ExternalObject'}
    specs = {'NAME': str, 'URI': str, 'SIZE': float}


class MapConfig(Hook):
    _attribs = {'NAME': 'MapStyle', 'zoom': 1.0}
    specs = {'NAME': str, 'max_node_width': int, 'zoom': float}


class Equation(Hook):
    _attribs = {'NAME': 'plugins/latex/LatexNodeHook.properties'}
    specs = {'NAME': str, 'EQUATION': str}


class AutomaticEdgeColor(Hook):
    _attribs = {'NAME': 'AutomaticEdgeColor', 'COUNTER': 0}
    specs = {'NAME': str, 'COUNTER': int}


class MapStyles(BaseElement):
    tag = 'map_styles'


class StyleNode(BaseElement):
    tag = 'stylenode'
    specs = {'LOCALIZED_TEXT': str, 'POSITION': ['left', 'right'], 'COLOR': str, 'MAX_WIDTH': int, 'STYLE': str}


class Font(BaseElement):
    tag = 'font'
    _attribs = {'BOLD': False, 'ITALIC': False, 'NAME': 'SansSerif', 'SIZE': 10}  # set defaults
    specs = {'BOLD': bool, 'ITALIC': bool, 'NAME': str, 'SIZE': int}


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
    specs = {'BUILTIN': builtinList}

    def set_icon(self, icon):
        self['BUILTIN'] = icon
        if icon not in self.builtinList:
            warnings.warn('icon "' + str(icon) + '" not part of freeplanes builtin icon list. ' +
                'Freeplane may not display icon. Use an icon from the builtinList instead', SyntaxWarning, stacklevel=2)


class Edge(BaseElement):
    tag = 'edge'
    styleList = ['linear', 'bezier', 'sharp_linear', 'sharp_bezier', 'horizontal', 'hide_edge']
    widthList = ['thin', '1', '2', '4', '8']
    specs = {'COLOR': str, 'STYLE': styleList, 'WIDTH': widthList}

    def set_style(self, style):
        self['STYLE'] = style
        if style not in self.styleList:
            warnings.warn('edge style "' + str(style) + '" not part of freeplanes edge styles list. ' +
                'Freeplane may not display edge. Use a style from the styleList instead', SyntaxWarning, stacklevel=2)


class Attribute(BaseElement):
    tag = 'attribute'
    _attribs = {'NAME': '','VALUE': ''}
    specs = {'NAME': str, 'VALUE': str, 'OBJECT': str}


class Properties(BaseElement):
    tag = 'properties'
    _attribs = {'show_icon_for_attributes': True, 'show_note_icons': True, 'show_notes_in_map': False}
    specs = {'show_icon_for_attributes': bool, 'show_note_icons': bool, 'show_notes_in_map': bool}


class ArrowLink(BaseElement):
    tag = 'arrowlink'
    _attribs = {'DESTINATION': ''}
    specs = {'COLOR': str, 'DESTINATION': str, 'ENDARROW': str, 'ENDINCLINATION': str, 'ID': str,
                    'STARTARROW': str, 'STARTINCLINATION': str, 'SOURCE_LABEL': str, 'MIDDLE_LABEL': str,
                    'TARGET_LABEL': str, 'EDGE_LIKE': bool}


class AttributeLayout(BaseElement):
    tag = 'attribute_layout'

class AttributeRegistry(BaseElement):
    tag = 'attribute_registry'
    _attribs = {'SHOW_ATTRIBUTES': 'all'}  # if we select 'all' the element should be omitted from file.
    specs = {'SHOW_ATTRIBUTES': ['selected', 'all', 'hide']}


class RichContent(BaseElement):
    ''' there is no need to use richcontent in freeplane. all nodes will automatically convert their html to richcontent
        if their html contains html tags (such as <b>). And will auto-downgrade from richcontent if you replace
        a nodes html-like html with plaintext  (all accessed using node.html). Unfortunately, the richcontent that is
        available is fully-fledged html. So trying to set up something to parse it will need to simply have a
        getplaintext() function to allow the user to quickly downgrade text to something readable. Until that time, html
        text is going to be very messy.
    '''
    tag = 'richcontent'
    _strConstructors = ['TYPE']
    specs = {'TYPE': str}
    html = ''

    def is_html(self):
        return bool(re.findall(r'<[^>]+>', self.html))

class NodeText(RichContent):
    ''' developer does not need to create NodeText, ever. This is created by the node itself during reversion if the
        nodes html includes html tags
    '''
    _attribs = {'TYPE': 'NODE'}


class NodeNote(RichContent):
    _attribs = {'TYPE': 'NOTE'}


class NodeDetails(RichContent):
    _attribs = {'TYPE': 'DETAILS'}