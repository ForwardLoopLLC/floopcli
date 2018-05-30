import subprocess
from sys import stdout
from shlex import split
from typing import List, Tuple 

class SystemCallException(Exception):
    '''
    System call returned non-zero exit code
    '''
    pass

def syscall(command: str, check: bool=False, verbose: bool=False) -> Tuple[str, str]:
    '''
    Call system to run system command

    Args:
        command (str):
            system command; should not contain pipes (|)
        check (bool):
            whether to check for non-zero exit code
        verbose (bool):
            if True, prints command output to stdout

    Raises:
        :py:class:`floopcli.util.SystemCallException`:
            verbose=True and command exited with non-zero code

    Returns:
        (str, str):
            tuple of command output to (stdout, stderr)
    '''
    command_ = split(command)
    process = subprocess.Popen(command_, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = ''
    for line in process.stdout:
        line = line.decode('utf-8')
        out += line
        if verbose:
            stdout.write(line)
    _, err = process.communicate()
    if err is not None:
        err = err.decode('utf-8')
    if check:
        if process.returncode != 0:
            raise SystemCallException(err)
    return (out, err)
