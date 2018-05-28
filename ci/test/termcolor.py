from datetime import datetime

class termcolor:
    RED = '\033[38;5;160m'
    GREEN = '\033[38;5;35m'
    YELLOW = '\033[38;5;190m'
    TIME = '\033[38;5;38m'
    DEFAULT = '\033[0m'
    END = '\033[0m'

def cprint(string, color, time=True, tag=None):
    print_string = color + string + termcolor.END
    if time:
        time_string = '[' + termcolor.TIME + str(datetime.now()) + termcolor.END + '] '
        if tag is not None:
            time_string = '[' + termcolor.TIME + str(datetime.now()) + ' ' + tag + termcolor.END + '] '
        print_string = time_string + print_string
    print(print_string)
