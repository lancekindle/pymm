import re


class ChildSetupVerify:
    """hold onto method to verify ChildSubset or SingleChild setup
    arguments
    """

    @staticmethod
    def _verify_identifier_args(identifier):
        """verify that identifier dict keys contain valid (and only
        valid) identifiers. tag and tag_regex must contain string
        identifiers, while attrib_regex must be a dict with string
        identifiers. In the case of tag_regex and attrib_regex, the
        strings will be used for regex matching
        """
        expected = {'tag': str, 'tag_regex': str, 'attrib_regex': dict}
        keys_expected = set(expected.keys())
        keys_got = set(identifier.keys())
        unexpected_keys = keys_got.difference(keys_expected)
        if not keys_got:
            raise KeyError('Expected either tag/tag_regex and/or attrib_regex')
        if unexpected_keys:
            raise KeyError('Unexpected keys found:' + str(unexpected_keys))
        incompatible = set(('tag', 'tag_regex',))
        if incompatible.issubset(keys_got):
            raise KeyError('Cannot specify both tag and tag_regex matching')
        for key in keys_got:
            val_type = expected[key]
            value = identifier[key]
            if not value or not isinstance(value, val_type):
                raise ValueError(
                    str(key) + ' should be non-empty and have value of type ' +
                    str(val_type)
                )


class ChildSubsetSimplified(ChildSetupVerify):
    """Provide simplified access to specific child elements through
    regex matching of descriptors such as tag, attributes, or a
    combination thereof.  For example, if you want to simply match a tag
    (or tags), pass in a regular expression string that will fully match
    the desired tag(s).  e.g. 'node|cloud'
    # matches any If you want to match a set of attributes, pass in a
    dictionary containing regexes to fully match the key(s) and value(s)
    of the element's attributes. For example:
    {'TEXT':'.*'}  matches any element with a 'TEXT' attribute.
    {'.*': '.*flag.*'}  matches any element with 'flag' in its value.
    {'COLOR': '.*'}  matches anything with a 'COLOR' attribute.
    You can include any number of tag and attribute regexes, each
    separated by a comma. All descriptors will have to fully match in
    order for an element to qualify as part of this subset.  Most useful
    for allowing access to child nodes.  Provide access to slicing,
    removal, appending

    :param element: the linked element whose children will be available
        through ElementAccessor
    :param descriptor: the list of specific
        descriptor of elements to group and provide access to.
    """
    def __init__(self, elementInstance, **identifier):
        self._verify_identifier_args(identifier)
        self.TAG = identifier.get('tag', None)
        self.TAG_REGEX = identifier.get('tag_regex', None)
        self.ATTRIB_REGEX = identifier.get('attrib_regex', {})
        self.parent = elementInstance

    @classmethod
    def setup(cls, **identifier):
        """Return getter and setter methods for self, such that returned
        functions can be used in defining a property of an element
        """
        self = cls(None, **identifier)

        def getter(parent):
            self.parent = parent
            return self

        def setter(parent, iterable):
            self.parent = parent
            self[:] = iterable

        return getter, setter

    def append(self, element):
        self.parent.children.append(element)

    def remove(self, element):
        self.parent.children.remove(element)

    def __len__(self):
        return len(self[:])

    def __getitem__(self, index):
        if isinstance(index, int):  # speed shortcut
            for i, elem in enumerate(self):
                if i == index:
                    return elem
            raise IndexError('list index out of range')
        elements = [e for e in self]
        return elements[index]

    def __iter__(self):
        """Iterate through _parent's children, yielding children when
        they match tag/tag_regex and/or attrib_regex
        """
        for elem in self.parent.children:
            if self._element_matches(elem):
                yield elem

    def _element_matches(self, elem):
        """return true if element matches all identifier criteria,
        which can include tag, tag_regex, and attrib_regex
        """
        matches = lambda x, y, rx, ry: \
            re.fullmatch(rx, x) and re.fullmatch(ry, y)
        if self.TAG:
            if self.TAG != elem.tag:
                return False
        if self.TAG_REGEX:
            if not re.fullmatch(self.TAG_REGEX, elem.tag):
                return False
        for regK, regV in self.ATTRIB_REGEX.items():
            matching_attrib = [
                key for key, val in elem.attrib.items() \
                if matches(key, val, regK, regV)
            ]
            if not matching_attrib:
                return False
        return True

    def __setitem__(self, index, elem):
        """remove element(s), then re-appends after modification.
        Sloppy, but it works, and elements are reordered later anyways.
        What really matters is that the order of elements of the same
        tag are not altered. Note that this is very inefficient because
        the list is reconstructed each time a set-operation is applied
        """
        if isinstance(index, int):
            e = self[index]
            i = self.parent.children.index(e)
            self.parent.children[i] = elem
            return
        subchildren = list(self)
        for element in subchildren:
            self.parent.children.remove(element)
        subchildren[index] = elem
        for element in subchildren:
            self.parent.children.append(element)

    def __delitem__(self, index):
        if isinstance(index, int):
            element = self[index]
            i = self.parent.children.index(element)
            del self.parent.children[i]
        elif isinstance(index, slice):
            indices = []
            for element in self[index]:
                i = self.parent.children.index(element)
                indices.append(i)
            indices.sort()
            # delete indices from largest index to smallest
            for i in reversed(indices):
                del self.parent.children[i]


class ChildSubsetCompare:
    """implement methods for comparing lists"""

    def _assert_other_is_comparable(self, other):
        if isinstance(other, ChildSubsetSimplified) or isinstance(other, list):
            return
        raise TypeError(
            'cannot compare: ' + str(type(self)) + str(type(other))
        )

    def __lt__(self, other):
        self._assert_other_is_comparable(other)
        return list(self) < list(other)

    def __gt__(self, other):
        self._assert_other_is_comparable(other)
        return list(self) > list(other)

    def __le__(self, other):
        self._assert_other_is_comparable(other)
        return list(self) <= list(other)

    def __ge__(self, other):
        self._assert_other_is_comparable(other)
        return list(self) >= list(other)

    def __eq__(self, other):
        self._assert_other_is_comparable(other)
        return list(self) == list(other)

    def __ne__(self, other):
        self._assert_other_is_comparable(other)
        return list(self) != list(other)


class ChildSubset(ChildSubsetSimplified, ChildSubsetCompare):
    """Provide access to specific elements within an element through
    matching of descriptor. Most useful for allowing access to child
    nodes. Provide access with indexing, slicing, removal, appending,
    etc.

    :param element: the linked element whose children will be available
        through ElementAccessor
    :param descriptor: the list of specific descriptor of elements to
        group and provide access to.
    """

    def pop(self, index=-1):
        """Remove and return element in children list"""
        children = list(self)
        elem = children.pop(index)
        self.parent.children.remove(elem)
        return elem

    def extend(self, elements):
        self.parent.children.extend(elements)

    def __repr__(self):
        """Represent ChildSubset as list"""
        return repr(list(self))


class SingleChild(ChildSetupVerify):
    """Provide access to a single child within an element's children.
    It does not directly store the child, but rather provides functions
    for getting, setting, and deleting the specified child from a
    parent element's children attribute. This is meant to be
    instantiated as a class property. Pass the setup fxn a tag_regex or
    attrib_regex in the same fashion as specifying a ChildSubset, and
    pass the returned values to property(). You can look at an example
    in Node.cloud.
    """

    @classmethod
    def setup(cls, **identifier):
        cls._verify_identifier_args(identifier)

        def getter(parent):
            return parent.find(**identifier)

        def deleter(parent):
            deleteable = parent.find(**identifier)
            if deleteable is not None:
                parent.children.remove(deleteable)

        def setter(parent, child):
            """replace or remove child. If child passed is None, will
            delete first matching child. Otherwise will replace
            existing child with passed child or append to end of
            children
            """
            if child is None:
                deleter(parent)
                return
            replaceable = parent.find(**identifier)
            if replaceable is None:
                parent.children.append(child)
                return
            i = parent.children.index(replaceable)
            parent.children[i] = child

        return getter, setter, deleter


class SingleAttrib:
    """property-instantiated class to provide get/set/del access for a
    single attrib value within an element. For example, Node provides a
    .text property which accesses its .attrib['TEXT']. If del node.text
    were called, it would replace the attrib value an empty string: ''.
    In this example, attrib_name = 'TEXT', and default_value = ''
    Init this within a class as a property like:
    text = property(*SingleAttrib(attrib_name, default_value))
    """

    @staticmethod
    def setup(attrib_name, default_value):

        def getter(element):
            return element.attrib.get(attrib_name, default_value)

        def setter(element, value):
            element.attrib[attrib_name] = value

        def deleter(element):
            element.attrib[attrib_name] = default_value

        return getter, setter, deleter


class Link:
    """link for a node. Sets and gets attrib['LINK'] for attached node.
    If user links a node, set attrib['LINK'] = node.attrib['ID']
    """

    @staticmethod
    def setup(ElementClass):

        def getter(parent):
            return parent.attrib.get('LINK')

        def setter(parent, url):
            if isinstance(url, ElementClass):
                url = url.attrib.get('ID')
            parent.attrib['LINK'] = url

        def deleter(parent):
            parent.attrib['LINK'] = None
            del parent.attrib['LINK']

        return getter, setter, deleter
