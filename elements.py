from uuid import uuid4


class BaseElement(object):
    # BaseElement for basic child access functionality
    def __init__(self, **kwargs):
        self._attribs = {}
        self.tag = 'invalid'  # must set to cloud, hook, edge, etc.
        self._children = []  # all child elements including nodes
        self._strConstructors = []  # list of attribs to use in construction __str__
        for key, value in kwargs.items():
            self[key] = value

    def _set_default_attribs(self, **kwargs):  # set attribs if not already set
        for key, value in kwargs.items():
            if key not in self:
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

    def append(self, element):
        self._children.append(element)

    def extend(self, elements):
        self._children.extend(elements)

    def remove(self, element):
        self._children.remove(element)

    def items(self):
        return self._attribs.items()

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

    def __init__(self, **kwargs):
        super(Node, self).__init__(**kwargs)
        self.tag = 'node'
        self._recognizableNodeTags = ['node']  # any element with matching tag will be accessible with node.nodes()
            # So if you wish add a new nodetype, simply add it using node.getRecognizableNodeTags().add(tag)
        self.text = '' # should initialize some html editor instance. That allows you to edit an html document
        # or just write it in plain text.
        self._set_default_attribs(**{'ID': 'ID_' + str(uuid4().time)[:-1]})

    def __str__(self):
        return self.gettag() + ': ' + str(self.gettext())

    def getRecognizableNodeTags(self):
        return self._recognizableNodeTags

    def nodes(self):  # returns an iterator for going through nodes
        for child in self:
            if child.gettag() in self.getRecognizableNodeTags():
                yield child

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

    def __init__(self, **kwargs):
        super(Map, self).__init__(**kwargs)
        self.tag = 'map'
        self._set_default_attribs(**{"version":'freeplane 1.3.0'})

    def setroot(self, root):
        pass

    def getroot(self):
        pass


class Cloud(BaseElement):
    
    def __init__(self, **kwargs):
        super(Cloud, self).__init__(**kwargs)
        self.tag = 'cloud'
        self._set_default_attribs(**{'COLOR': '#333ff', 'SHAPE': 'ARC'})
        self._strConstructors.extend(['COLOR', 'SHAPE'])

    #def __str__(self):
    #    s = ''
    #    desired = ['COLOR', 'SHAPE']
    #    ss = [' ' + prop + ':' + value for prop, value in self.items() if prop in desired]
    #    for p in ss:
    #        s+= p
    #    return self.gettag() + ':' + s# + str(self['COLOR']) + ' shape:' + str(self['SHAPE'])


class Hook(BaseElement):

    def __init__(self, **kwargs):
        super(Hook, self).__init__(**kwargs)
        self.tag = 'hook'

class MapStyles(BaseElement):

    def __init__(self, **kwargs):
        super(MapStyles, self).__init__(**kwargs)
        self.tag = 'map_styles'


class StyleNode(BaseElement):

    def __init__(self, **kwargs):
        super(StyleNode, self).__init__(**kwargs)
        self.tag = 'stylenode'


class Font(BaseElement):

    def __init__(self, **kwargs):
        super(Font, self).__init__(**kwargs)
        self.tag = 'font'
        self._set_default_attribs(**{'BOLD': 'false', 'ITALIC': 'false', 'NAME': 'SansSerif', 'SIZE': '10'})


class Icon(BaseElement):

    def __init__(self, **kwargs):
        super(Icon, self).__init__(**kwargs)
        self.tag = 'icon'


class Edge(BaseElement): 

    def __init__(self, **kwargs):
        super(Edge, self).__init__(**kwargs)
        self.tag = 'edge'

    
class Attribute(BaseElement):

    def __init__(self, **kwargs):
        super(Attribute, self).__init__(**kwargs)
        self.tag = 'attribute'


class Properties(BaseElement):

    def __init__(self, **kwargs):
        super(Properties, self).__init__(**kwargs)
        self.tag = 'properties'
