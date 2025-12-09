"""
doxyfile files contain settings for doxygen

this allows you to easily read/change them in a pythonic way

Example:
    d=Doxyfile(f'codeLocation/doxyfile')
    d['HAVE_DOT']=True

It is usually a better idea to set many at once
(especially if autosave is enabled)
    d.update({
        'HAVE_DOT':True,
        'EXTRACT_ALL':True,
        'EXTRACT_PRIVATE':True,
        'EXTRACT_STATIC':True,
        'CALL_GRAPH':True,
        'CALLER_GRAPH':True,
        'DISABLE_INDEX':True,
        'GENERATE_TREEVIEW':True,
        'RECURSIVE':True})

Note that help() also works on settings!
    help(d['HAVE_DOT'])

See also:
    https://www.doxygen.nl/manual/diagrams.html
"""
import typing
import os
import re
from pathlib import Path
import k_runner.osrun as osrun
from k_runner import ApplicationCallbacks
from paths import URL,Url,UrlCompatible,asUrl
from util import findDoxygenInputDirs


class DoxyfileSetting:
    """
    A single setting within a doxyfile
    """

    def __init__(self,
        doxyfile:"DoxyFile",
        lineNo:int,
        name:str,
        value:str,
        docs:str):
        """ """
        self.doxyfile=doxyfile
        self.name=name
        self.docs=docs
        self._value=value
        self._lineNo=lineNo # zero-based

    @property
    def value(self)->str:
        """
        The value of this setting
        """
        return self._value
    @value.setter
    def value(self,value:typing.Any):
        if isinstance(value,bool):
            if value:
                value='YES'
            else:
                value='NO'
        elif not isinstance(value,str):
            value=str(value)
        self._value=value
        prev=self.doxyfile._lines[self._lineNo].split('=',1) # noqa: E501 # pylint: disable=protected-access
        if prev[1].lstrip()!=value:
            self.doxyfile._lines[self._lineNo]=f'{prev[0]}= {value}' # noqa: E501 # pylint: disable=line-too-long,protected-access
            self.doxyfile.markDirty()

    @property
    def parent(self)->"DoxyFile":
        """
        Reteurn the tree parent
        (which is the doxygen file)
        """
        return self.doxyfile

    @property
    def __doc__(self)->str: # type: ignore
        return self.docs

    def __repr__(self)->str:
        return f'{self.name} = {self.value}'


class DoxyFile:
    """
    doxyfile files contain settings for doxygen

    this allows you to easily read/change them in a pythonic way

    Example:
        d=Doxyfile(f'codeLocation/doxyfile')
        d['HAVE_DOT']=True

    It is usually a better idea to set many at once
    (especially if autosave is enabled)
        d.update({
            'HAVE_DOT':True,
            'EXTRACT_ALL':True,
            'EXTRACT_PRIVATE':True,
            'EXTRACT_STATIC':True,
            'CALL_GRAPH':True,
            'CALLER_GRAPH':True,
            'DISABLE_INDEX':True,
            'GENERATE_TREEVIEW':True,
            'RECURSIVE':True})

    Note that help() also works on settings!
        help(d['HAVE_DOT'])

    See also:
        https://www.doxygen.nl/manual/diagrams.html
    """

    def __init__(self,
        filename:typing.Union[str,Path]='Doxyfile',
        autoCreate:bool=True,
        autosave:bool=True,
        makeCommand:typing.Union[None,str,typing.List[str]]=None,
        makeDirectory:typing.Union[None,str,typing.List[str]]=None):
        """
        :makeCommand: how to generate the documentation
            (if absent, will take a reasonable guess)
        :makeDirectory: directory to run the make in
            (if absent, will take the location of the doxyfile)
        """
        self.autosave=autosave
        self.autoCreate=autoCreate
        self.filename=Path(filename)
        self._dirty=False
        self._lines:typing.List[str]=[]
        self._settings:typing.Optional[typing.Dict[str,DoxyfileSetting]]=None
        self._makeCommand:typing.Union[
            None,str,typing.List[str]]=makeCommand
        self._makeDirectory:typing.Union[
            None,str,typing.List[str]]=makeDirectory

    @property
    def url(self)->URL:
        """
        Url of the index.html of the documentation
        """
        return URL(self.doxygenBaseDir/'index.html')
    URL=url

    @property
    def doxygenBaseDir(self)->Path:
        """
        The base directory of the doxygen output directory
        """
        d=self.settings['OUTPUT_DIRECTORY'].value
        d=Path(os.path.expandvars(d))
        d=d/'html'
        return d.absolute()

    _DOXY_TARGET_RE=re.compile(
        r"""<a\s+(class\s*=\s*"[^"]*"\s+)?href="(?P<target>[^"]+)"\s*>(?P<label>.*?)</a>""", # noqa: E501 # pylint: disable=line-too-long
        re.DOTALL)

    def _doxygenTargets(self,
        htmlFilename:UrlCompatible
        )->typing.Generator[typing.Tuple[str,str],None,None]:
        """
        open the htmlFilename and find the href target
        to jump to for each label

        yields [(label,target)]
        """
        htmlFilename=asUrl(htmlFilename)
        data=''
        found=set()
        found.add('Functions')
        data=htmlFilename.readString()
        for m in self._DOXY_TARGET_RE.finditer(data):
            label=m.group('label')
            label=label.replace('&nbsp;',' ').replace('(','').replace(')','').strip() # noqa: E501 # pylint: disable=line-too-long
            target=m.group('target').replace('(','').replace(')','').strip()
            if label \
                and target \
                and label[0] not in ('&','<') \
                and label not in found:
                #
                yield (label,target)
                found.add(label)

    def doxygenTargets(self,
        codeFilename:typing.Union[str,Path,None]=None
        )->typing.Generator[typing.Tuple[str,str],None,None]:
        """
        open the appropriate html for the codeFilename and find
        the href target to jump to for each label

        yields [(label,target)]
        """
        htmlFilename=self.doxygenHtmlFilename(codeFilename)
        #print(f'{codeFilename} => {htmlFilename}')
        if htmlFilename is not None:
            yield from self._doxygenTargets(htmlFilename)

    def doxygenHtmlFilename(self,
        codeFilename:typing.Union[None,str,Path]=None
        )->typing.Optional[Path]:
        """
        Make an educated guess at the .html file that refers
        to the given code filename.

        If that file doesn't exist, returns None.
        """
        if codeFilename is None:
            htmlFilename='index.html'
        else:
            if not isinstance(codeFilename,Path):
                codeFilename=Path(codeFilename)
            codeFilename=codeFilename.name
            htmlFilename=codeFilename\
                .replace('_','__')\
                .replace('/','_2')\
                .replace('\\','_2')\
                .replace('.','_8')+'.html'
        ret=self.doxygenBaseDir/htmlFilename
        if ret.is_file():
            return ret
        # not found exact match, so search in source sub-directories
        rr=ret.rsplit(os.sep,1)
        rr[1]=f'_2{rr[1]}' # where _2 is the subdirectory separator
        for filename in os.listdir(rr[0]):
            if filename.endswith(rr[1]):
                return os.sep.join((rr[0],filename))
        raise FileNotFoundError(f'File not found:\n\t{ret}')

    def doxygenUrl(self,
        codeFilename:typing.Union[None,str,Path]=None,
        label:typing.Optional[str]=None
        )->typing.Optional[Url]:
        """
        get the doxygen url that refers to a code file

        :codeFilename: can be of the form "myfile.cpp->myfunc()"

        If a doxygen output file doesn't exist for that file, returns None.
        """
        codeFilename=str(asUrl(codeFilename))
        if label is None:
            cf=codeFilename.split('->',1)
            if len(cf)>1:
                label=cf[1]
            elif codeFilename[-1]=='-':
                msg=f"""ERR: malformed filename "{codeFilename}"
                (probably because you used a reserved ">" symbol from the
                command line please consider putting your query string
                in quotes!)"""
                raise Exception(msg)
            codeFilename=cf[0]
        htmlFilename=self.doxygenHtmlFilename(codeFilename)
        if htmlFilename is None:
            return None
        if label is not None and label:
            label=label.split('(',1)[0].strip()
            t=''
            for name,target in self._doxygenTargets(htmlFilename):
                if name==label:
                    t=target
                    break
            if t:
                if t[0]=='#':
                    htmlFilename=htmlFilename+t
                else:
                    htmlFilename=os.sep.join((
                        htmlFilename.rsplit(os.sep,1)[0],
                        t))
        if os.sep!='/':
            htmlFilename=htmlFilename.replace(os.sep,'/')
        return Url(f'file:///{htmlFilename}')

    @property
    def settings(self)->typing.Dict[str,DoxyfileSetting]:
        """
        Get the settings from the doxyfile
        """
        if self._settings is None:
            self.load(self.filename)
        return self._settings # type: ignore

    @property
    def makeDirectoryStr(self)->str:
        """
        self.makeDirectory always as a str
        """
        if isinstance(self.makeDirectory,str):
            return self.makeDirectory
        return os.sep.join(self.makeDirectory)
    @makeDirectoryStr.setter
    def makeDirectoryStr(self,makeDirectory:str):
        self.makeDirectory=makeDirectory

    def run(self,
        outputLineCb:typing.Optional[typing.Callable[[str],None]]=None
        )->None:
        """
        Run doxygen with this configuration file
        (be sure to save first if you don't have autosave on)
        """
        cmd=self.makeCommand
        if not isinstance(cmd,str):
            cmd[0]=os.path.abspath(os.path.expandvars(cmd[0]))
        else:
            cmd=os.path.expandvars(cmd)
        directory=os.path.abspath(os.path.expandvars(self.makeDirectoryStr))
        results=osrun.run(cmd,shell=True,
            workingDirectory=directory,
            runCallbacks=ApplicationCallbacks(outputLineCb))
        if results!=0:
            raise Exception(results.stdouterr)
    __call__=run
    doxygen=run
    make=run

    @property
    def makeCommand(self)->typing.Union[str,typing.List[str]]:
        """
        The associated make command
        """
        if self._makeCommand is None:
            filename=os.path.abspath(os.path.expandvars(self.filename))
            ff=filename.rsplit(os.sep,1)
            self._makeCommand=['doxygen',ff[1]]
        return self._makeCommand
    @makeCommand.setter
    def makeCommand(self,makeCommand:typing.Union[str,typing.List[str]])->None:
        self._makeCommand=makeCommand

    @property
    def makeDirectory(self)->typing.Union[str,typing.List[str]]:
        """
        Make a directory exist
        """
        if self._makeDirectory is None:
            filename=os.path.abspath(os.path.expandvars(self.filename))
            ff=filename.rsplit(os.sep,1)
            self._makeDirectory=ff[0]
        return self._makeDirectory
    @makeDirectory.setter
    def makeDirectory(self,
        makeDirectory:typing.Union[str,typing.List[str]]
        )->None:
        """ """
        self._makeDirectory=makeDirectory

    def create(self)->None:
        """
        Usually don't need to call directly.
        Just specify autoCreate and it will do this when
        it tries to load.
        """
        filename=os.path.expandvars(self.filename)
        cmd=['doxygen','-g',filename]
        results=osrun.run(cmd)
        if results.stderr:
            raise Exception(results.stdouterr)

    def update(self,values:typing.Dict[str,typing.Any])->None:
        """
        The nice thing about doing this over directly setting each
        value individually is that if autosave=True will only save once when
        it's done, instead of for every single value.
        """
        originalAutosave=self.autosave
        self.autosave=False
        for k,v in values.items():
            self.settings[k].value=v
        if originalAutosave:
            if self.dirty:
                self.save()
            self.autosave=originalAutosave
    batchSet=update

    def enableCallGraph(self):
        """
        Canned shortcut to enable generating function call graphs.
        """
        self.update({
            'HAVE_DOT':True,
            'EXTRACT_ALL':True,
            'EXTRACT_PRIVATE':True,
            'EXTRACT_STATIC':True,
            'CALL_GRAPH':True,
            'CALLER_GRAPH':True,
            'DISABLE_INDEX':True,
            'GENERATE_TREEVIEW':True,
            'RECURSIVE':True})

    def __getitem__(self,k:str)->typing.Optional[DoxyfileSetting]:
        return self.settings.get(k)
    def __setitem__(self,k:str,v:typing.Any):
        self.settings[k].value=v

    def load(self,filename:UrlCompatible)->None:
        """
        load a doxyfile

        No need to call directly.  Will load on first use.
        """
        self.filename=filename
        lastsection=[]
        section:typing.List[str]=[]
        self._settings={}
        filename=os.path.expandvars(filename)
        if self.autoCreate and not os.path.exists(filename):
            self.create()
        data=filename.read_text('utf-8',errors='ignore')
        self._lines=[line.strip() for line in data.split('\n')]
        for lineNo,line in enumerate(self._lines):
            if not line:
                if section:
                    lastsection=section
                    section=[]
                continue
            if line[0]=='#':
                section.append(line[2:])
            else:
                cols=[x.strip() for x in line.split('=',1)]
                if len(cols)>1:
                    if section:
                        lastsection=section
                        section=[]
                    setting=DoxyfileSetting(self,
                        lineNo,cols[0],cols[1],'\n'.join(lastsection))
                    self._settings[setting.name]=setting

    def save(self,filename:typing.Union[None,str,Path]=None)->None:
        """
        save a doxyfile
        """
        if filename is None:
            filename=self.filename
        data='\n'.join(self._lines)
        with open(os.path.expandvars(filename),'w',encoding="utf-8") as f:
            f.write(data)
            f.flush()
        self._dirty=False

    @property
    def dirty(self)->bool:
        """
        Whether or not the file has changed
        and is in need of being saved
        """
        return self._dirty
    @dirty.setter
    def dirty(self,dirty:bool):
        if not dirty:
            self._dirty=False
        else:
            self.markDirty()

    def markDirty(self)->None:
        """
        indicate whether it needs to be saved
        """
        if self.autosave:
            self.save(self.filename)
        else:
            self._dirty=True

    def __str__(self)->str:
        return '\n'.join(self._lines)

Doxygen=DoxyFile
DoxygenFile=DoxyFile
Doxyfile=DoxyFile


def createDoxyFile(directory:Path,overwriteExisting:bool=False)->Path:
    """
    Create a doxyfile

    Returns Path object to the new file
    """
    directory=directory.absolute()
    doxyFile=directory/'Doxyfile'
    if not os.path.exists(doxyFile) or overwriteExisting:
        defaultDoxyfile=Path(__file__).parent/'data'/'Doxyfile'
        data=defaultDoxyfile.read_text()
        # may as well change the project name while we're at it
        data=data.replace('"My Project"',f'"{directory.name}"',1)
        # add source directory locations
        inputs=' '.join([
            str(x).replace('\\','/').replace(' ','\\ ') for x in findDoxygenInputDirs(directory)])
        data=re.sub(r"(INPUT\s+=[ ]*)",r"\1 "+inputs,data,count=1)
        # save over existing file
        doxyFile.write_text(data)
    return doxyFile
createDoxyfile=createDoxyFile


def cmdline(args):
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    printhelp=False
    if not args:
        printhelp=True
    else:
        doxygen=DoxyFile()
        for arg in args:
            if arg.startswith('-'):
                arg=[a.strip() for a in arg.split('=',1)]
                arg[0]=arg[0].lower()
                if arg[0] in ['-h','--help']:
                    printhelp=True
                elif arg[0] in ('--edit','--open','--view'):
                    if len(arg)>1:
                        url=doxygen.doxygenUrl(arg[1])
                    else:
                        url=doxygen.doxygenUrl()
                    print(url)
                    import subprocess
                    cmd=['start','',url]
                    subprocess.Popen(cmd,shell=True).communicate()
                elif arg[0] in ('--url','--doxygenurl'):
                    if len(arg)>1:
                        print(doxygen.doxygenUrl(arg[1]))
                    else:
                        print(doxygen.doxygenUrl())
                elif arg[0] in ('--doxygentargets','--targets'):
                    if len(arg)>1:
                        targets=doxygen.doxygenTargets(arg[1])
                    else:
                        targets=doxygen.doxygenTargets()
                    for target in targets:
                        #print(f'{target[0]} - ({target[1]})')
                        print(f'{target[0]}')
                elif arg[0] in ('--make','--run'):
                    def cb(line:str):
                        print(line)
                    doxygen.run(cb)
                else:
                    print('ERR: unknown argument "'+arg[0]+'"')
            else:
                url=doxygen.doxygenUrl(arg)
                print(url)
                import subprocess
                cmd=['start','',url]
                subprocess.Popen(cmd,shell=True).communicate()
    if printhelp:
        print('Usage:')
        print('  codeProject.py [options]')
        print('Options:')
        print('   --targets')
        print('   --make')
        print('   --url[=file.c->fn()]')
        print('   --open[=file.c->fn()]')
        return -1
    return 0


if __name__=='__main__':
    import sys
    sys.exit(cmdline(sys.argv[1:]))
