"""
Main entrypoint for dealing with doxygen data

Will auto-scan doxygen tree as necessary

TODO: attach to doxygenFile
"""
import typing
import subprocess
import xml.etree.ElementTree as ET
from paths import UrlCompatible,Url
from .doxygenFunctionInfo import DoxygenFunctionInfo
from .doxygenFileInfo import DoxygenFileInfo
from .callLocation import CallLocation


class DoxygenInfo:
    """
    Main entrypoint for dealing with doxygen data

    Will auto-scan doxygen tree as necessary

    TODO: attach to doxygenFile
    """
    def __init__(self,
        codeDirectory:UrlCompatible='.',
        outputDir:typing.Optional[UrlCompatible]=None,
        forceRescan=False):
        """ """
        self.codeDirectory=Url(codeDirectory).absolute()
        if outputDir is None:
            outputDir=self.codeDirectory/"doxygen"
        else:
            outputDir=Url(outputDir).absolute()
        self.doxygenOutputDirectory=outputDir
        self._functions:typing.Dict[str,DoxygenFunctionInfo]={}
        self._references:typing.Dict[str,DoxygenFunctionInfo]={}
        self._files:typing.Dict[str,DoxygenFileInfo]={}
        self._functionBackreferencesCalculated=False
        self.rescan(forceRescan)

    def calculateFunctionBackreferences(self,force:bool=False):
        """
        Doxygen only tracks what function a function calls.
        Therefore, to determine what calls a function,
        we need to go through all functions and link
        children back to parents.
        """
        if force or not self._functionBackreferencesCalculated:
            # find all references
            for fn in self.functions.values():
                for fnCall in fn.thisCallsFunctions():
                    fnCall.fn._parentReferences.append( # noqa: E501; pylint: disable=protected-access
                        CallLocation(fn,fnCall.location))
            self._functionBackreferencesCalculated=True

    @property
    def files(self)->typing.Dict[str,DoxygenFileInfo]:
        """
        Get all source files
        """
        if not self._files:
            self._reparseXmlIndex()
        return self._files
    @property
    def functions(self)->typing.Dict[str,DoxygenFunctionInfo]:
        """
        Get all function info
        """
        if not self._functions:
            self._reparseXmlIndex()
        return self._functions
    @property
    def references(self)->typing.Dict[str,DoxygenFunctionInfo]:
        """
        Get all reference id to object mappings
        """
        if not self._references:
            self._reparseXmlIndex()
        return self._references

    @property
    def xmlFilename(self)->Url:
        """
        file that contains info about this function
        """
        return self.doxygenOutputDirectory/'xml'/'index.xml'

    @property
    def xml(self)->ET.ElementTree[ET.Element[str]]: # pylint: disable=unsubscriptable-object
        """
        XML of the doxygen index
        """
        xml=ET.parse(self.xmlFilename)
        return xml

    def _reparseXmlIndex(self):
        """
        re-parse the doxygen index
        """
        self._files={}
        self._functions={}
        self._references={}
        xmlIndex=self.xml
        for file in xmlIndex.findall('.//compound'):
            if file.attrib.get("kind","")!="file":
                continue
            shortFilename=file.attrib['refid']+'.xml'
            xmlFilename=self.doxygenOutputDirectory/'xml'/shortFilename
            name=''
            elements=file.findall('name')
            if elements and elements[0].text is not None:
                name=elements[0].text
            fileInfo=DoxygenFileInfo(self,name,xmlFilename)
            for member in file.findall('member'):
                refid=member.attrib['refid']
                kind=member.attrib['kind']
                if kind=='function':
                    if refid in self._references:
                        fn=self._references[refid]
                    else:
                        name=''
                        elements=member.findall('name')
                        if elements and elements[0].text is not None:
                            name=elements[0].text
                        fn=DoxygenFunctionInfo(self,name,refid)
                        self._functions[fn.name]=fn
                        self._references[refid]=fn
                    fileInfo.functions[fn.name]=fn
                    fn.files[Url(fileInfo.name)]=fileInfo

    @property
    def localUrl(self)->str:
        """
        Get the local url of the main doxygen entrypoint
        """
        doxygenOutput=self.doxygenOutputDirectory/'html'/'index.html'
        return 'file://'+str(doxygenOutput).replace('\\','//')
    @property
    def url(self)->str:
        """
        Get the local url of the main doxygen entrypoint
        """
        return self.localUrl

    def rescan(self,forceRescan:bool=True)->Url:
        """
        Generate doxygen documentation.

        returns the path to the generated documentation
        """
        if self.doxygenOutputDirectory.isDir and not forceRescan:
            print(f'Doxygen results: "{self.doxygenOutputDirectory}"')
            return self.doxygenOutputDirectory
        self._functions={}
        # Create Doxygen configuration
        self.doxygenOutputDirectory.mkdir(parents=True,exist_ok=True)
        doxyfile=self.doxygenOutputDirectory/'Doxyfile'
        doxyfile.writeString(f"""
            OUTPUT_DIRECTORY       = {self.doxygenOutputDirectory}
            GENERATE_XML           = YES
            RECURSIVE              = YES
            EXTRACT_ALL            = YES
            CALL_GRAPH             = YES
            HAVE_DOT               = YES
            INPUT                  = {self.codeDirectory}
            QUIET                  = YES
        """)
        # Run Doxygen
        print("Running doxygen (could take awhile - like 10min)")
        po=subprocess.Popen(["doxygen",str(doxyfile)],
            stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        out,_=po.communicate()
        out=out.strip()
        if out:
            print(out.decode('utf-8',errors='ignore'))
        print(f'Doxygen results: "{self.doxygenOutputDirectory}"')
        return self.doxygenOutputDirectory
Doxygen=DoxygenInfo
