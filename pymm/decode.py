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
decorated = {}

def post_decode(fxn):
    decorated[fxn] = 'post_decode'
    return fxn
