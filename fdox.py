"""
Fast doxygen of directory
"""
import typing
import os
from pathlib import Path
from k_runner import OsRun,OsRunJob
from doxyFile import createDoxyFile


FDOX_DEFAULT_DIRECTORY=os.environ.get('FDOX_DEFAULT_DIRECTORY','.')


def fdox(
    directory:typing.Union[str,Path,None]=None,
    addDoxygenStuffToGitIgnore:bool=True
    )->OsRunJob:
    """
    Fast doxygen of directory

    Returns a background job that is running doxygen
    """
    if directory is None:
        directory=FDOX_DEFAULT_DIRECTORY
    directory=Path(directory)
    if not directory.exists():
        raise FileNotFoundError(str(directory))
    doxyFile=createDoxyFile(directory)
    directory=doxyFile.parent
    if addDoxygenStuffToGitIgnore:
        from gitignore import Gitignore
        gitignore=Gitignore(directory,errorOnFileNotFound=False)
        gitignore.add('Doxyfile')
        gitignore.add('doxygen/*')
        gitignore.save()
    cmd=['doxygen',doxyFile]
    os.makedirs(directory/'doxygen')
    instance=OsRun(cmd,detach=True,workingDirectory=directory)
    job=instance.runAsync()
    return job


def main(argv:typing.List[str]):
    """
    Main program entrypoint
    """
    addDoxygenStuffToGitIgnore:bool=True
    printHelp=False
    didSomething=False
    for arg in argv[1:]:
        if arg.startswith('-'):
            kv=arg.split('=',1)
            k=kv[0].lower()
            if k=='--addDoxygenStuffToGitIgnore':
                addDoxygenStuffToGitIgnore=kv[1][0].lower() in ('1','y','t')
            elif k=='--help':
                printHelp=True
            else:
                print(f'Unknown parameter "{k}"')
                printHelp=True
        else:
            didSomething=True
            fdox(arg,addDoxygenStuffToGitIgnore)
            addDoxygenStuffToGitIgnore=False
    if printHelp:
        print('Fast doxygen creation.')
        print('Will initialize doxygen and run for the given directory.')
        print('If no directory is specified, will use FDOX_DEFAULT_DIRECTORY from environment')
        print(f'  (currently, "{os.environ.get("FDOX_DEFAULT_DIRECTORY")}")')
        print('If still not specified, uses current directory.')
        print('USAGE:')
        print('  fdox [params] [file_or_dir]')
        print('PARAMS:')
        print('  --help ......... this help')
        print('  --addDoxygenStuffToGitIgnore=[y/n] ... name says it all (default=y)')
    elif not didSomething:
        fdox(None,addDoxygenStuffToGitIgnore)


if __name__=="__main__":
    import sys
    sys.exit(main(sys.argv))
