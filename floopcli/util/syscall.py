import subprocess
from sys import stdout
from shlex import split
from typing import List, Tuple 

class SystemCallException(Exception):
    '''
    System call returned non-zero exit code
    '''
    pass

# TODO: figure out consistent Python 2/3 typing
def syscall(command, check=False, # type: ignore
        verbose=False): 
    '''
    Call system to run system command

    Args:
        command (str):
            system command; should not contain pipes (|)
        check (bool):
            whether to check for non-zero exit code
        verbose (bool):
            if True, streams command output to stdout

    Raises:
        :py:class:`floopcli.util.SystemCallException`:
            verbose=True and command exited with non-zero code

    Returns:
        (str, str):
            tuple of command output to (stdout, stderr)
    '''
    command_ = split(command)
    try:
        process = subprocess.Popen(command_, stdout=subprocess.PIPE)
        out = ''
        # Python 2: str to bytes?
        # Python 3: unicode to str?
        for line in iter(process.stdout.readline, b''): # type: ignore
            line = line.decode('utf-8')
            out += line
            if verbose:
                # this sits below the logger, so removing the console handler 
                # would not silence this print
                stdout.write(line)
        _, err = process.communicate()
        if err is not None:
            err = err.decode('utf-8')
        if check:
            if process.returncode != 0:
                raise SystemCallException(err)
        return (out, err)
    except (KeyboardInterrupt, SystemCallException) as e:
        try:
            process.kill()
        except OSError:
            pass
        raise SystemCallException
