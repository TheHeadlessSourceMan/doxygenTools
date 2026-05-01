"""
Where a function is called from
"""
import typing
from paths import UrlLocation,UrlLocationCompatible
from codeTools import FunctionCallLocation
if typing.TYPE_CHECKING:
    from .doxygenFunctionInfo import DoxygenFunctionInfo


class DoxygenCallLocation(FunctionCallLocation):
    """
    Where a function is called from according to doxygen
    """
    def __init__(self,
        fn:"DoxygenFunctionInfo",
        location:UrlLocationCompatible):
        """ """
        self.fn:"DoxygenFunctionInfo"=fn
        self.location:UrlLocation=UrlLocation(self.fn.name,location)
