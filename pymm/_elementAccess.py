import warnings
import copy
import re

class ChildSubsetSimplified:
    ''' Provide simplified access to specific child elements through regex 
    matching of descriptors such as tag, attributes, or a combination thereof.
    For example, if you want to simply match a tag (or tags), pass in a regular
    expression string that will fully match the desired tag(s).
    e.g. 'node|cloud'  # matches any 
    If you want to match a set of attributes, pass in a dictionary containing 
    regexes to fully match the key(s) and value(s) of the element's attributes
    e.g. {'TEXT':'.*'}  # matches any element with a 'TEXT' attribute
    e.g. {'.*': '.*flag.*'}  # matches any element with a 'flag' in its value
    e.g. {'COLOR': '.*'}  # matches anything with a 'COLOR' attribute
    You can include any number of tag and attribute regexes, each separated by
    a comma. All descriptors will have to fully match in order for an element
    to qualify as part of this subset.
    Most useful for allowing access
    to child nodes. Provide access to slicing, removal, appending

    :param element: the linked element whose children will be available through ElementAccessor
    :param descriptor: the list of specific descriptor of elements to group and provide access to.
    '''
    def __init__(self, elementInstance, **kwargs):
        self._verify_arguments(kwargs)
        self._TAG_REGEX = kwargs.get('tag_regex', None)
        self._ATTRIB_REGEX = kwargs.get('attrib_regex', {})
        self._parent = elementInstance

    @classmethod
    def _verify_arguments(cls, kwargs):
        keysExpected = set(('tag_regex', 'attrib_regex'))
        keysGot = set(kwargs.keys())
        unexpectedKeys = keysGot.difference(keysExpected)
        if not keysGot:
            raise ValueError('Must pass in either/both tag_regex and ' + 
                            'attrib_regex')
        if unexpectedKeys:
            raise KeyError('Unexpected keys found in subset init: ' +
                            str(unexpectedKeys))
        tag = kwargs.get('tag_regex', None)
        attrib = kwargs.get('attrib_regex', {})
        if tag and not isinstance(tag, str):
            raise ValueError('tag_regex should be string. Got ' + str(tag))
        if attrib and not isinstance(attrib, dict):
            raise ValueError('attrib_regex should be dict. Got ' + str(attrib))
        if not tag and not attrib:
            raise ValueError('Must define either tag or attrior regex. Got ' +
                    str(tag) + str(attrib))

    @classmethod
    def class_preconstructor(cls, **kwargs):
        cls._verify_arguments(kwargs)
        kwargs = copy.deepcopy(kwargs)
        def this_function_gets_automatically_run_inside_elements__new__(elementInstance):
            return cls(elementInstance, **kwargs) 
        return this_function_gets_automatically_run_inside_elements__new__ #  long
        # name because this function name NEEDS to be unique. It is automatically
        # instantiated in the __new__ method of base element

    def append(self, element):
        self._parent.children.append(element)
        #what about setting child's 'parent' property?

    def remove(self, element):
        self._parent.chilren.remove(element)

    def __len__(self):
        return len(self[:])

    def __getitem__(self, index):
        if index == 0:  # speed shortcut
            for e in self:
                return e
            raise IndexError('Index out of bounds')
        elements = [e for e in self]
        return elements[index]

    def __iter__(self):
        for elem in self._parent.children:
            if self._TAG_REGEX:
                if not re.fullmatch(self._TAG_REGEX, elem.tag):
                    continue  # skip this element, it doesn't match tag_regex
            matches = lambda x, y, rx, ry: re.fullmatch(rx, x) and re.fullmatch(ry, y)
            for regK, regV in self._ATTRIB_REGEX.items():
                match = [k for k, v in elem.attrib.items() if matches(k, v, regK, regV)]
                if not match:
                    break  # skip element that can't match one of our attribs
            else:  # only get here if we didn't break attrib matching (always works if no attrib_regex)
                yield elem  # yield element only if it matches tag and attrib regex


    def __setitem__(self, index, elem):   # removes elements, then re-appends them after modification.
        """ remove element(s), then re-appends after modification. Sloppy, but
        it works, and elements are reordered later anyways.
        what really matters is that the order of elements of the same tag are
        not altered
        """
        # check for index == 0, can use shortcut in that case
        if index == 0:
            e = self[index]
            i = self._parent.children.index(e)
            self._parent.children[i] = elem
            return
        subchildren = self[:]             # sloppy, but it works. And elements are reordered later anyways.
        for element in subchildren:       # what really matters is that the order of elements of the same tag are not
            self._parent.children.remove(element)  # altered.
        subchildren[index] = elem
        for element in subchildren:
            self._parent.children.append(element)

    def __delitem__(self, index):
        element = self[index]
        i = self._parent.children.index(element)
        del self._parent[i]


class ChildSubset(ChildSubsetSimplified):
    ''' Provide access to specific elements within an element through matching of descriptor. Most useful for allowing access
    to child nodes. Provide access with indexing, slicing, removal, appending, etc.

    :param element: the linked element whose children will be available through ElementAccessor
    :param descriptor: the list of specific descriptor of elements to group and provide access to.
    '''
    
    def pop(self, index=-1):
        """ Remove and return element in children list """
        elem = self[index]
        self._parent.children.remove(elem)
        return elem

    def extend(self, elements):
        self._parent.children.extend(elements)

    def __contains__(self, element):
        return element in self[:]

    def __str__(self):
        s = 'subset: '
        if self._TAG_REGEX:
            s += str(self._TAG_REGEX)  # looks aweful because string
            # representation of compiled regex is.... re.compiled('asdf')
        if self._ATTRIB_REGEX:
            s += str(self._ATTRIB_REGEX)
        return s

    def __repr__(self):
        return '<' + str(self)[:15] + '...'*(len(str(self)) > 15) + ' @' + hex(id(self)) + '>'


class SingleChild:
    """Provide access to a single child within an element's children. It does
    not directly store the child, but rather provides functions for getting,
    setting, and deleting the specified child from a parent element's children
    attribute. This is meant to be instantiated as a class property. Pass the
    setup fxn a tag_regex or attrib_regex in the same fashion as specifying a
    ChildSubset, and pass the returned values to property(). You can look at an
    example in Node.cloud.
    """

    @classmethod
    def setup(cls, **regexes):
        if not regexes:
            raise ValueError('expected either tag_regex or attrib_regex')

        def getter(parent):
            return parent.find(**regexes)
        
        def setter(parent, child):
            replaceable = parent.find(**regexes)
            i = parent.children.index(replaceable)
            parent.children[i] = child

        def deleter(parent):
            deleteable = parent.find(**regexes)
            parent.children.remove(deleteable)

        return getter, setter, deleter


class Attrib:
    attrib = {}  # pre-define these (outside of init like this) in other classes to define default element attribs
    _descriptors = []  # list of attribs that can be used to better describe instance. Used in str(self) construction
    specs = {}  # list all possible attributes of an element and valid entries / types in a list or standalone:
                    # [str, int, 'thin', etc.], str, int, 'thin', etc.

    def __getitem__(self, key):
        """ Return attrib value given key.

        :param key:
        :return attribute value
        """
        return self.attrib[key]

    def __delitem__(self, key):
        """ Delete attrib key: value pair given a key

        :param key: attrib key (string)
        """
        del self.attrib[key]

    def items(self):
        return self.attrib.items()  # both update() and items() are functions that I'd like to remove if possible.

    def keys(self):
        return self.attrib.keys()

    def __str__(self):
        """ Construct string representation of self. Configured to display more info: self._descriptors.append() """
        extraDescriptors  = [' ' + prop + '=' + value for prop, value in self.attrib.items() if prop in self._descriptors]
        return self.tag + ':' + ''.join(extraDescriptors)

    def __repr__(self):
        """ Return shortened description of self """
        return '<' + str(self)[:13] + '...'*(len(str(self)) > 13) + ' @' + hex(id(self)) + '>'

    def __setitem__(self, key, value):
        """ Set Element's attribute

        :param key: dictionary key
        :param value: dictionary value.
        """
        self._setdictitem(key, value)  # error-check self.attrib[key] = value

    def _setdictitem(self, key, value):
        """  Error check (key: value) pair against Element.specs, warn user if mismatch found but still allow operation.

        :param key: dictionary key (string expected)
        :param value: dictionary value
        """
        self.attrib[key] = value  # regardless of whether we warn developer, add attribute.
        if key not in self.specs:   # add keywords and arguments to element.specs to address unnecessary warnings
            warnings.warn('<' + self.tag + '> does not have "' + key + '" spec', UserWarning, stacklevel=2)
        else:  # then key IS in attribSpecs
            entries = self.specs[key]
            if not isinstance(entries, list):
                entries = [entries]
            entry = None # default value
            for entry in entries:
                if type(entry) == type:
                    if type(value) == entry:
                        break
                elif type(entry) == type(lambda x: x):
                    break  # assume that a function means any attribute is valid
                else:
                    if entry == value:
                        break
            else:
                raise ValueError('attribute value not correct type:' + str(entry) + ' vs ' + str(type(value)))


class AttribEnhanced(Attrib):
    
    def __contains__(self, key):
        """ Returns if key is part of this Elements dictionary
        :param key: dictionary key
        :return: Boolean
        """
        return key in self.attrib

    def __iter__(self):
        ''' raise error. We do not want user iterating over attribs (because implicit iteration here can lead to confusing code) '''
        raise NotImplementedError('DO NOT use implicit iteration of attributes. Can confuse between iteration of children' \
                                         ' and attributes. Instead, use .items() for attribute iteration or access .children if iterating children')

    def update(self, attribs):
        """ Update Element's attributes """
        for k, v in attribs.items():  # add attributes one at a time, which allows element to warn if passed key is
            self[k] = v               # not part of its specs.
