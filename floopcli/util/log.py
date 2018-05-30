# based on https://gist.github.com/JesseBuesking/10674086#file-logging-yaml-L10
import os
import multiprocessing, threading, logging, sys, traceback
from logging.handlers import RotatingFileHandler
from typing import TypeVar

LogType = TypeVar('LogType', bound='Log')
'''Generic Log type'''

class Log(logging.Handler):
    '''
    Queue-based single-file logger for parallel processes

    Args:
        name (str):
            name of the logger
        mode (str):
            write mode; defaults to 'a' (append)
        maxsize (int):
            maximum size in bytes of log file
        rotate (int):
            number of historical log files to retain; defaults to 0
    '''
    def __init__(self, name, mode, maxsize, rotate): # type: (LogType, str, str, int, int) -> None 
        logging.Handler.__init__(self)
        self._handler = RotatingFileHandler(name, mode, maxsize, rotate)
        self.queue = multiprocessing.Queue(-1) #type: multiprocessing.Queue
        t = threading.Thread(target=self.receive)
        t.daemon = True
        t.start()

    def setFormatter(self, fmt): # type: (LogType, logging.Formatter) -> None
        '''
        Set logging formatter

        Args:
            fmt (:py:class:`logging.Formatter`):
                valid formatter; read more about valid formatters `here <https://docs.python.org/3/library/logging.html#formatter-objects>`_
        '''
        logging.Handler.setFormatter(self, fmt)
        self._handler.setFormatter(fmt)

    def receive(self): # type: (LogType) -> None
        '''
        Receive logging records from queue 

        Raises:
            Exception:
                re-raise after :py:class:`KeyboardInterrupt` or :py:class:`SystemExit`
        '''
        while True:
            try:
                record = self.queue.get()
                self._handler.emit(record)
            except (KeyboardInterrupt, SystemExit):
                raise
            except EOFError:
                break
            except:
                traceback.print_exc(file=sys.stderr)

    def send(self, s): # type: (LogType, LogRecord) -> None
        '''
        Send logging record to logging queue

        Args:
            s (:py:class`logging.LogRecord`):
                record to be logged
        '''
        self.queue.put_nowait(s)

    def _format_record(self, record): # type: (LogType, logging.LogRecord) -> logging.LogRecord
        '''
        Format record to ensure it is pickle-able

        Args:
            record (:py:class:`logging.LogRecord`):
                logging record
        '''
        # ensure that exc_info and args have been stringified. Removes any
        # chance of unpickleable things inside and possibly reduces message size
        # sent over the pipe
        if record.args:
            record.msg = record.msg % record.args
            record.args = None
        if record.exc_info:
            dummy = self.format(record)
            record.exc_info = None
        return record

    def emit(self, record): # type: (LogType, logging.LogRecord) -> None 
        '''
        Format and send record to queue

        Args:
            record (:py:class:`logging.LogRecord`):
                logging record

        Raises:
            Exception:
                re-raise after :py:class:`KeyboardInterrupt` or :py:class:`SystemExit`
        '''
        try:
            s = self._format_record(record)
            self.send(s)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def close(self): # type: (LogType) -> None
        '''
        Close logger and all associated handlers
        '''
        self._handler.close()
        logging.Handler.close(self)
