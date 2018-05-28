import pytest

from floopcli.util.syscall import syscall, SystemCallException

def test_syscall_pwd():
    syscall('pwd', check=True, verbose=True)

def test_syscall_check_nonzero_exit_fails():
    with pytest.raises(SystemCallException):
        syscall('cp', check=True, verbose=True)
