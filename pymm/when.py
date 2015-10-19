""" define hooks that are triggered through various actions, including adding_children,
converting, and reverting
ANY function decorated by these when-decorators will BE REMOVED from their respective class.
The when-decorated function will be stored in this module and accessed by class.
"""
from collections import OrderedDict


class Hooks:
    """ hold all hooked classes here and allow quick access to the hook dictionaries
    """
    add_child_hook = {}
    has_added_child = OrderedDict()
    unclaimed = []  # can't use set because it requires ALL objects to be hashable when
                          # searching to see if an object is inside unclaimed
    @classmethod
    def trigger_child_add(cls, obj, *args):
        """ obj is the object whose class we must find """
        reversed_keys = lambda keys: reversed([k for k in keys])
        for elementClass in reversed_keys(cls.has_added_child.keys()):  # start with newest classes. First match
            if isinstance(obj, elementClass):  # is the newest hook to call
                hook_fxn = cls.has_added_child[elementClass]
                hook_fxn(obj, *args)
                break

# currently works ONLY when adding an element directly to BaseElement.
# I think the isinstance searching has failed here. It looks like it correctly holds onto the
# instance in _Hook_Key but it cannot find the class fxn hook to call
class ChildrenMonitor(list):
    """ mimicks a list, but listens to any calls that might change the list. If any part is
    changed in any way, it calls the appropriate hook.
    Currently only support an has_added_child hook
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self._Hook_Key = kwargs['Hook_Key']

    def __setitem__(self, index, item):
    # call hook after adding item (so that errors are thrown first, if any)
        super().__setitem__(index, item)
        Hooks.trigger_child_add(self._Hook_Key, item)

    def append(self, item):
        super().append(item)
        Hooks.trigger_child_add(self._Hook_Key, item)


class PreventOverwritingChildren:
    """ BaseElement should inherit from this. It will help prevent user from setting child to a
    simple list, since that would ruin the hooked list part
    """
    def __setattr__(self, attr_name, attr):
        if attr_name == 'children':
            if not isinstance(attr, ChildrenMonitor):
                Hook_Key = self.children._Hook_Key  # get other child's Hook Key
                attr = ChildrenMonitor(attr, Hook_Key=Hook_Key)
        super().__setattr__(attr_name, attr)


class Remove_WhenDecorated_Functions(type):
    """ this is a Metaclass. BaseElement will use this to identify and remove REST-ful style
    decorated functions
    """

    def __new__(cls, clsname, bases, attr_dict):
        # identify functions decorated here
        decorated_fxns = [v for k, v in attr_dict.items() if v in Hooks.unclaimed]
        filtered_attr = {k: v for k, v in attr_dict.items() if v not in decorated_fxns}
        cls = super().__new__(cls, clsname, bases, filtered_attr)
        if len(decorated_fxns) > 1:
            raise ValueError("got more than 1 decorated fxn. ... that's ok but you need work here")
        for func in decorated_fxns:
            Hooks.unclaimed.remove(func)
            Hooks.has_added_child[cls] = func  # associate class with function
        return cls


def has_added_child(*args, **kwargs):
    """ Decorator that matches function to class, either implicitly (if function is inside class)
    or explicitly (if Class=... argument supplied) that hooks the function into the class's
    add_child hook. The end result is that any function decorated by add_child will be called by
    the object that just added a child. The arguments supplied to any add_child decorated function
    will be as follows: self, child  (where self = the element who has just added a child)
    If you define the function inside it's class definition, the function should look like:
    
    @pymm.when.has_added_child
    def this_function_gets_called_when_adding_child(self, child):

    However, if you define that function outside of the class definition, you need to supply the
    Class=... argument like so:

    @pymm.when.has_added_child(Class=pymm.Node)
    def this_function_gets_called_when_adding_child_to_a_node(node, child):
    """

    if not kwargs and len(args) == 1:  # then we presume it's a non-argumented decorator
        func = args[0]
        Hooks.unclaimed.append(func)  # this will later be claimed by class
        return func  # return function unchanged
    def child_hook_decorator(func):
        cls = kwargs.get('Class')  # get Class=argument supplied
        if cls is not None:
            Hooks.has_added_child[cls] = func
        else:  #cls is None
            Hooks.unclaimed.append(func)
        return func
    return child_hook_decorator
           
if __name__ == '__main__':
    class test:

        @has_added_child
        def no_arguments(self):
            pass

    @has_added_child(Class=test)
    def with_arguments(self):
        pass

    f = Hooks.unclaimed.pop()
