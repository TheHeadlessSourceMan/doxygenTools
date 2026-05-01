"""
Information provided by doxygen about a function
and its call tree

TODO: can add parameters and docstrings
"""
import typing
import re
import xml.etree.ElementTree as ET
from backup_plan import asFilePath
from paths import (
    UrlMatchable,urlMatches,Url)
from codeTools import FunctionDeclaration,FunctionDefinition
from .callLocation import DoxygenCallLocation
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
        self.root:"DoxygenInfo"=root
        self.parent:typing.Union["DoxygenInfo",DoxygenFunctionInfo]=root
        self.name:str=name
        self.refid:str=refid
        self.files:typing.Dict[Url,"DoxygenFileInfo"]={}
        self._parentReferences:typing.List[DoxygenCallLocation]=[]
        self._declaration:typing.Optional[FunctionDeclaration]=None
        self._definition:typing.Optional[FunctionDefinition]=None

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
    def xmlFilename(self)->Url:
        """
        file that contains info about this function
        """
        return self.bestFile.xmlFilename

    @property
    def bestFile(self)->"DoxygenFileInfo":
        """
        Get the file that best represents the function
        (eg, the .c file over the .h file)
        """
        if not self.files:
            f=self.refid.rsplit('_',1)[0]+'.xml'
            filename=Url(self.root.doxygenOutputDirectory/'xml'/f)
            fileInfo=DoxygenFileInfo(self.root,'',filename)
            fileInfo.functions[self.name]=self
            self.files[filename]=fileInfo
            return fileInfo
        bestFile=None
        for f in self.files.values():
            if bestFile is None or bestFile.xmlFilename.ext in ('.h','.hpp','.hh','.hxx'):
                bestFile=f
        if bestFile is None:
            raise Exception(f'No file found for function {self.name}')
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
        )->typing.Iterable["DoxygenCallLocation"]:
        """
        Functions that this function calls

        returns [(function, DoxygenCallLocation)]
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
                        yield DoxygenCallLocation(fn,self.filename)
                    else:
                        yield DoxygenCallLocation(fn,f'{self.filename}:{row}')

    @property
    def parentReferences(self)->typing.Iterable[DoxygenCallLocation]:
        """
        references to all direct parents off this function call
        """
        self.root.calculateFunctionBackreferences()
        return self._parentReferences

    def functionsCallThis(self,
        ignoreFunctions:typing.Optional[
            typing.Iterable[typing.Union["DoxygenFunctionInfo",str,typing.Pattern]]]=None,
        ignoreFiles:UrlMatchable=None,
        recursive:bool=False
        )->typing.Iterable["DoxygenCallLocation"]:
        """
        Functions that call this function

        returns [(function, DoxygenCallLocation)]
        """
        if ignoreFunctions:
            return self.parentReferences
        tape=list(self.parentReferences)
        for callLocation in tape:
            # first, exclude whatever needs excluding
            if ignoreFunctions is not None:
                found=False
                for ignore in ignoreFunctions:
                    if isinstance(ignore,str):
                        if ignore==callLocation.fn.name:
                            found=True
                            break
                    elif isinstance(ignore,DoxygenFunctionInfo):
                        if ignore.name==callLocation.fn:
                            found=True
                            break
                    else:
                        if ignore.match(callLocation.fn.name) is not None:
                            found=True
                            break
                if found:
                    continue
            # accept that value
            if ignoreFiles is None or urlMatches(callLocation.url,ignoreFiles):
                yield callLocation
            # recurse if necessary
            if recursive:
                tape.extend(callLocation.fn.parentReferences)

    @property
    def callGraph(self)->"CallGraph":
        """
        Get the full call graph for this function
        including what calls it, and what it calls.
        """
        from .callGraph import CallGraph
        return CallGraph(self)

    @property
    def filename(self)->Url:
        """
        The source file where this function is implemented
        (full path)
        """
        return self.getDefinitionLocation(False,False,False).url
    @property
    def relativeFilename(self)->Url:
        """
        The source file where this function is implemented
        (path relative to the source code base)
        """
        return asFilePath(self.filename).getRelativeFrom(self.root.codeDirectory)

    def getDeclarationLocation(self,
        includeRow=True,
        includeColumn=True,
        includeSpan=False
        )->FunctionDeclaration:
        """
        Get source location where this function is declared

        :includeRow: if possible, include the row in the filename
            eg foo.c:10
        :includeColumn: if possible, include the column in the filename
            eg foo.c:10:1
        :includeSpan: if possible, include the row span in the filename
            eg foo.c:10-14
        """
        if self._declaration is None:
            filename=None
            _=includeSpan
            for element in self.xml:
                loc=element.find('location')
                if loc is None:
                    continue
                filename=loc.attrib.get('declfile',loc.attrib['file'])
                if includeRow:
                    row=loc.attrib.get('declline',loc.attrib['line'])
                    if includeColumn:
                        col=loc.attrib.get('declcolumn',loc.attrib['column'])
                        filename=f'{filename}:{row}:{col}'
                    else:
                        filename=f'{filename}:{row}'
            if filename is None:
                raise Exception(f'No location found for function {self.name}')
            self._declaration=FunctionDeclaration(filename)
            self._declaration.definition=self.definition
        return self._declaration
    @property
    def declaration(self)->FunctionDeclaration:
        """
        Get source location where this function is declared
        """
        return self.getDeclarationLocation()

    def getDefinitionLocation(self,
        includeRow=True,
        includeColumn=True,
        includeSpan=False
        )->FunctionDefinition:
        """
        Get source location where this function is defined

        :includeRow: if possible, include the row in the filename
            eg foo.c:10
        :includeColumn: if possible, include the column in the filename
            eg foo.c:10:1
        :includeSpan: if possible, include the row span in the filename
            eg foo.c:10-14
        """
        if self._definition is None:
            filename=None
            _=includeColumn
            for element in self.xml:
                loc=element.find('location')
                if loc is None:
                    continue
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
            if filename is None:
                raise Exception(f'No location found for function {self.name}')
            self._definition=FunctionDefinition(filename)
            self._definition.declaration=self.definition
        return self._definition
    @property
    def definition(self)->FunctionDefinition:
        """
        Get source location where this function is defined
        """
        return self.getDefinitionLocation()

    @property
    def localUrls(self)->typing.Iterable[typing.Tuple[Url,Url]]:
        """
        There can be multiple urls, for instance
        if it is c++ there is a .h and a .c file

        returns [sourceFilename,htmlUrl]
        """
        doxygenOutput=self.root.doxygenOutputDirectory/'html'
        doxygenOutputFunctions=doxygenOutput/'globals_func.html'
        data=doxygenOutputFunctions.readString()
        reg=re.compile(
            r'<li>\s*'+self.name+r'\(\)(?P<references>.*?)</li>',
            re.DOTALL)
        linkReg=re.compile(
            r'<a .*?href="(?P<url>[^"]*)".*?>\s*(?P<filename>[^<]*)<',
            re.DOTALL)
        for m in reg.finditer(data):
            references=m.group('references')
            for reference in linkReg.finditer(references):
                url:Url=doxygenOutput/str(reference.group('url'))
                yield (Url(reference.group('filename')),url)
    @property
    def urls(self)->typing.Iterable[typing.Tuple[Url,Url]]:
        """
        Local urls to the documentation for this function
        """
        return self.localUrls

    @property
    def localUrl(self)->Url:
        """
        This will return the most representative url

        There can be multiple urls, for instance
        if it is c++ there is a .h and a .c file
        You can use self.urls to get all of them.

        returns [sourceFilename,htmlUrl]
        """
        best=None
        bestExt=''
        for codeFilename,url in self.urls:
            if bestExt.startswith('h') or not best:
                best=url
                bestExt=codeFilename.ext
        if best is None:
            raise Exception(f'No local url found for function {self.name}')
        return best
    @property
    def url(self)->Url:
        """
        Local url to the documentation for this function
        """
        return self.localUrl

    def __repr__(self):
        location=self.getDeclarationLocation(True,True,True)
        return f'{self.name} at "{location}" url {self.url}'
