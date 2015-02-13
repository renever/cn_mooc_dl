# -*- coding: utf-8 -*-
"""
This module contains a set of functions to be used by others.
Some of them are ripped from https://github.com/coursera-dl/
"""


import time
import math
import sys
import os
import argparse
import re
import zlib
import errno

class DownloadProgress(object):
    """
    Report download progress.
    Ripped from https://github.com/coursera-dl/
    """
    def __init__(self, start, total):
        if total in [0, '0', None]:
            self._total = None
        else:
            self._total = int(total)

        self._current = int(start)
        self._start = int(start)
        self._time_start = 0
        self._time_now = 0

        self._finished = False

    def start(self):
        self._time_now = time.time()
        self._time_start = self._time_now

    def stop(self):
        self._time_now = time.time()
        self._finished = True
        if self._total is None:
            self._total = self._current
        self.report_progress()
        if self._total != self._current:
            raise Exception('Error: Stopped abnormally.')

    def read(self, bytes):
        self._time_now = time.time()
        self._current += bytes
        self.report_progress()

    def calc_percent(self):
        if self._total is None:
            return '--%'
        percentage = int(float(self._current) / float(self._total) * 100.0)
        done = int(percentage/2)
        return '[{0: <50}] {1}%'.format(done * '>', percentage)

    def calc_speed(self):
        dif = self._time_now - self._time_start
        if self._current == 0 or dif < 0.001:  # One millisecond
            return '---b/s    '
        return '{0}/s    '.format(format_bytes(float(self._current - self._start) / dif))

    def report_progress(self):
        """
        Report download progress.
        Ripped from https://github.com/coursera-dl/
        """
        percent = self.calc_percent()
        total = format_bytes(self._total)

        speed = self.calc_speed()
        total_speed_report = '{0} at {1}'.format(total, speed)

        report = '\r{0: <56} {1: >20}'.format(percent, total_speed_report)

        if self._finished:
            print report
        else:
            print (report + "\r"),

        sys.stdout.flush()               

def format_bytes(bytes):
    """
    Get human readable version of given bytes.
    Ripped from https://github.com/rg3/youtube-dl
    """
    if bytes is None:
        return 'N/A'
    if type(bytes) is str:
        bytes = float(bytes)
    if bytes == 0.0:
        exponent = 0
    else:
        exponent = int(math.log(bytes, 1024.0))
    suffix = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'][exponent]
    converted = float(bytes) / float(1024 ** exponent)
    return '{0:.2f}{1}'.format(converted, suffix)


def mkdir_p(path, mode=0o777):
    """
    Create subdirectory hierarchy given in the paths argument.
    Ripped from https://github.com/coursera-dl/
    """

    try:
        os.makedirs(path, mode)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def download_file(session, url, filename):

    attempts_count = 0
    error_msg = ''

    while attempts_count < 2:

        r = session.get(url, stream = True)
        if r.status_code is not 200:
            if r.reason:
                error_msg = r.reason + ' ' + str(r.status_code)
            else:
                error_msg = 'HTTP Error ' + str(r.status_code)
            
            if attempts_count + 1 < 2:
                wait_interval = 2 ** (attempts_count + 1)
                msg = 'Error downloading, will retry in {0} seconds ...'
                print(msg.format(wait_interval))
                time.sleep(wait_interval)
                attempts_count += 1
                continue
            else:
                raise Exception('Connection Error: %s' % error_msg)

        content_length = r.headers.get('content-length')
        progress = DownloadProgress(0, content_length)
        chunk_sz = 1048576 

        with open(filename, 'wb') as f:
            progress.start()
            while True:
                data = r.raw.read(chunk_sz, decode_content=True)                   
                if not data:
                    progress.stop()
                    break
                progress.read(len(data))
                f.write(data)
        r.close()
        break


def resume_download_file(session, url, filename, overwrite = False):

    if os.path.exists(filename) and not overwrite:
        resume_len = os.path.getsize(filename)
        file_mode = 'ab'
    else:
        resume_len = 0   
        file_mode = 'wb'     

    attempts_count = 0
    error_msg = ''

    while attempts_count < 2:

        session.headers['Range'] = 'bytes=0-'
        r = session.get(url, stream = True)

        if r.status_code != 200 and r.status_code != 206:
            if r.reason:
                error_msg = r.reason + ' ' + str(r.status_code)
            else:
                error_msg = 'HTTP Error ' + str(r.status_code)
            
            if attempts_count + 1 < 2:
                wait_interval = 2 ** (attempts_count + 1)
                msg = 'Error downloading, will retry in {0} seconds ...'
                print(msg.format(wait_interval))
                time.sleep(wait_interval)
                attempts_count += 1
                continue
            else:
                raise Exception('Connection Error: %s' % error_msg)
        
        total_length = r.headers.get('content-length')

        if resume_len != 0:
            if total_length is None or resume_len == int(total_length):
                print ('Already downloaded.')
                break

        session.headers['Range'] = 'bytes=%d-' % (resume_len)
        r = session.get(url, stream = True)  

        

        progress = DownloadProgress(resume_len, total_length)
        chunk_sz = 1048576 

        with open(filename, file_mode) as f:
            progress.start()
            while True:
                data = r.raw.read(chunk_sz, decode_content=True)                   
                if not data:
                    progress.stop()
                    break
                progress.read(len(data))
                f.write(data)
        r.close()
        break


def parse_args():

    parser = argparse.ArgumentParser(description = 'Download lecture material from mooc websites')

    
    parser.add_argument('-u',
                        '--username',
                        dest='username',
                        action='store',
                        default=None,
                        help='username')

    parser.add_argument('-p',
                        '--password',
                        dest='password',
                        action='store',
                        default=None,
                        help='password')

    parser.add_argument('course_url',
                        action='store',
                        nargs='+',
                        help='(e.g. "http://www.xuetangx.com/courses/NTHU/MOOC_01_004/2014_T2/courseware/")')

    # optional
    parser.add_argument('--path',
                        dest='path',
                        action='store',
                        default='.',
                        help='path to save the files')


    parser.add_argument('-o',
                        '--overwrite',
                        dest='overwrite',
                        action='store_true',
                        default=False,
                        help='whether existing files should be overwritten'
                             ' (default: False)')
    
    args = parser.parse_args()
    
    return args


def clean_filename(s):
    """
    Sanitize a string to be used as a filename.

    If minimal_change is set to true, then we only strip the bare minimum of
    characters that are problematic for filesystems (namely, ':', '/' and
    '\x00', '\n').
    """

    s = s.replace(':', '_') \
        .replace('/', '_')\
        .replace('\x00', '_')

    s = re.sub('[\n\\\*><\?\"\|\t]', '', s)
    s = re.sub(' +$','', s)
    s = re.sub('^ +','', s)


    return s