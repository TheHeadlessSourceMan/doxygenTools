"""
Full call graph for a function, including
parent function that call it, and child functions
that it calls.
"""
import typing
from .doxygenFunctionInfo import DoxygenFunctionInfo
from .callLocation import CallLocation


class CallGraphNode:
    """
    A single node in the call graph tree
    """
    def __init__(self,
        fn:DoxygenFunctionInfo,
        callLocation:typing.Optional[CallLocation]=None):
        """ """
        self.fn=fn
        self.callLocation=callLocation

    @property
    def parents(self)->typing.Iterable["CallGraphNode"]:
        """
        Parents that call this function
        """
        for call in self.fn.functionsCallThis():
            yield CallGraphNode(call.fn,call)

    @property
    def children(self)->typing.Iterable["CallGraphNode"]:
        """
        Children that this function calls
        """
        for call in self.fn.thisCallsFunctions():
            yield CallGraphNode(call.fn,call)

    @property
    def roots(self)->typing.Iterable["CallGraphNode"]:
        """
        Top-level entrypoints that call this function
        """
        if self.isRoot():
            yield self
            return
        for parent in self.parents:
            yield from parent.roots
    @property
    def root(self)->"CallGraphNode":
        """
        Main top-level entrypoint that call this function

        (Usually there is only one, but not necessarily always...
        eg, if it is called from an interrupt, or exported as a library)
        """
        ret=self
        for parent in ret.parents:
            ret=parent
            break
        return ret

    def isRoot(self)->bool:
        """
        Is this the ultimate parent of the call tree?
        """
        for _ in self.parents:
            return False
        return True

    def __childTreeString__(self,indent:str=''):
        """
        Private function used to help in printing out the call tree
        """
        if self.callLocation is not None:
            selfInfo=repr(self.callLocation)
        else:
            selfInfo=self.fn.name
        ret=[f'{indent}{selfInfo}']
        nextIndent=f'{indent}    '
        for child in self.children:
            ret.append(child.__childTreeString__(nextIndent))
        return '\n'.join(ret)


class CallGraph(CallGraphNode):
    """
    Full call graph for a function, including
    parent function that call it, and child functions
    that it calls.
    """
    def __init__(self,fn:DoxygenFunctionInfo):
        CallGraphNode.__init__(self,fn)

    def __repr__(self):
        ret=[]
        for root in self.roots:
            ret.append(root.__childTreeString__())
        return '\n'.join(ret)
