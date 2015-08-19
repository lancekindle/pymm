import warnings

class Children:
    ''' Provide access to specific elements within an element through matching of tags. Most useful for allowing access
    to child nodes. Provide access with indexing, slicing, removal, appending, etc.

    :param element: the linked element whose children will be available through ElementAccessor
    :param tags: the list of specific tags of elements to group and provide access to.
    '''

    def __init__(self, element, tags):
        # would be awesome to allow tags to be a regex instead of a normal string
        if isinstance(tags, str):  # allow user to pass in single string for searchable element tag
            if not tags:
                raise ValueError('element accessor requires non-empty string for tag')
            tags = [tags]
        if not len(tags):
            raise ValueError('element accessor requires non-empty tags')
        self._tags = (t for t in tags)  # use tuple for list of tags to imply that this "list" should not be altered
        self._container = element

    @classmethod
    def preconstructor(cls, tags):
        def element_access_construction(element):  # just call self.nodes() or self.clouds(), self.etc... to initialize
            return cls(element, tags)
        return element_access_construction

    def append(self, element):
        self._container.children.append(element)

    def extend(self, elements):
        self._container.children.extend(elements)

    def remove(self, element):
        self._container.chilren.remove(element)

    def pop(self, index=-1):
        """ Remove and return element in children list """
        elem = self[index]
        self._container.children.remove(elem)
        return elem

    def __iter__(self):
        for elem in self._container.children:
            if elem.tag in self._tags:
                yield elem

    def __getitem__(self, index):
        elements = iter(self)
        if index >= 0:
            i = 0
            for elem in elements:
                if i == index:
                    return elem
                i += 1
        allElements = [e for e in elements]
        return allElements[index]

    def __setitem__(self, index, elem):   # removes elements, then re-appends them after modification.
        subchildren = self[:]             # sloppy, but it works. And elements are reordered later anyways.
        for element in subchildren:       # what really matters is that the order of elements of the same tag are not
            self._container.remove(element)  # altered.
        subchildren[index] = elem
        for element in subchildren:
            self._container.append(element)

    def __delitem__(self, key):
        element = self[key]
        index = self._container.index(element)
        del self._container[index]

    def __contains__(self, element):
        return element in self[:]

    def __len__(self):
        return len(self[:])

    def __str__(self):
        return 'Accessor for: ' + str(self._tags)

    def __repr__(self):
        return '<' + str(self)[:15] + '...'*(len(str(self)) > 15) + ' @' + hex(id(self)) + '>'


class Attrib:
    attrib = {}  # pre-define these (outside of init like this) in other classes to define default element attribs
    _descriptors = []  # list of attribs that can be used to better describe instance. Used in str(self) construction
    specs = {}  # list all possible attributes of an element and valid entries / types in a list or standalone:
                    # [str, int, 'thin', etc.], str, int, 'thin', etc.

    def __contains__(self, key):
        """ Returns if key is part of this Elements dictionary
        :param key: dictionary key
        :return: Boolean
        """
        return key in self.attrib

    def __getitem__(self, key):
        """ Return attrib value given key.

        :param key:
        :return attribute value
        """
        return self.attrib[key]

    def __setitem__(self, key, value):
        """ Set Element's attribute

        :param key: dictionary key
        :param value: dictionary value.
        """
        self._setdictitem(key, elements_or_value)  # error-check self.attrib[key] = value

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
                raise ValueError('attribute value not correct type:' + str(vtype) + ' vs ' + str(type(value)))

    def update(self, attribs):
        """ Update Element's attributes """
        for k, v in attribs.items():  # add attributes one at a time, which allows element to warn if passed key is
            self[k] = v               # not part of its specs.

    def __delitem__(self, key):
        """ Delete attrib key: value pair given a key

        :param key: attrib key (string)
        """
        del self.attrib[key]

    def __str__(self):
        """ Construct string representation of self. Configured to display more info: self._descriptors.append() """
        extraDescriptors  = [' ' + prop + '=' + value for prop, value in self.items() if prop in self._descriptors]
        return self.tag + ':' + ''.join(extraDescriptors)

    def __repr__(self):
        """ Return shortened description of self """
        return '<' + str(self)[:13] + '...'*(len(str(self)) > 13) + ' @' + hex(id(self)) + '>'
