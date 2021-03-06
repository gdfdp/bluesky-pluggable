# obfsproxy logging code

import logging
import sys

# XXX Add Formatter!!!

our_logger = logging.getLogger('our_logger')
default_handler = logging.StreamHandler(sys.stdout)
our_logger.addHandler(default_handler)
our_logger.propagate = False

def set_log_file(filename):
    """Set up our logger so that it starts logging to file in 'filename' instead."""

    # remove the default handler, and add the FileHandler:
    our_logger.removeHandler(default_handler)

    log_handler = logging.FileHandler(filename)
    our_logger.addHandler(log_handler)

def set_log_severity(sev_string):
    """Update our minimum logging severity to 'sev_string'."""

    # Turn it into a numeric level that logging understands first.
    numeric_level = getattr(logging, sev_string.upper(), None)
    our_logger.setLevel(numeric_level)

def disable_logs():
    """Disable all logging."""

    logging.disable(logging.CRITICAL)

# Redirect logging functions to our custom logger.
debug = our_logger.debug
info = our_logger.info
warning = our_logger.warning
error = our_logger.error
critical = our_logger.critical
