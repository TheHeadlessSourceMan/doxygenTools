"""
Doxygen information about a source file
"""
import typing
import xml.etree.ElementTree as ET
from paths import Url,UrlCompatible
if typing.TYPE_CHECKING:
    from .doxygenInfo import DoxygenInfo
    from .doxygenFunctionInfo import DoxygenFunctionInfo


class DoxygenFileInfo:
    """
    Doxygen information about a source file
    """
    def __init__(self,
        root:"DoxygenInfo",
        name:str,
        xmlFilename:UrlCompatible):
        """ """
        self.root=root
        self.name=name
        self.functions:typing.Dict[str,DoxygenFunctionInfo]={}
        self._xml:typing.Optional[ET.Element]=None
        self.xmlFilename:Url=Url(xmlFilename)

    @property
    def xml(self)->ET.Element:
        """
        XML tag pertaining to this source file
        """
        if self._xml is None:
            try:
                s=self.xmlFilename.readString()
                self._xml=ET.fromstring(s)
            except FileNotFoundError:
                print(f'ERR: "{self.xmlFilename}" not found')
                self._xml=ET.Element('file_not_found')
        return self._xml
