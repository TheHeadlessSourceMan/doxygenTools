"""
Where a function is called from
"""
import typing
from paths import UrlLocation,UrlLocationCompatible
if typing.TYPE_CHECKING:
    from .doxygenFunctionInfo import DoxygenFunctionInfo


class CallLocation:
    """
    Where a function is called from
    """
    def __init__(self,
        fn:"DoxygenFunctionInfo",
        location:UrlLocationCompatible):
        """ """
        self.fn:"DoxygenFunctionInfo"=fn
        self.location:UrlLocation=UrlLocation(location)

    def __repr__(self):
        return f'{self.fn.name} called from {self.location}'
