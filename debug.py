from termcolor import colored
import sys
import shutil

def log_info(msg):
    """
    Print an info message in cyan.
    """
    prefix = colored('INFO: ', 'cyan', attrs=['bold'])
    print(f"{prefix}{msg}")

def log_success(msg):
    """
    Print a success message in green.
    """
    prefix = colored('SUCCESS: ', 'green', attrs=['bold'])
    print(f"{prefix}{msg}")

def log_warning(msg):
    """
    Print a warning message in yellow.
    """
    prefix = colored('WARNING: ', 'yellow', attrs=['bold'])
    print(f"{prefix}{msg}", file=sys.stderr)

def log_error(msg):
    """
    Print an error message in red.
    """
    prefix = colored('ERROR: ', 'red', attrs=['bold'])
    print(f"{prefix}{msg}", file=sys.stderr)

def log_debug(msg):
    """
    Print a debug message in magenta.
    """
    prefix = colored('DEBUG: ', 'magenta', attrs=['bold'])
    print(f"{prefix}{msg}")
