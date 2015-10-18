""" define hooks that are triggered through various actions, including adding_children,
converting, and reverting
"""

class Controller:
    add_child_hook = {}
    unclaimed_child_hooks = []
    pass

def has_added_child(*args, **kwargs):
    """ Decorator that matches function to class, either implicitly (if function is inside class)
    or explicitly (if class=... argument supplied) that hooks the function into the class's
    add_child hook. The end result is that any function decorated by add_child will be called by
    the object that just added a child. The arguments supplied to any add_child decorated function
    will be as follows: self, child  (where self = the element who has just added a child)
    If you define the function inside it's class definition, the function should look like:
    
    @pymm.when.has_added_child
    def this_function_gets_called_when_adding_child(self, child):

    However, if you define that function outside of the class definition, you need to supply the
    class=... argument like so:

    @pymm.when.has_added_child(class=pymm.Node)
    def this_function_gets_called_when_adding_child_to_a_node(node, child):
    """

    if not kwargs and len(args) == 1:  # then we presume it's a non-argumented decorator
        func = args[0]
        Controller.unclaimed_child_hooks.append(func)  # this will later be claimed by class
        return func  # return function unchanged
    # we assume that some arguments are supplied below here
    def child_hook_decorator(func):
        cls = kwargs.get('class')  # get class=argument supplied
        if cls is None:
            self = getattr(func, '__self__', None)  # try to find object instance through function
            if self is not None:  # FAILS. we are getting a class-function, no object instance yet
                cls = getattr(self, '__class__', None)  # find class through object instance
        if cls is not None:
            Controller.add_child_hook[cls] = func
        return func
    return child_hook_decorator
           

class test:

    @has_added_child
    def no_arguments(self):
        pass

@has_added_child(cls=test)
def with_arguments(self):
    pass

f = Controller.unclaimed_child_hooks[0]
