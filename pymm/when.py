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
