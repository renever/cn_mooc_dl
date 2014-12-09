#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module contains a set of functions to be used by edx-dl.
"""


import time
import math
import sys
import os
import argparse
import re

class DownloadProgress(object):
    """
    Report download progress.
    Ripped from https://github.com/coursera-dl/
    """
    def __init__(self, total):
        if total in [0, '0', None]:
            self._total = None
        else:
            self._total = int(total)

        self._current = 0
        self._start = 0
        self._now = 0

        self._finished = False

    def start(self):
        self._now = time.time()
        self._start = self._now

    def stop(self):
        self._now = time.time()
        self._finished = True
        self._total = self._current
        self.report_progress()

    def read(self, bytes):
        self._now = time.time()
        self._current += bytes
        self.report_progress()

    def calc_percent(self):
        if self._total is None:
            return '--%'
        percentage = int(float(self._current) / float(self._total) * 100.0)
        done = int(percentage/2)
        return '[{0: <50}] {1}%'.format(done * '>', percentage)

    def calc_speed(self):
        dif = self._now - self._start
        if self._current == 0 or dif < 0.001:  # One millisecond
            return '---b/s'
        return '{0}/s'.format(format_bytes(float(self._current) / dif))

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
            print report + "\r",

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
                break

        content_length = r.headers.get('content-length')
        progress = DownloadProgress(content_length)
        chunk_sz = 1048576 

        with open(filename, 'wb') as f:
            progress.start()
            while True:
                data = r.raw.read(chunk_sz)                   
                if not data:
                    progress.stop()
                    break
                progress.read(len(data))

                f.write(data)
        r.close()
        break

    if attempts_count == 2:
        print ('Skipping, can\'t download file ...')
        print (error_msg)

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
                        default='',
                        help='path to save the files')


    parser.add_argument('-o',
                        '--overwrite',
                        dest='overwrite',
                        action='store_true',
                        default=False,
                        help='whether existing files should be overwritten'
                             ' (default: False)')

    
    args = parser.parse_args()


    if not args.username:
        print ('No username specified.')
        sys.exit(1)
    if not args.password:
        print ('No password specified.')
        sys.exit(1)
    
    return args