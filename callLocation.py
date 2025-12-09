"""
Where a function is called from
"""
import typing
if typing.TYPE_CHECKING:
    from .doxygenFunctionInfo import DoxygenFunctionInfo


class CallLocation:
    """
    Where a function is called from
    """
    def __init__(self,
        fn:"DoxygenFunctionInfo",
        location:str):
        """ """
        self.fn=fn
        self.location=location

    def __repr__(self):
        return f'{self.fn.name} called from {self.location}'
