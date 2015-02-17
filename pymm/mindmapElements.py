from uuid import uuid4
import warnings
import re
# see http://freeplane.sourceforge.net/wiki/index.php/Current_Freeplane_File_Format for file specifications
# terminology: elem, element = MindMap Elements (no etree elements allowed! Use a mmFactory to convert those

# if you want to update __all__ simply run dir(mindmapElements) (after
# import) to list all available modules. Then remove unwanted modules
 

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
        subchildren = self[:]             # sloppy, but it works. And elements are reordered later anyways.
        for element in subchildren:       # what really matters is that the order of elements of the same tag are not
            self._holder.remove(element)  # altered.
        subchildren[index] = elem
        for element in subchildren:
            self._holder.append(element)

    def __delitem__(self, key):
        element = self[key]
        index = self._holder.index(element)
        del self._holder[index]

    def __contains__(self, element):
        return element in self[:]

    def __len__(self):
        return len(self[:])

    def append(self, element):
        self._holder.append(element)

    def extend(self, elements):
        self._holder.extend(elements)

    def remove(self, element):
        self._holder.remove(element)

    def __str__(self):
        return 'Accessor for: ' + str(self._tags)

    def __repr__(self):
        return '<' + str(self)[:15] + '...'*(len(str(self)) > 15) + ' @' + hex(id(self)) + '>'

    @classmethod
    def constructor(cls, tags):
        def element_access_construction(element):  # just call self.nodes() or self.clouds(), self.etc... to initialize
            return cls(element, tags)
        return element_access_construction


class BaseElement(object):
    """ pymm's Base Element. Can represent any element that xml.etree.ElementTree can.

    BaseElement includes additional attributes to improve upon ElementTree's approach.
    It stores all its children in a list that you can access through explicit slicing or indexing of BaseElement.
    e.g.: BaseE[:], BaseE[0], etc. Native iteration through children is NOT supported. Use slicing for child iteration.
    append(), extend(), index(), pop(), and remove() are usable functions for accessing an element's children.
    BaseElement stores xml attributes in a dictionary, which can be accessed as if the element sub-classed Dict.
    e.g.: BaseE['TEXT'] or BaseE['SIZE'] can access BaseElement's attributes TEXT and SIZE, respectively. xml
    attributes are those key=value declarations that exist within an xml-elements opening (<) and closing (>) tags.
    The functions items(), keys(), and update() are used to access BaseElement's attributes.
    """
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

    def __init__(self, attribs={}, **kwargs):
        self._children = list(self._children) + []
        self._attribs = self._attribs.copy()  # copy all class lists/dicts into instance
        self._strConstructors = list(self._strConstructors) + []
        self.specs = self.specs.copy()
        self._attribs.update(attribs)
        for k, v in kwargs.items():  # make this call different than updating _attribs directly because it's more likely
            self[k] = v  # that a developer specifically typed this out. This will error check it

    def __contains__(self, key_or_element):
        """ Returns if key_or_element is part of this Elements dictionary or children, respectively.
        :param key_or_element: dictionary key (string) OR child element.
        :return: Boolean
        """
        if isinstance(key_or_element, str):
            return key_or_element in self._attribs
        if key_or_element in self._children:
            return True
        return False

    def findall(self, tag):
        """ Return all child elements with matching tag. Return all children if '*' passed in.

        :param tag: child element tag (ex. 'node', 'hook', 'map', etc.)
        :return: list of matching children. Return empty list if none found.
        """
        if tag == '*':
            return self._children
        matching = []
        for element in self[:]:
            if element.tag == tag:
                matching.append(element)
        return matching
            
    def __len__(self):
        """ Return number of children in node """
        return len(self[:])

    def __getitem__(self, index_or_key):
        """ Return dictionary value or child element(s) if passed value is key, or index / slice, respectively.

        :param index_or_key:
        :return child element OR attribute value: depending if param passed was index/slice or key string, respectively
        """
        if isinstance(index_or_key, str):
            return self._attribs[index_or_key]
        return self._children[index_or_key]

    def __setitem__(self, index_or_key, elements_or_value):
        """ Set Element's children or attribute

        :param index_or_key: list index / slice or dictionary key. If dictionary key, key MUST be string
        :param elements_or_value: child element(s) to set, OR dictionary value.
        """
        if isinstance(index_or_key, str):
            self._setdictitem(index_or_key, elements_or_value)  # error-check self._attribs[key] = value
        else:
            index, child = index_or_key, elements_or_value
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
        """  Error check (key: value) pair against Element.specs, warn user if mismatch found but still allow operation.

        :param key: dictionary key (string expected)
        :param value: dictionary value
        """
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

    def __delitem__(self, index_or_key):
        """ Delete element child or dictionary key: value pair given an index / slice or key, respectively

        :param index_or_key: Dictionary value (string) or index / slice
        """
        if isinstance(index_or_key, str):
            del self._attribs[index_or_key]
        else:
            element = self._children[index_or_key]
            if hasattr(element, 'parent'):
                element.parent = None
            del self._children[index_or_key]

    def index(self, element):
        """ Return index of child element in Element's children list """
        return self._children.index(element)

    def append(self, element):
        """ Append element to Element's children list """
        self._children.append(element)
        if hasattr(element, 'parent'):
            element.parent = self

    def extend(self, elements):
        """ Extends Element's children """
        if isinstance(elements, BaseElement):
            raise TypeError('can only assign an iterable')
        for element in elements:
            self.append(element)  # we call here so that we can set parent attribute. Unfortunately means its slowish

    def update(self, attribs):
        """ Update Element's attributes """
        for k, v in attribs.items():  # add attributes one at a time, which allows element to warn if passed key is
            self[k] = v               # not part of its specs.

    def remove(self, element):
        """ Remove element from children """
        self._children.remove(element)
        if hasattr(element, 'parent'):
            element.parent = None

    def pop(self, index=-1):
        """ Remove and return element in children list """
        return self._children.pop(index)

    def items(self):
        """ Return attribute items in (key, value) format """
        return self._attribs.items()

    def keys(self):
        """ Return attribute keys """
        return self._attribs.keys()

    def __str__(self):
        """ Construct string representation of self. Configured to display more info: self._strConstructors.append() """
        extras = [' ' + prop + '=' + value for prop, value in self.items() if prop in self._strConstructors]
        s = self.tag + ':'
        for descriptor in extras:
            s += descriptor
        return s

    def __repr__(self):
        """ Return shortened description of self """
        return '<' + str(self)[:13] + '...'*(len(str(self)) > 13) + ' @' + hex(id(self)) + '>'


class Node(BaseElement):
    tag = 'node'
    nodes = ElementAccessor.constructor(['node'])
    _attribs = {'ID': 'random#', 'TEXT': ''}
    specs = {'BACKGROUND_COLOR': str, 'COLOR': str, 'FOLDED': bool, 'ID': str, 'LINK': str,
             'POSITION': ['left', 'right'], 'STYLE': str, 'TEXT': str, 'LOCALIZED_TEXT': str, 'TYPE': str,
             'CREATED': int, 'MODIFIED': int, 'HGAP': int, 'VGAP': int, 'VSHIFT': int, 'ENCRYPTED_CONTENT': str,
             'OBJECT': str, 'MIN_WIDTH': int, 'MAX_WIDTH': int}

    def __init__(self, **kwargs):
        self['ID'] = 'ID_' + str(uuid4().time)[:-1]
        super(Node, self).__init__(**kwargs)
        self.nodes = self.nodes()

    def __str__(self):
        return self.tag + ': ' + self['TEXT'].replace('\n', '')


class Map(BaseElement):
    tag = 'map'
    _attribs = {'version': 'freeplane 1.3.0'}
    specs = {'version': str}
    nodes = ElementAccessor.constructor(['node'])

    def __init__(self, **kwargs):
        super(Map, self).__init__(**kwargs)
        self.nodes = self.nodes()

    def setroot(self, root):
        self.nodes[:] = [root]

    def getroot(self):
        return self.nodes[0]  # there should only be one node on Map!


class Cloud(BaseElement):
    tag = 'cloud'
    shapeList = ['ARC', 'STAR', 'RECT', 'ROUND_RECT']
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
                   'males', 'fema', 'group', 'ksmiletris', 'smiley-neutral', 'smiley-oh', 'smiley-angry', 'smiley_bad',
                   'licq', 'penguin', 'freemind_butterfly', 'bee', 'forward', 'back', 'up', 'down', 'addition',
                   'subtraction', 'multiplication', 'division']
    # you can add additional icons right here if one is
    # missing by simply appending to the class builtin list: Icon.builtinList.append(icon-name)
    _attribs = {'BUILTIN': 'bookmark'}
    specs = {'BUILTIN': builtinList}

    def set_icon(self, icon):
        self['BUILTIN'] = icon
        if icon not in self.builtinList:
            warnings.warn('icon "' + str(icon) + '" not part of freeplanes builtin icon list. ' +
                          'Freeplane may not display icon. Use an icon from the builtinList instead', SyntaxWarning,
                          stacklevel=2)


class Edge(BaseElement):
    tag = 'edge'
    styleList = ['linear', 'bezier', 'sharp_linear', 'sharp_bezier', 'horizontal', 'hide_edge']
    widthList = ['thin', '1', '2', '4', '8']
    specs = {'COLOR': str, 'STYLE': styleList, 'WIDTH': widthList}

    def set_style(self, style):
        self['STYLE'] = style
        if style not in self.styleList:
            warnings.warn('edge style "' + str(style) + '" not part of freeplanes edge styles list. ' +
                          'Freeplane may not display edge. Use a style from the styleList instead', SyntaxWarning,
                          stacklevel=2)


class Attribute(BaseElement):
    tag = 'attribute'
    _attribs = {'NAME': '', 'VALUE': ''}
    specs = {'NAME': str, 'VALUE': str, 'OBJECT': str}


class Properties(BaseElement):
    tag = 'properties'
    _attribs = {'show_icon_for_attributes': True, 'show_note_icons': True, 'show_notes_in_map': False}
    specs = {'show_icon_for_attributes': bool, 'show_note_icons': bool, 'show_notes_in_map': bool}


class ArrowLink(BaseElement):
    tag = 'arrowlink'
    _attribs = {'DESTINATION': ''}
    specs = {'COLOR': str, 'DESTINATION': str, 'ENDARROW': str, 'ENDINCLINATION': str, 'ID': str, 'STARTARROW': str,
             'STARTINCLINATION': str, 'SOURCE_LABEL': str, 'MIDDLE_LABEL': str, 'TARGET_LABEL': str, 'EDGE_LIKE': bool}


class AttributeLayout(BaseElement):
    tag = 'attribute_layout'


class AttributeRegistry(BaseElement):
    tag = 'attribute_registry'
    _attribs = {'SHOW_ATTRIBUTES': 'all'}  # if we select 'all' the element should be omitted from file.
    specs = {'SHOW_ATTRIBUTES': ['selected', 'all', 'hide']}


class RichContent(BaseElement):
    # there is no need to use richcontent in freeplane. all nodes will automatically convert their html to richcontent
    #   if their html contains html tags (such as <b>). And will auto-downgrade from richcontent if you replace
    #   a nodes html-like html with plaintext  (all accessed using node.html). Unfortunately, the richcontent that is
    #   available is fully-fledged html. So trying to set up something to parse it will need to simply have a
    #   getplaintext() function to allow the user to quickly downgrade text to something readable. Until that time, html
    #   text is going to be very messy.
    tag = 'richcontent'
    _strConstructors = ['TYPE']
    specs = {'TYPE': str}
    html = ''

    def is_html(self):
        return bool(re.findall(r'<[^>]+>', self.html))


class NodeText(RichContent):
    # developer does not need to create NodeText, ever. This is created by the node itself during reversion if the
    #   nodes html includes html tags
    _attribs = {'TYPE': 'NODE'}


class NodeNote(RichContent):
    _attribs = {'TYPE': 'NOTE'}


class NodeDetails(RichContent):
    _attribs = {'TYPE': 'DETAILS'}
