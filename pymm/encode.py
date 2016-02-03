""" A module designed to hold onto encode.* decorated functions. Each
    function decorated by encode is returned untouched. However, they
    are registered within this module for retrieval by factories when
    encoding from a pymm element.
    This module (and it's decorations) should be used in-place of
    writing a specific factory, since the type of decorations
    allowed is limited but powerful enough to allow custom exporting
    of mindmaps
"""

# unclaimed is the dictionary of functions decorated, and their
# keyword-used in decorating them. For example, 'post_encode': fxn
unclaimed = {}


def pre_encode(fxn):
    """any function decorated by pre_encode will be called before any
    other encode functions. pre_encode functions are called top-down
    from the root to subchildren, in the order they appear in the tree
    in breadth-first search
    """
    unclaimed[fxn] = 'pre_encode'
    return fxn


def post_encode(fxn):
    """decorate a function with post_encode if you want to re-configure
    an element after encoding. Since anything done in post_encode will
    not influence the file / encoded tree, this decoration is only used
    if some custom modification of a pymm element should be undone
    afterwards
    """
    unclaimed[fxn] = 'post_encode'
    return fxn


def get_children(fxn):
    """the function decorated by get_children will be used when getting
    the children list from the element. Use this if you wish to modify
    the list of children, such as including additional children or
    removing children that you don't want to include in the exported
    file
    """
    unclaimed[fxn] = 'encode_getchildren'
    return fxn

def get_attrib(fxn):
    """the function decorated by get_Attrib will be used when getting
    the attrib dictionary from pymm element. Use this if you wish to
    modify the attrib dictionary; such as include or exclude attrib
    key,values. The attrib returned by this function will be used
    in exporting
    """
    unclaimed[fxn] = 'encode_getattrib'
    return fxn

