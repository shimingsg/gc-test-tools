from contextlib import contextmanager
from logging import getLogger
from stat import S_IWRITE
from shutil import rmtree
from typing import List, Optional, Tuple
from subprocess import CalledProcessError
from subprocess import list2cmdline
from subprocess import PIPE, STDOUT, DEVNULL
from subprocess import Popen
from io import StringIO

import os
import sys

def get_python_executable() -> str:
    '''
    Gets the absolute path of the executable binary for the Python interpreter.
    '''
    if not sys.executable:
        raise RuntimeError('Unable to get the path to the Python executable.')
    return sys.executable    

def get_script_path() -> str:
    '''Gets this script directory.'''
    return os.path.dirname(os.path.realpath(__file__))

def get_root_path() -> str:
    '''Gets repository root directory.'''
    return os.path.abspath(os.path.join(get_script_path(), '..'))

def make_directory(path: str):
    if not path:
        raise TypeError('Undefined path.')
    os.makedirs(path, exist_ok=True)

def remove_directory(path: str) -> None:
    '''Recursively deletes a directory tree.'''
    if not path:
        raise TypeError('Undefined path.')
    if not isinstance(path, str):
        raise TypeError('Invalid type.')

    if os.path.isdir(path):
        def handle_rmtree_errors(func, path, exc_info):
            """
            Helper function to handle long path errors on Windows.
            """
            if os.name == 'nt' and not path.startswith('\\\\?\\'):
                path = '\\\\?\\' + os.path.abspath(path)
            os.chmod(path, S_IWRITE)
            func(path)
        rmtree(path, onexc=handle_rmtree_errors)

@contextmanager
def push_dir(path: Optional[str] = None):
    '''
    Adds the specified location to the top of a location stack, then changes to
    the specified directory.
    '''
    if path:
        prev = os.getcwd()
        try:
            abspath = path if os.path.isabs(path) else os.path.abspath(path)
            getLogger().info('$ pushd "%s"', abspath)
            os.chdir(abspath)
            yield
        finally:
            getLogger().info('$ popd')
            os.chdir(prev)
    else:
        yield

def set_environment_variable(name: str, value: str, ):
    os.environ[name] = value
    
class RunCommand:
    '''
    This is a class wrapper around `subprocess.Popen` with an additional set
    of logging features.
    '''

    def __init__(
            self,
            cmdline: List[str],
            success_exit_codes: Optional[List[int]] = None,
            verbose: bool = False,
            echo: bool = True,
            retry: int = 0):
        if cmdline is None:
            raise TypeError('Unspecified command line to be executed.')
        if not cmdline:
            raise ValueError('Specified command line is empty.')

        self.__cmdline = cmdline
        self.__verbose = verbose
        self.__retry = retry
        self.__echo = echo

        if success_exit_codes is None:
            self.__success_exit_codes = [0]
        else:
            self.__success_exit_codes = success_exit_codes

    @property
    def cmdline(self) -> List[str]:
        '''Command-line to use when starting the application.'''
        return self.__cmdline

    @property
    def success_exit_codes(self) -> List[int]:
        '''
        The successful exit codes that the associated process specifies when it
        terminated.
        '''
        return self.__success_exit_codes

    @property
    def echo(self) -> bool:
        '''Enables/Disables echoing of STDOUT'''
        return self.__echo

    @property
    def verbose(self) -> bool:
        '''Enables/Disables verbosity.'''
        return self.__verbose

    @property
    def stdout(self) -> str:
        return self.__stdout.getvalue()

    def __runinternal(self, working_directory: Optional[str] = None) -> Tuple[int, str]:
        should_pipe = self.verbose
        with push_dir(working_directory):
            quoted_cmdline = '$ '
            quoted_cmdline += list2cmdline(self.cmdline)

            getLogger().info(quoted_cmdline)

            with Popen(
                    self.cmdline,
                    stdout=PIPE if should_pipe else DEVNULL,
                    stderr=STDOUT,
                    universal_newlines=False,
                    encoding=None,
                    bufsize=0
            ) as proc:
                if proc.stdout is not None:
                    with proc.stdout:
                        self.__stdout = StringIO()
                        for raw_line in iter(proc.stdout.readline, b''):
                            line = raw_line.decode('utf-8', errors='backslashreplace')
                            self.__stdout.write(line)
                            line = line.rstrip()
                            if self.echo:
                                getLogger().info(line)
                proc.wait()
                return (proc.returncode, quoted_cmdline)


    def run(self, working_directory: Optional[str] = None) -> int:
        '''Executes specified shell command.'''

        retrycount = 0
        (returncode, quoted_cmdline) = self.__runinternal(working_directory)
        while returncode not in self.success_exit_codes and self.__retry != 0 and retrycount < self.__retry:
            (returncode, _) = self.__runinternal(working_directory)
            retrycount += 1

        if returncode not in self.success_exit_codes:
            getLogger().error(
                "Process exited with status %s", returncode)
            raise CalledProcessError(
                returncode, quoted_cmdline)
        
        return returncode