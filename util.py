"""
General useful tools
"""
import typing

from paths import Url,UrlCompatible,UrlListCompatible,asUrl,toUrlList


SOURCE_EXTENSIONS=[
    '.c','.cc','.cxx','.cpp','.c++','.java','.ii','.ixx','.ipp','.i++','.inl','.idl',
    '.ddl','.odl','.h','.hh','.hxx','.hpp','.h++','.l','.cs','.d','.php','.php4',
    '.php5','.phtml','.inc','.m','.markdown',
    #'.md',
    '.mm','.dox','.py','.pyw','.f90',
    '.f95','.f03','.f08','.f18','.f','.for','.vhd','.vhdl','.ucf','.qsf','.ice']


def containsSource(directory:UrlCompatible)->bool:
    """
    Determine if a directory contains source code
    """
    directory=asUrl(directory)
    for file in directory.iterdir():
        if file.ext.lower() in SOURCE_EXTENSIONS:
            return True
    return False


def subdirectories(directory:UrlCompatible
    )->typing.Generator[Url,None,None]:
    """
    Get all subdirectories of a certain directory
    """
    directory=asUrl(directory)
    for file in directory.iterdir():
        if file.isDir:
            yield file


def findDoxygenInputDirs(
    startingDirectories:UrlListCompatible='.'
    )->typing.Generator[Url,None,None]:
    """
    Find all doxygen input dirs, that is,
    topmost directories containing source code.
    """
    tape=list(toUrlList(startingDirectories))
    for directory in tape:
        if containsSource(directory):
            yield directory
        else:
            tape.extend(subdirectories(directory))
