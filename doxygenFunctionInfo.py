"""
Information provided by doxygen about a function
and its call tree

TODO: can add parameters and docstrings
"""
import typing
import re
from pathlib import Path
import xml.etree.ElementTree as ET
from .callLocation import CallLocation
from .doxygenFileInfo import DoxygenFileInfo
if typing.TYPE_CHECKING:
    from .doxygenInfo import DoxygenInfo
    from .callGraph import CallGraph


class DoxygenFunctionInfo:
    """
    Information provided by doxygen about a function
    and its call tree

    TODO: can add parameters and docstrings
    """
    def __init__(self,
        root:"DoxygenInfo",
        name:str,
        refid:str):
        """ """
        self.root=root
        self.parent=root
        self.name=name
        self.refid=refid
        self.files:typing.Dict[str,"DoxygenFileInfo"]={}
        self._parentReferences:typing.List[CallLocation]=[]

    def __hash__(self):
        return hash(self.refid)

    def __eq__(self,other):
        if isinstance(other,DoxygenFunctionInfo):
            return other.refid==self.refid
        if isinstance(other,str):
            if self.refid==other or self.name==other:
                return True
        return False

    @property
    def xmlFilename(self)->Path:
        """
        file that contains info about this function
        """
        return self.bestFile.name

    @property
    def bestFile(self)->"DoxygenFileInfo":
        """
        Get the file that best represents the function
        (eg, the .c file over the .h file)
        """
        if not self.files:
            f=self.refid.rsplit('_',1)[0]+'.xml'
            filename=self.root.doxygenOutputDirectory/'xml'/f
            fileInfo=DoxygenFileInfo(self.root,'',filename)
            fileInfo.functions[self.name]=self
            self.files[filename]=fileInfo
            return fileInfo
        bestFile=None
        for f in self.files.values():
            if bestFile is None or bestFile.extension=='.h':
                bestFile=f
        return bestFile
    @property
    def file(self)->"DoxygenFileInfo":
        """
        Get the file that best represents the function
        (eg, the .c file over the .h file)
        """
        return self.bestFile

    @property
    def xml(self)->typing.List[ET.Element]:
        """
        Get a list of xml elements from all files
        that define this function
        """
        xml=[]
        for xmlFile in self.files.values():
            tags=xmlFile.xml.findall(f".//*[@id='{self.refid}']")
            if tags:
                xml.extend(tags)
            else:
                print(
                    f'refid {self.refid} not found in "{self.bestFile.name}"')
        return xml

    def thisCallsFunctions(self,
        ignore:typing.Optional[typing.Set["DoxygenFunctionInfo"]]=None
        )->typing.Iterable["CallLocation"]:
        """
        Functions that this function calls

        returns [(function, callLocation)]
        """
        if ignore is None:
            ignore=set((self,))
        for element in self.xml:
            for ref in element.findall('references'):
                fn=self.root.references.get(ref.attrib['refid'])
                if fn is not None \
                    and isinstance(fn,DoxygenFunctionInfo) \
                    and fn not in ignore:
                    #
                    ignore.add(fn)
                    row=ref.attrib.get('startline')
                    if not row:
                        yield CallLocation(fn,self.filename)
                    else:
                        yield CallLocation(fn,f'{self.filename}:{row}')

    def functionsCallThis(self,
        ignore:typing.Optional[typing.Set["DoxygenFunctionInfo"]]=None
        )->typing.Iterable["CallLocation"]:
        """
        Functions that call this function

        returns [(function, callLocation)]
        """
        _=ignore
        self.root.calculateFunctionBackreferences()
        return self._parentReferences

    @property
    def callGraph(self)->"CallGraph":
        """
        Get the full call graph for this function
        including what calls it, and what it calls.
        """
        from .callGraph import CallGraph
        return CallGraph(self)

    @property
    def filename(self)->Path:
        """
        The source file where this function is implemented
        (full path)
        """
        return Path(self.getDefinitionLocation(False,False,False))
    @property
    def relativeFilename(self)->Path:
        """
        The source file where this function is implemented
        (path relative to the source code base)
        """
        return self.filename.relative_to(self.root.codeDirectory)

    def getDeclarationLocation(self,
        includeRow=True,
        includeColumn=True,
        includeSpan=False
        )->str:
        """
        Get source location where this function is declared

        :includeRow: if possible, include the row in the filename
            eg foo.c:10
        :includeColumn: if possible, include the column in the filename
            eg foo.c:10:1
        :includeSpan: if possible, include the row span in the filename
            eg foo.c:10-14
        """
        _=includeSpan
        for element in self.xml:
            loc=element.find('location')
            filename=loc.attrib.get('declfile',loc.attrib['file'])
            if includeRow:
                row=loc.attrib.get('declline',loc.attrib['line'])
                if includeColumn:
                    col=loc.attrib.get('declcolumn',loc.attrib['column'])
                    filename=f'{filename}:{row}:{col}'
                else:
                    filename=f'{filename}:{row}'
        return filename

    def getDefinitionLocation(self,
        includeRow=True,
        includeColumn=True,
        includeSpan=False
        )->str:
        """
        Get source location where this function is defined

        :includeRow: if possible, include the row in the filename
            eg foo.c:10
        :includeColumn: if possible, include the column in the filename
            eg foo.c:10:1
        :includeSpan: if possible, include the row span in the filename
            eg foo.c:10-14
        """
        _=includeColumn
        for element in self.xml:
            loc=element.find('location')
            filename=loc.attrib.get('bodyfile',loc.attrib['file'])
            if includeRow:
                row=loc.attrib.get('bodystart',loc.attrib['line'])
                if includeSpan:
                    endRow=loc.attrib.get('bodyend',row)
                    if row!=endRow:
                        filename=f'{filename}:{row}-{endRow}'
                    else:
                        filename=f'{filename}:{row}'
                else:
                    filename=f'{filename}:{row}'
        return filename

    @property
    def localUrls(self)->typing.Iterable[typing.Tuple[str,str]]:
        """
        There can be multiple urls, for instance
        if it is c++ there is a .h and a .c file

        returns [sourceFilename,htmlUrl]
        """
        doxygenOutput=doxygenOutput=self.root.doxygenOutputDirectory/'html'
        doxygenOutputFunctions=doxygenOutput/'globals_func.html'
        data=doxygenOutputFunctions.read_text('utf-8',errors='ignore')
        reg=re.compile(
            r'<li>\s*'+self.name+r'\(\)(?P<references>.*?)</li>',
            re.DOTALL)
        linkReg=re.compile(
            r'<a .*?href="(?P<url>[^"]*)".*?>\s*(?P<filename>[^<]*)<',
            re.DOTALL)
        for m in reg.finditer(data):
            references=m.group('references')
            for reference in linkReg.finditer(references):
                yield (reference.group('filename'),
                    doxygenOutput/reference.group('url'))
    @property
    def urls(self)->typing.Iterable[typing.Tuple[str,str]]:
        """
        Local urls to the documentation for this function
        """
        return self.localUrls

    @property
    def localUrl(self)->str:
        """
        This will return the most representative url

        There can be multiple urls, for instance
        if it is c++ there is a .h and a .c file
        You can use self.urls to get all of them.

        returns [sourceFilename,htmlUrl]
        """
        best=''
        bestExt=''
        for codeFilename,url in self.urls:
            ext=codeFilename.rsplit('.',1)[-1]
            if bestExt.startswith('h') or not best:
                best=url
                bestExt=ext
        return best
    @property
    def url(self)->str:
        """
        Local url to the documentation for this function
        """
        return self.localUrl

    def __repr__(self):
        location=self.getDeclarationLocation(True,True,True)
        return f'{self.name} at "{location}" url {self.url}'
