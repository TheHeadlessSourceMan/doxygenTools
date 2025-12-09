"""
Manage a gitignore file
"""
import typing
from pathlib import Path
import re
from paths import globToRegex


GitignoreRule=re.Pattern


class Gitignore:
    """
    Manage a gitignore file
    """
    def __init__(self,
        fileOrDir:typing.Union[None,str,Path]=None,
        errorOnFileNotFound:bool=True):
        """ """
        self.currentFile:typing.Optional[Path]=None
        self._rules:typing.List[GitignoreRule]=[]
        self._dataLines:typing.List[str]=[]
        self.hasChanged:bool=False
        if fileOrDir is not None:
            self.load(fileOrDir,errorOnFileNotFound=errorOnFileNotFound)

    def load(self,
        fileOrDir:typing.Union[None,str,Path]=None,
        addToExisting:bool=False,
        errorOnFileNotFound:bool=True):
        """
        Load gitignore rules
        if fileOrDir is a directory, gets directory/.gitignore

        NOTE: this does not yet have any kind of recursive logic.
        It just checks the one file and that's it.
        """
        if fileOrDir is None:
            fileOrDir=self.currentFile
            if fileOrDir is None:
                fileOrDir=Path('.gitignore')
        if not addToExisting:
            self._rules=[]
            self._dataLines=[]
        startedEmpty=not self._rules
        if not isinstance(fileOrDir,Path):
            fileOrDir=Path(fileOrDir)
        if fileOrDir.is_dir():
            fileOrDir=fileOrDir/'.gitignore'
        self.currentFile=fileOrDir
        if not fileOrDir.exists():
            if errorOnFileNotFound:
                raise FileNotFoundError(str(fileOrDir))
            else:
                return
        data=fileOrDir.read_text(encoding='utf-8',errors='ignore').split('\n')
        for line in data:
            line=line.lstrip()
            if line and line[0]!='#':
                self.addRule(line)
        self.hasChanged=not startedEmpty
    reload=load

    def addRule(self,rule:str)->None:
        """
        Add a new rule to the set of rules

        Will not add duplicates
        """
        for line in self._dataLines:
            if line==rule:
                return
        r=globToRegex(rule,caseSensitive=True)
        self._rules.append(r)
        self._dataLines.append(rule)
        self.hasChanged=True
    add=addRule
    append=addRule

    def removeRule(self,rule:str)->None:
        """
        Remove a rule from the rules
        """
        for n,line in enumerate(self._dataLines):
            if line==rule:
                del self._rules[n]
                del self._dataLines[n]
                self.hasChanged=True
                return
    remove=removeRule

    def save(self,
        fileOrDir:typing.Union[None,str,Path]=None):
        """
        Save gitignore rules
        """
        if fileOrDir is None:
            fileOrDir=self.currentFile
            if fileOrDir is None:
                fileOrDir=Path('.gitignore')
        elif isinstance(fileOrDir,str):
            fileOrDir=Path(fileOrDir)
        if fileOrDir.is_dir():
            fileOrDir=fileOrDir/'.gitignore'
        if self.hasChanged or self.currentFile!=fileOrDir:
            self.currentFile=fileOrDir
            fileOrDir.write_text('\n'.join(self._dataLines),encoding='utf-8',errors='ignore')
            self.hasChanged=False
    saveAs=save

    def firstRuleMatch(self,
        file:typing.Union[str,Path]
        )->typing.Optional[GitignoreRule]:
        """
        Return the first rule that matches a given file
        None, if none of the rules match
        """
        if not isinstance(file,Path):
            file=Path(file)
        here="."
        if self.currentFile is not None:
            here=self.currentFile.absolute().parent
        file=str(file.absolute().relative_to(here))
        for rule in self._rules:
            if rule.match(file) is not None:
                return rule
        return None
    whichRuleMatched=firstRuleMatch
    whichRuleMatches=firstRuleMatch

    def isIgnored(self,file:typing.Union[str,Path])->bool:
        """
        Check to see if a file is ignored or not
        """
        return self.whichRuleMatched(file) is not None
    ignored=isIgnored

    def isNotIgnored(self,file:typing.Union[str,Path])->bool:
        """
        Determine if a file is not ignored by the gitignore
        """
        return self.whichRuleMatched(file) is None
    notIgnored=isNotIgnored
    isAllowed=isNotIgnored
    ok=isNotIgnored
    isOk=isNotIgnored
    check=isNotIgnored

    def __repr__(self):
        return '\n'.join(self._dataLines)


def main(argv:typing.List[str]):
    """
    Main program entrypoint
    """
    from glob import glob
    printHelp=False
    didSomething=False
    gitignore=Gitignore('.',errorOnFileNotFound=False)
    for arg in argv[1:]:
        if arg.startswith('-'):
            kv=arg.split('=',1)
            k=kv[0].lower()
            if k=='--add':
                if len(kv)>1:
                    for expression in kv[1].split(','):
                        gitignore.add(expression)
                        gitignore.save()
                        didSomething=True
            elif k=='--remove':
                if len(kv)>1:
                    for expression in kv[1].split(','):
                        gitignore.remove(expression)
                        gitignore.save()
                        didSomething=True
            elif k=='--check':
                if len(kv)>1:
                    for expression in kv[1].split(','):
                        didSomething=True
                        for filename in glob(expression):
                            if gitignore.check(filename):
                                print(f'ALLOW {filename}')
                            else:
                                print(f'SKIP {filename}')
            elif k=='--list' or k=='--ls':
                print(gitignore)
                didSomething=True
            elif k=='--help':
                printHelp=True
            else:
                print(f'Unknown parameter "{k}"')
                printHelp=True
        else:
            gitignore=Gitignore(arg)
    if printHelp or not didSomething:
        print('Handle .gitignore files')
        print('Add operations will happen in order.')
        print('  (probably always want the .gitignore file first!)')
        print('USAGE:')
        print('  gitignore [file(s)] [operation(s)]')
        print('OPERATIONS:')
        print('  --help ........... this help')
        print('  --list ........... list gitignore rules')
        print('  --add=[expn] ..... add to gitignore')
        print('  --remove=[expn] .. remove from gitignore')
        print('  --check=[files] .. test a file or glob expression against .gitignore file')


if __name__=="__main__":
    import sys
    sys.exit(main(sys.argv))
