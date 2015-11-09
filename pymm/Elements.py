"""
    Pymm mindmaps are composed of a hierarchical tree composed of elements
    defined within this Elements module. The hierarchical format is exact or
    similar in structure to the trees constructed by xml.etree, but with
    different syntax for traversing and modifying the tree.

    If you want to make your own element, see the example below:

    class ExampleElement:
        # [REQUIRED]. Only way for a Factory (which you must code) to
        # convert the element of type 'tag'. Examples include 'node' or 'cloud'
        tag = ''
        # [OPTIONAL] pre-define default element attributes
        attrib = {}
        # [OPTIONAL] pre-define attribute types (like bool, str, int, float).
        specs = {}
        # [OPTIONAL] list of attribs that are used when constructing str(self)
        _display_attrib = []
"""
from uuid import uuid4
import warnings
import re
import copy
from . import _elementAccess
import types
# http://freeplane.sourceforge.net/wiki/index.php/Current_Freeplane_File_Format


class BaseElement:
    """ pymm's Base Element. All other elements inherit from BaseElement, which
    represents an element in a similar style to xml.etree.ElementTree with
    enhancements aimed at providing faster mindmap manipulation. Each element
    has a specific identifier--a tag--that specifies what type of element it
    is. If a specific xml element type does not have a corresponding pymm
    element, it will become a BaseElement, but the corresponding "BaseElement"
    tag will be replaced with the actual xml element's tag.

    
    :param tag: the tag specifying type of element
    :param parent: a link to the element's parent element
    :param specs:     """
    tag = 'BaseElement'
    parent = None

    #: _text and _tail are here for compatibility reasons. They correspond to
    #: xml.etree's .text and .tail, respectively. _text is the text between the
    #: xml element's start tag, and the next element. _tail is the text after
    #: the xml element's ending tag and before the next element. These 
    #: attributes are not necessary, but help improve the plaintext readability
    #: of the written .mm file
    _text = ''
    _tail = ''
    
    #: BaseElement stores all its children in a list that you can access and
    #: modify @ element.children. This is dissimilar to xml.etree, which
    #: allows implicit indexing of children. If you want to access children
    #: within pymm, you will need to access from the children list.
    children = []

    #: xml attributes are stored in the same fastion as xml.etree: in a
    #: dictionary called attrib. xml attributes are key=value declarations
    #: that exist within an xml-element's opening (<) and closing (>) tags.
    #: For example, the attrib for an example element:
    #: <edge COLOR='ff0000', STYLE='linear', WIDTH='2'>
    #: would be:
    #: attrib = {'COLOR': 'ff0000', 'STYLE': 'linear', 'WIDTH': '2'}
    #: If you modify attrib in a class, thereafter each instance of that class
    #: will include your attrib version unless overwritten when decoding
    #: from an existing xml Element.
    attrib = {}

    #: to improve readability of interactions with pymm elements,
    #: _display_attrib may contain specific attribs that will be used in the
    #: representation of an element.
    _display_attrib = []

    #: a dictionary of expected xml attributes and a list of their expected
    #: types (i.e. int, list, string, etc.).When changing an element's 
    #: attribute, the new attribute will be checked against the specs, and a
    #: warning generated if the new attribute does not match the specs. Can be
    #: modified to allow additional specs. I.E. elem.attrib['TEXT'] = 'HI 5'
    #: sets the element's TEXT attrib to 'HI 5'. If specs contains the key
    #: 'TEXT', the type of value 'HI 5' (str) will be checked against the
    #: value of specs['TEXT'], and a warning generated if they do not match
    #: list all possible attributes of an element and valid entries / types in
    #: a list or standalone: [str, int, 'thin', etc.], str, int, 'thin', etc.
    specs = {}

    def __new__(cls, *args, **kwargs):
        """DO NOT OVERRIDE W/O super. override __init__ for most stuff. Copy
        all the mutable class attributes such as children, attrib, specs, and 
        _display_attrib into the class instance to prevent user from
        accidentally adding to class-wide attributes if he overrides __init__
        and forgets to call super().__init__ first. It is still possible for
        user to change class-wide variables, but this will make it less likely
        he will do so with an instance of the class. We do not use *args or
        **kwargs in __new__ because developer may want to override behavior of
        arguments
        """
        self = super().__new__(cls)
        self.children = copy.deepcopy(self.children)
        self.attrib = copy.deepcopy(self.attrib)
        self._display_attrib = copy.deepcopy(self._display_attrib)
        self.specs = copy.deepcopy(self.specs)
        self._init_all_preconstructed_element_accessors()
        return self

    def _init_all_preconstructed_element_accessors(self):
        """locate all preconstructed child access functions and run them:
        get back child access object, and set using same attribute name.
        things like self.nodes. Makes sure that this is a new, separate
        instance from the class itself. This feels computationally heavy tho...
        basically a catch-all version of self.nodes = self.nodes()
        """
        for varName in dir(self):
            func = getattr(self, varName)
            if type(func) == types.MethodType and func.__name__ == 'this_function_gets_automatically_run_inside_elements__new__':
                childAccessor = func()
                setattr(self, varName, childAccessor)

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            self.attrib[k] = v

    def __str__(self):
        """Construct string representation of self. Configured to display
        attrib values listed in self._display_attrib
        """
        identifying = [
            ' ' + prop + '=' + val for prop, val in self.attrib.items() if
            prop in self._display_attrib
        ]
        return self.tag + ': ' + ''.join(identifying)

    def __repr__(self):
        """Return shortened description of self, encapsulated in < > brackets
        like an xml-element
        """
        string = str(self)
        shorter = string[:13]
        ellipses = '...'
        if shorter == string:
            ellipses = ''
        return '<' + shorter + ellipses + ' @' + hex(id(self)) + '>'

    def findall(self, **kwargs):
        """Return all child elements matching regex parameters.

        :param tag_regex: regex matching child element tag (e.g. r'node')
        :param attrib_regex: regex matching keys, values in child.attrib.
                             Requires dictionary-format regex key/value pairs.
                             e.g. {r'COLOR': r'ff[0-9a-f]{4}'}
        :return: list of matching children. Return empty list if none found.
        """
        subset = _elementAccess.ChildSubset(self, **kwargs) 
        return list(subset)

    def find(self, **kwargs):
        subset = _elementAccess.ChildSubset(self, **kwargs)
        try:
            return subset[0]
        except IndexError:
            return None


class ImplicitNodeAttributes:
    """attributes are excel like tables (2-cells wide each) that define a
    key-value pair they are attached (visually) beneath a Node in Freeplane. 
    This class allows the user to define attributes on a node with implicit
    indexing, iteration, and contains-checking like a dictionary but with only
    the .items() method exposed. You can get the attribute dictionary directly
    by calling .get_attributes()
    """

    def __setitem__(self, key, val):
        self._attribute[key] = val

    def __getitem__(self, key):
        return self._attribute[key]

    def __iter__(self):
        return iter(self._attribute)

    def __contains__(self, key):
        return self._attribute.__contains__(self, key)

    def __delitem__(self, key):
        del self._attribute[key]

    def items(self):
        return self._attribute.items()

    def get_attributes(self):
        return self._attribute


class Node(ImplicitNodeAttributes, BaseElement):
    """The most common element in a mindmap. The Node is the visual circle in
    freeplane, with an expandable branch of children. A Node contains text
    you type, contains pictures, urls or links to other nodes, and can be made
    visually distict through clouds, edge-line colors, or rich-text formatting.
    A Node contains an ID and text by default
    """
    tag = 'node'
    nodes = property(*_elementAccess.ChildSubset.setup(tag_regex=r'node'))
    attrib = {'ID': 'random#', 'TEXT': ''}
    # _attribute is node-specific, excel-like tables underneath a node that
    # have key/value pairs
    _attribute = {}
    # cloud automatically gets/sets a cloud within children
    cloud = property(*_elementAccess.SingleChild.setup(tag_regex=r'cloud'))
    # note automaticaly gets/sets a note within children
    note = property(*_elementAccess.SingleChild.setup(tag_regex=r'hook',
                                            attrib_regex={r'STYLE': r'NOTE'}))
    specs = {
        'BACKGROUND_COLOR': str, 'COLOR': str, 'FOLDED': bool, 'ID': str,
        'LINK': str, 'POSITION': ['left', 'right'], 'STYLE': str,  'TEXT': str,
        'LOCALIZED_TEXT': str, 'TYPE': str, 'CREATED': int, 'MODIFIED': int,
        'HGAP': int, 'VGAP': int, 'VSHIFT': int,  'ENCRYPTED_CONTENT': str,
        'OBJECT': str, 'MIN_WIDTH': int, 'MAX_WIDTH': int,
    }

    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls, *args, **kwargs)
        self._attribute = self._attribute.copy()
        return self

    def __init__(self, **kwargs):
        self.attrib['ID'] = 'ID_' + str(uuid4().time).replace('L', '')
        super().__init__(**kwargs)

    def __str__(self):
        return self.tag + ': ' + self.attrib['TEXT'].replace('\n', '')

    def set_text(self, text):
        self.attrib['TEXT'] = text

    def get_text(self):
        return self.attrib['TEXT']


class Map(BaseElement):
    """Map is the first element of any mindmap. It is the highest-level
    element and all other elements are sub-children of the Map. Map generally
    contains only two direct children: a Node (root), and MapStyle.
    """
    tag = 'map'
    attrib = {'version': 'freeplane 1.3.0'}
    specs = {'version': str}
    nodes = property(*_elementAccess.ChildSubset.setup(tag_regex=r'node'))
    root = property(*_elementAccess.SingleChild.setup(tag_regex=r'node'))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Cloud(BaseElement):
    """Cloud is a visual indicator around a particular Node, making it stand
    out above other Nodes. As a child of the Node, a cloud applies its visual
    style to its parent Node and that nodes children and sub-children. The
    cloud has two main attributes to control its visual style: SHAPE, and
    COLOR. SHAPE must be chosen from Cloud.shapeList, while COLOR can be any 
    string representation starting with #, and using two hexidecimal characters
    for each color in RGB
    """
    tag = 'cloud'
    shapeList = ['ARC', 'STAR', 'RECT', 'ROUND_RECT']
    attrib = {'COLOR': '#f0f0f0', 'SHAPE': 'ARC'}
    specs = {'COLOR': str, 'SHAPE': shapeList, 'WIDTH': str}
    _display_attrib = ['COLOR', 'SHAPE']

    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls)
        self.shapeList = copy.deepcopy(self.shapeList)
        return self


class Hook(BaseElement):
    """Hook is used frequently throughout a mindmap to represent different
    added elements. Hook is often subclassed as a result. The NAME attribute of
    a hook tells what type of hook it is. Add a Hook as a child to apply the
    effect.
    """
    tag = 'hook'
    attrib = {'NAME': 'overwritten'}
    specs = {'NAME': str}


class EmbeddedImage(Hook):
    """place EmbeddedImage as the child of a Node to embed the image into the
    given node. Must supply the full or relative path to the image using
    EmbeddedImage['URI'] = path
    """
    attrib = {'NAME': 'ExternalObject'}
    specs = {'NAME': str, 'URI': str, 'SIZE': float}


class MapConfig(Hook):
    """MapConfig is only used once in a mindmap: as the child of RootNode. It
    provides a few configurations to the map, such as zoom-level, or
    max_node_width which defines how many characters long a node runs before
    wrapping.
    """
    attrib = {'NAME': 'MapStyle', 'zoom': 1.0}
    specs = {'NAME': str, 'max_node_width': int, 'zoom': float}


class Equation(Hook):
    """Equation allows a LaTeX-style equation to be inserted into a particular
    Node. Define the equation using Equation['EQUATION'] = latex-string
    """
    attrib = {'NAME': 'plugins/latex/LatexNodeHook.properties'}
    specs = {'NAME': str, 'EQUATION': str}


class AutomaticEdgeColor(Hook):
    """AutomaticEdgeColor is a child of RootNode. If AutomaticEdgeColor is
    present, then creating new child nodes of the root will have their edge
    automatically colored differently. The COUNTER attribute keeps track of how
    many edges have been automatically colored.
    """
    attrib = {'NAME': 'AutomaticEdgeColor', 'COUNTER': 0}
    specs = {'NAME': str, 'COUNTER': int}


class MapStyles(BaseElement):
    """MapStyles is the child of the MapConfig Hook. MapStyles defines the
    styles of all the nodes. MapStyles contains multiple StyleNodes, each 
    defining a new style.
    """
    tag = 'map_styles'


class StyleNode(BaseElement):
    """StyleNode defines the characteristics of a style. Its LOCALIZED_TEXT
    attribute is the same name used by a Node's LOCALIZED_STYLE_REF, when
    choosing what style to use. StyleNodes share their attributes through
    inheritance. Their children StyleNodes will contain the same attributes as 
    their parents + their unique attributes.
    """
    tag = 'stylenode'
    specs = {
        'LOCALIZED_TEXT': str, 'POSITION': ['left', 'right'], 'COLOR': str,
        'MAX_WIDTH': int, 'STYLE': str,
    }


class Font(BaseElement):
    """Font influence the visual style of text. Font should be a child of a
    StyleNode to change that StyleNode's text appearance
    """
    tag = 'font'
    attrib = {'BOLD': False, 'ITALIC': False, 'NAME': 'SansSerif', 'SIZE': 10}
    specs = {'BOLD': bool, 'ITALIC': bool, 'NAME': str, 'SIZE': int}


class Icon(BaseElement):
    """Add a small icon to the front of a node by adding Icon as a Node's
    child. Icon['BUILTIN'] = builtinIcon sets the icon. You can choose a 
    built-in icon from the list: Icon.builtinList.
    """
    tag = 'icon'
    _display_attrib = ['BUILTIN']
    builtinList = [
        'help', 'bookmark', 'yes', 'button_ok', 'button_cancel', 'idea',
        'messagebox_warning', 'stop-sign', 'closed', 'info', 'clanbomber',
        'checked', 'unchecked', 'wizard', 'gohome', 'knotify', 'password',
        'pencil', 'xmag', 'bell', 'launch', 'broken-line', 'stop', 'prepare',
        'go', 'very_negative', 'negative', 'neutral', 'positive',
        'very_positive', 'full-1', 'full-2', 'full-3', 'full-4', 'full-5',
        'full-6', 'full-7', 'full-8', 'full-9', 'full-0', '0%', '25%', '50%',
        '75%', '100%', 'attach', 'desktop_new', 'list', 'edit', 'kaddressbook',
        'pencil', 'folder', 'kmail', 'Mail', 'revision', 'video', 'audio',
        'executable', 'image', 'internet', 'internet_warning', 'mindmap',
        'narrative', 'flag-black', 'flag-blue', 'flag-green', 'flag-orange',
        'flag-pink', 'flag', 'flag-yellow', 'clock', 'clock2', 'hourglass',
        'calendar', 'family', 'female1', 'female2', 'females', 'male1',
        'male2', 'males', 'fema', 'group', 'ksmiletris', 'smiley-neutral',
        'smiley-oh', 'smiley-angry', 'smiley_bad', 'licq', 'penguin',
        'freemind_butterfly', 'bee', 'forward', 'back', 'up', 'down',
        'addition', 'subtraction', 'multiplication', 'division'
    ]
    attrib = {'BUILTIN': 'bookmark'}
    specs = {'BUILTIN': builtinList}

    def set_icon(self, icon):
        self.attrib['BUILTIN'] = icon
        if icon not in self.builtinList:
            warnings.warn(
                'icon "' + str(icon) + '" not part of freeplanes builtin icon '
                + 'list. Freeplane may not display icon. Use an icon from the '
                + 'builtinList instead', SyntaxWarning, stacklevel=2
            )

    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls)
        self.builtinList = copy.deepcopy(self.builtinList)
        return self


class Edge(BaseElement):
    """Edge defines the look of the lines (edges) connecting nodes. You can
    change the color, style, and width attrib. Any attrib not defined will be
    visually inherited from a parent's edge. The COLOR attrib must be any
    string starting with # and having two hexidecimal characters for
    each color in RGB. The STYLE attrib must be one of the styles in
    Edge.styleList. The WIDTH attrib must be 'thin' or a string
    representation of any integer. Any edge width > '4' is visually
    unappealing.
    """
    tag = 'edge'
    styleList = [
        'linear', 'bezier', 'sharp_linear', 'sharp_bezier', 'horizontal',
        'hide_edge'
    ]
    widthList = ['thin', int]
    specs = {'COLOR': str, 'STYLE': styleList, 'WIDTH': widthList}

    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls)
        self.styleList = copy.deepcopy(self.styleList)
        self.widthList = copy.deepcopy(self.widthList)
        return self

class Attribute(BaseElement):
    """(Node) Attributes display underneath a Node like a table, with NAME
    attribute to the left, and VALUE to the right. You can use Node Attributes
    to specify categories / traits of a specific Node. You can visually hide
    Node Attributes by setting AttributeRegistry['SHOW_ATTRIBUTES'] = 'hide'.
    Additionally, you can hide or show an icon indicating the presence of 
    Attributes on a Node through the Properties Element.
    """
    tag = 'attribute'
    attrib = {'NAME': '', 'VALUE': ''}
    specs = {'NAME': str, 'VALUE': str, 'OBJECT': str}


class Properties(BaseElement):
    """Control the appearance of notes on Nodes, and icons, note, or attribute 
    presence on a node. Is child of MapStyle
    """
    tag = 'properties'
    attrib = {
        'show_icon_for_attributes': 'true', 'show_note_icons': 'true',
        'show_notes_in_map': 'true'
    }
    specs = {
        'show_icon_for_attributes': bool, 'show_note_icons': bool,
        'show_notes_in_map': bool
    }


class ArrowLink(BaseElement):
    tag = 'arrowlink'
    attrib = {'DESTINATION': ''}
    specs = {
        'COLOR': str, 'DESTINATION': str, 'ENDARROW': str, 
        'ENDINCLINATION': str, 'ID': str, 'STARTARROW': str, 
        'STARTINCLINATION': str, 'SOURCE_LABEL': str, 'MIDDLE_LABEL': str,
        'TARGET_LABEL': str, 'EDGE_LIKE': bool
    }


class AttributeLayout(BaseElement):
    tag = 'attribute_layout'


class AttributeRegistry(BaseElement):
    tag = 'attribute_registry'
    attrib = {'SHOW_ATTRIBUTES': 'all'}
    specs = {'SHOW_ATTRIBUTES': ['selected', 'all', 'hide']}


class RichContent(BaseElement):
    """There is no need to use richcontent in freeplane. all nodes will
    automatically convert their html to richcontent if their html contains html
    tags (such as <b>). And will auto-downgrade from richcontent if you replace
    a nodes html-like html with plaintext  (all accessed using node.html).
    Unfortunately, the richcontent that is available is fully-fledged html. So
    trying to set up something to parse it will need to simply have a 
    getplaintext() function to allow the user to quickly downgrade text to 
    something readable. Until that time, html text is going to be very messy.
    """
    tag = 'richcontent'
    _display_attrib = ['TYPE']
    specs = {'TYPE': str}
    html = ''

    def is_html(self):
        return bool(re.findall(r'<[^>]+>', self.html))


class NodeText(RichContent):
    """Developer does not need to create NodeText, ever. This is created by the
    node itself during reversion if the nodes' html includes html tags
    """
    attrib = {'TYPE': 'NODE'}


class NodeNote(RichContent):
    attrib = {'TYPE': 'NOTE'}


class NodeDetails(RichContent):
    attrib = {'TYPE': 'DETAILS'}
