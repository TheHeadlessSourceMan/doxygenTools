"""
This is an interface to the Doxygen source documentor tool.
"""
import typing
from subprocess import Popen,PIPE
from paths import UrlCompatible, asUrl
from stringTools import Version
from codeTools import SourceDocumentor


class Doxygen(SourceDocumentor):
    """
    This is an interface to the Doxygen source documentor tool.
    """
    # TOOL: doxygen=Doxygen()
    # FN: doxygen.view(docFile)

    def __init__(self):
        """
        Construct a new Doxygen object
        """

    def document(self,
        fileOrDir:UrlCompatible,
        docFormat='HTML',
        exclude:typing.Optional[typing.Iterable[str]]=None
        )->str:
        """
        Document a file or files.

        Doxygen settings can be found at:
            http://www.stack.nl/~dimitri/doxygen/config.html#cfg_chm_file
        """
        # FN: doxygen.document(fileOrDir,format)
        formats:typing.Dict[
            str,typing.List[typing.Union[str,None]]
            ]={ # {type:[config_option,post_tool]}
            'xhtml':['GENERATE_HTML',None],
            'html':['GENERATE_HTML',None],
            'htm':['GENERATE_HTML',None],
            'latex':['GENERATE_LATEX',None],
            'tex':['GENERATE_TEX',None],
            'man':['GENERATE_MAN',None],
            'rtf':['GENERATE_RTF',None],
            'xml':['GENERATE_XML',None],
            'qhp':['GENERATE_QHP',None],
            'chm':['GENERATE_HTMLHELP',None],
            'qch':['GENERATE_QHP','qhelpgenerator'],
            'ps':['GENERATE_LATEX','make ps'],
            'pdf':['GENERATE_LATEX','make pdf'],
        }
        docFormat=formats[docFormat.lower()]
        config=''
        config=config+'PROJECT_NAME='+'TODO: Get project name from projecto\n'
        config=config+'PROJECT_NUMBER='+'TODO: Get version from projecto\n'
        config=config+'OUTPUT_DIRECTORY=doc\n'
        config=config+'INPUT='+str(fileOrDir)+'\n'
        firstValue=['']
        for firstValue in formats.values():
            break
        config=config+str(firstValue[0])+'=YES\n'
        config=config+'RECURSIVE=YES\n'
        config=config+'SEARCHENGINE=YES\n'
        config=config+'TREEVIEW=YES\n'
        config=config+'GENERATE_TAGFILE=YES\n'
        config=config+'CLASS_DIAGRAMS=YES\n'
        config=config+'SOURCE_BROWSER=YES\n'
        config=config+'ALPHABETICAL_INDEX=YES\n'
        if exclude is not None:
            config=config+'EXCLUDE_PATTERNS='+(' '.join(exclude))+'\n'
        cmd=('echo',
            config.replace('\\','\\\\').replace('"','\\"'),
            '|',
            'doxygen','-')
        return str(Popen(cmd,stderr=PIPE).communicate()[1])

    def getVersion(self)->Version:
        """
        Returns a version string for this tool or None if not installed.
        """
        # FN: getVersion()
        cmd='doxygen --version'
        out,err=Popen(cmd,stderr=PIPE,stdout=PIPE).communicate()
        if len(err)>0:
            return Version(str(err))
        return Version(str(out))

    def canLoadFile(self,fileName:UrlCompatible)->bool:
        """
        Returns whether or not this tool can open the given file.
        """
        # FN: canLoadFile(fileName)
        sourceExt=[
            'c','cc','cp','cpp','cxx','c++',
            'h','hh','hp','hpp','h++','hxx',
            'java','py','python','idl','cs','vhdl',
            'f','for','ftn','f77','f90','f95',
            'vhdl','php','phtml','php3','cs']
        ext=asUrl(fileName).ext.rsplit('.',1)
        if len(ext)>1 and ext[1] in sourceExt:
            return True
        return False
