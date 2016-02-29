"""
    registry holds the two registry metaclasses for element.py and
    factory.py. These metaclasses are responsible for keeping track
    of each element or factory class created, including any new
    elements created by you. This is done so that newly created
    elements are automaticallly used when reading from a mindmap
"""
import collections
from uuid import uuid4
from . import decode
from . import encode


class ElementRegistry(type):
    """Metaclass to hold all elements created. As each element class is
    created, Registry adds it (The new element class) to its internal
    registry, so long as an element inherits from BaseElement.
    Factories will search through all registered elements and use the
    newest matching element.
    """
    _elements = []
    _decorated_fxns = collections.defaultdict(dict)

    @classmethod
    def get_elements(cls):
        """Return list of all registered elements"""
        return list(cls._elements)

    @classmethod
    def get_decorated_fxns(cls):
        """Return dict of encode/decode-decorated fxns"""
        return dict(cls._decorated_fxns)

    class attribute_searched:
        """class to use in keeping track of which attribute is being
        looked up currently. Used to prevent recursive __getattr__
        calls
        """
        _searched = collections.defaultdict(bool)
        _name = None

        def __init__(self, name):
            self._name = name

        def __bool__(self):
            return self._searched[self._name]

        def __enter__(self):
            self._searched[self._name] = True
            return self

        def __exit__(self, *errors):
            self._searched[self._name] = False

    def __new__(cls, clsname, bases, attr_dict):
        """Record unaltered class. In addition, identify encode/decode
        decorated functions within the element and organize as
        class: {fxn: 'event_name'}. The decorated function is kept here
        and added to the Element's factory during creation. It is then
        called with the proper arguments during encode/decode.
        """
        ElementClass = super().__new__(cls, clsname, bases, attr_dict)
        decorated = dict(decode.unclaimed)
        decorated.update(encode.unclaimed)
        for fxn_name, fxn in attr_dict.items():
            try:
                hash(fxn)
            except TypeError:
                continue
            if fxn in decorated:
                event_name = decorated.pop(fxn)
                class_decorated = cls._decorated_fxns[ElementClass]
                class_decorated[event_name] = fxn
        cls._elements.append(ElementClass)
        #erase unclaimed @decode or @encode, but give error if some fxns
        #went unclaimed
        decode.unclaimed.clear()
        encode.unclaimed.clear()
        if decorated:
            raise RuntimeError(
                '@decode or @encode must be used to decorate a function ' +
                'inside a new element class declaration. ' +
                'The following were unclaimed by the last-created element: ' +
                str(ElementClass) + '\n and functions: ' + str(decorated)
            )
        return ElementClass

    @classmethod
    def identify_attribute_error(mcs, element, name):
        """this is called ONLY if an attribute is missing from an
        element. Re-raise AttributeError so that user is informed of
        her error. However, due to how element inheritance dictates
        which Element class is used when creating the hierarchy, it
        may be difficult to realize that a recently-created class has
        become the new default for a specific element type. This can
        become apparent when an attribute access fails on an element!
        Therefore this __getattr__ attempts to figure out which element
        the user MEANT to access, and includes that info in the
        AttributeError
        """
        if mcs.attribute_searched(name) or hasattr(type(element), name):
            raise AttributeError(name)
        with mcs.attribute_searched(name):
            elements = mcs.get_elements()
            has_attr = [elem for elem in elements if hasattr(elem, name)]
            most_likely = [
                elem for elem in reversed(has_attr) if elem.tag == element.tag
            ]
            least_likely = [
                elem for elem in reversed(has_attr) if elem not in most_likely
            ]
        err_msg = name
        if most_likely + least_likely:
            relevant_elements = ''
            if most_likely:
                relevant_elements += ' '.join((
                    '\nThese elements have the attribute you seek and are',
                    'related to the current element:\n',
                ))
            relevant_elements += '\n'.join(str(elem) for elem in most_likely)
            if least_likely:
                relevant_elements += ' '.join((
                    '\nThese elements have the attribute you seek but',
                    'ARE NOT RELATED to this current element:\n',
                ))
            relevant_elements += '\n'.join(str(elem) for elem in least_likely)
            err_msg += ' '.join((
                '\n\nHello! This is a friendly reminder from pymm. It appears',
                'that you are trying to access "' + name + '"',
                'within this element:\n' + str(type(element)) + '\nHowever, ',
                'no such attribute exists on this element. Due to how pymm',
                'prefers to use newer elements over older elements (by order',
                'in which they were defined), a recently-defined Element',
                'Class (this one) MAY have taken preference over the element',
                'you wanted at this moment.', relevant_elements,
                '\nSome examples of what you may do to rememdy this problem',
                'are\n1) double-check your code for mistakes\n2) change the',
                'order in which you define new element classes\n3) define a',
                'newer class that inherits from the element you wanted here.',
                'For example:\nclass Preferred(element.you.wanted):\n\tpass',
                "\n3) modify this element's .identifier proptery such",
                'that this element is not used in this situation\n',
            ))
        raise AttributeError(err_msg)





class FactoryRegistry(type):
    """Metaclass to register all Factories created, and assist in
    creating new factories for unclaimed elements (elements without a
    corresponding factory). In addition, collect encode/decode
    decorated functions and apply them to the correct factory.
    """
    _factories = []
    verbose = False
    _skip_registration = ''
    default = None

    @classmethod
    def get_factories(cls):
        factories = list(tuple(cls._factories))
        generated = cls.create_unclaimed_element_factories(factories)
        return factories + generated

    def __new__(mcs, clsname, bases, attr_dict):
        """create Factory-class, and register it in list of factories
        """
        FactoryClass = super().__new__(mcs, clsname, bases, attr_dict)
        # do not register factory if it was generated by this metaclass
        if clsname != mcs._skip_registration:
            if mcs.default is None:
                mcs.default = FactoryClass  # keep default factory reference
            mcs._factories.append(FactoryClass)
        return FactoryClass

    @classmethod
    def create_unclaimed_element_factories(cls, factories):
        """iterate all elements inheriting from Elements.BaseElement.
        For each element with no corresponding factory, create a factory
        to handle it, inheriting from closest-matching factory.
        Closest-matching factory is determined as the newest factory to
        use a decoding-element of which the unclaimed element is a
        subclass AND which inherits from the previous closest-matching
        factory. (this second part ensures that a DefaultFactory-clone
        will not become the closest-match

        Return list of all factories created in this way
        """
        generated = []
        factories = list(factories)
        convert_fxns = ElementRegistry.get_decorated_fxns()
        for elem in ElementRegistry.get_elements():
            closest_match = cls.default
            for factory in factories:
                if issubclass(elem, factory.decoding_element) and \
                        issubclass(factory, closest_match):
                    closest_match = factory
                if factory.decoding_element == elem:
                    break
            else:
                factory = cls.create_factory(elem, closest_match, convert_fxns)
                generated.append(factory)
                # allow generated factories to inherit from prior generated
                factories.append(factory)
        cls.verbose = False
        return generated

    @classmethod
    def create_factory(cls, elem, closest_matching_factory, convert_fxns):
        """creat factory for given element, inheriting from closest
        matching factory, and include any functions decorated by
        encode.* or decode.*
        """
        if cls.verbose:
            print(
                'unclaimed element:', elem,
                '\n\t tag:', elem.tag,
                '\n\t identifier:', elem.identifier,
                '\n\t closest matching factory:', closest_matching_factory,
            )
        element_name = getattr(elem, '__name__', elem.tag)
        name = element_name + '-Factory@' + uuid4().hex
        cls._skip_registration = name
        inherit_from = (closest_matching_factory,)
        variables = {'decoding_element': elem}
        def simulate_bound_method(event_fxn):
            """wrap function to discard the first argument, thereby
            simulating a method call for the 2nd argument, the element.
            Wrapping a fxn through this helps create a permanent scope
            for wrapping a function as well.
            """
            return lambda factory, *args: event_fxn(*args)
        convert_events = convert_fxns.get(elem, {})
        for event_name, event_fxn in convert_events.items():
            wrapped_event = simulate_bound_method(event_fxn)
            variables[event_name] = wrapped_event
        new_factory = type(name, inherit_from, variables)
        return new_factory
