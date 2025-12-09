"""
General useful tools
"""
import typing
from pathlib import Path


SOURCE_EXTENSIONS=[
    '.c','.cc','.cxx','.cpp','.c++','.java','.ii','.ixx','.ipp','.i++','.inl','.idl',
    '.ddl','.odl','.h','.hh','.hxx','.hpp','.h++','.l','.cs','.d','.php','.php4',
    '.php5','.phtml','.inc','.m','.markdown',
    #'.md',
    '.mm','.dox','.py','.pyw','.f90',
    '.f95','.f03','.f08','.f18','.f','.for','.vhd','.vhdl','.ucf','.qsf','.ice']


def containsSource(directory:typing.Union[str,Path])->bool:
    """
    Determine if a directory contains source code
    """
    if not isinstance(directory,Path):
        directory=Path(directory)
    for file in directory.iterdir():
        if file.suffix.lower() in SOURCE_EXTENSIONS:
            return True
    return False


def subdirectories(directory:typing.Union[str,Path])->typing.Generator[Path,None,None]:
    """
    Get all subdirectories of a certain directory
    """
    if not isinstance(directory,Path):
        directory=Path(directory)
    for file in directory.iterdir():
        if file.is_dir():
            yield file


def findDoxygenInputDirs(
    startingDirectories:typing.Union[str,Path,typing.Iterable[typing.Union[str,Path]]]='.'
    )->typing.Generator[Path,None,None]:
    """
    Find all doxygen input dirs, that is,
    topmost directories containing source code.
    """
    if isinstance(startingDirectories,(str,Path)):
        startingDirectories=[startingDirectories]
    tape:typing.List[Path]=[Path(path).absolute() for path in startingDirectories]
    for directory in tape:
        if containsSource(directory):
            yield directory
        else:
            tape.extend(subdirectories(directory))
