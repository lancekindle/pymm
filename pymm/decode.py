""" A module designed to hold onto decode.* decorated functions. Each
    function decorated by decode is returned untouched. However, they
    are registered within this module for retrieval by factories when
    decoding and encoding to and from (respectively) a pymm element.
    This module (and it's decorations) should be used in-place of
    writing a specific factory, since the type of decorations
    allowed is limited but powerful enough to allow custom exporting
    and importing of mindmaps
"""

# decorated is the dictionary of functions decorated, and their
# keyword-used in decorating them. For example, 'post_decode': fxn
unclaimed = {}


def post_decode(fxn):
    """any function decorated by post_decode will be called after the
    element hierarchy has been created and before any scripting can be
    done on the hierarchy. Typically, one should post_decode decorate a
    function that corrects or standardizes certain aspects of the
    element itself before the user's code has a chance to mess with it.
    For example, Node uses a post_decode-decorated function to replace
    its attrib key "LOCALIZED_TEXT" with "TEXT", due to an expected
    "TEXT" key. post_decode is called on each element (where defined)
    starting at the root node, and calling each children's post_decode
    in breadth-first order (all children of root are triggered. Then all
    children of root's first child is triggered, then all children of
    root's second child is triggered, etc.)
    """
    unclaimed[fxn] = 'post_decode'
    return fxn
