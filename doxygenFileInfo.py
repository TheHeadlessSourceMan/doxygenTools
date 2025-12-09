"""
Doxygen information about a source file
"""
import typing
from pathlib import Path
import xml.etree.ElementTree as ET
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
        xmlFilename:Path):
        """ """
        self.root=root
        self.name=name
        self.functions:typing.Dict[str,DoxygenFunctionInfo]={}
        self._xml:typing.Optional[ET.Element]=None
        self.xmlFilename=xmlFilename

    @property
    def xml(self)->ET.Element:
        """
        XML tag pertaining to this source file
        """
        if self._xml is None:
            try:
                s=self.xmlFilename.read_text('utf-8',errors='ignore')
                self._xml=ET.fromstring(s)
            except FileNotFoundError:
                print(f'ERR: "{self.xmlFilename}" not found')
                self._xml=ET.Element('file_not_found')
        return self._xml
