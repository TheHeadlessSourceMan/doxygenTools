r"""
Tools for handling doxygen documentation

EXAMPLE:
    dox=DoxygenInfo(r'c:\code\myproject')
    print(dox.url)
    fn=dox.functions['some_random_function']
    print(fn)
    print(fn.callGraph)
"""
from .doxyFile import *
from .doxygenInfo import *
from .fdox import *
