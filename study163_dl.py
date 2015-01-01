# -*- coding: utf-8 -*-

from __future__ import print_function

import re
import os
import sys
import requests
import time

from utils import mkdir_p, parse_args, clean_filename, DownloadProgress

def download_file_study163(session, url, filename):

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
        progress = DownloadProgress(0, content_length)
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

def download_syllabus_study163(session, syllabus, path = '', overwrite = False):

    headers = {
            'Accept':'*/*',
            'Accept-Encoding':'gzip, deflate, sdch',
            'Accept-Language':'zh-CN,zh;q=0.8,en;q=0.6,zh-TW;q=0.4',
            'Connection':'keep-alive',
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
            }
    get_token_url = 'http://study.163.com/video/getVideoAuthorityToken.htm'

    session.headers.update(headers);
            
    course_id = syllabus[0]
    course = syllabus[1]
    
    for (chapter_num,(chapter, lessons)) in enumerate(course):
        chapter_name = clean_filename(chapter)
        dir = os.path.join(path, ('%02d %s'% (chapter_num+1, chapter_name)))
        if not os.path.exists(dir):
            mkdir_p(dir)        
        for (lesson_num,(lesson_url, lesson_name)) in enumerate(lessons):
            fmt = lesson_url.split('.')[-1]
            lesson_name = clean_filename(lesson_name.decode('raw_unicode_escape'))
            filename = os.path.join(dir, '%02d_%s.%s' %(lesson_num+1, lesson_name, fmt))
            print(filename)
            r = session.get(get_token_url)
            video_url_suffix = '88C752A6C3513A0A5EEFA4CD7091A96E365D0185B8133CC883910200B043BC0F57E3024A35D1C582757D905A6B9289E9f4eej632de59'\
                                 + r.content 
            video_url = lesson_url + '?key=' + video_url_suffix
            if overwrite or not os.path.exists(filename):
                download_file_study163(session, video_url, filename )
            else:
                print ('Already downloaded')



def parse_syllabus_study163(session, page):
    data = page.splitlines(True)

    multi_resolution_flag = ['videoSHDUrl',
                            'flvShdUrl',
                            'videoHDUrl',
                            'flvHdUrl',
                            'videoUrl',
                            'flvSdUrl']    
    course = []
    lessons = []
    course_id = ''
    cur_chapter = ''

    get_videoid_url = 'http://study.163.com/dwr/call/plaincall/LessonLearnBean.getVideoLearnInfo.dwr'
    
    headers = {
            'Accept':'*/*',
            'Accept-Encoding':'gzip, deflate',
            'Accept-Language':'zh-CN,zh;q=0.8,en;q=0.6,zh-TW;q=0.4',
            'Connection':'keep-alive',
            'Content-Length':'230',
            'Content-Type':'text/plain',
            'Cookie':'videoResolutionType=3;',
            'Host':'study.163.com',
            'Origin':'http://study.163.com',
            'Referer':'http://study.163.com/course/courseLearn.htm?courseId=953005',
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
            }

    for line in data:
        print('.', end="")
        
        lesson_info = dict(re.findall(r"s\d+\.(?P<name>.*?)=(?P<value>.*?);",line))

        if lesson_info:

            if lesson_info.has_key('courseId'):
                course_id = lesson_info['courseId']
                if lessons:
                    course.append((cur_chapter, lessons))
                    lessons = []
                cur_chapter = lesson_info['name'].decode('raw_unicode_escape')

            elif lesson_info.has_key('lessonName'):
                params =  {
                        'callCount':'1',
                        'scriptSessionId':'${scriptSessionId}190', #* , but arbitrarily
                        'httpSessionId':'686777b732444cd2b43020d3fcddd0d1',
                        'c0-scriptName':'LessonLearnBean',
                        'c0-methodName':'getVideoLearnInfo',
                        'c0-id':'0',
                        'c0-param0':'string:' + lesson_info['id'],
                        'c0-param1':'string:' + course_id,
                        'batchId':'969403', #* , but arbitrarily
                        }
                r = session.post(get_videoid_url, headers = headers, data = params, cookies = {'Cookie':'videoResolutionType=3;'})
                if r.status_code is not 200:
                    print("Failed to get video ID.")
                    sys.exit(0)   
                s = re.search(r"remoteHandleCallback.+{(?P<content>.*)}", r.content)
                if not s:
                    print("Failed to get video ID.")
                    sys.exit(0) 
                                        
                info = dict(re.findall(r"(?P<name>.*?):(?P<value>.*?),", s.group('content')))
                    
                for res in multi_resolution_flag:
                    if info[res] != 'null':
                        lesson_url = info[res].strip('\"')
                        break
  
                lessons.append((lesson_url, lesson_info['lessonName'].strip('\"')))
                
    course.append((cur_chapter, lessons))
    return (course_id, course)
    
    
def main():
    
    args = parse_args()
    
    course_link = args.course_url[0]
    path = args.path
    overwrite = args.overwrite
    
    regex = r'(?:https?://)(?P<site>[^/]+)/course/introduction/(?P<courseid>[^/]+)\.htm'
    
    m = re.match(regex, course_link)  

    if m is None:
        print ('The URL provided is not valid for study.163.com')
        sys.exit(0)
    if m.group('site') not in ['study.163.com']:
        print ('The URL provided is not valid for study.163.com')
        sys.exit(0)   
    path = os.path.join(path, m.group('courseid'))         
    headers = {
            'Accept':'*/*',
            'Accept-Encoding':'gzip, deflate, sdch',
            'Accept-Language':'zh-CN,zh;q=0.8,en;q=0.6,zh-TW;q=0.4',
            'Connection':'keep-alive',
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
            'X-Requested-With':'ShockwaveFlash/16.0.0.235',
            }
        
    post_data = {
                'callCount':1,
                'scriptSessionId':'${scriptSessionId}190',
                'c0-scriptName':'PlanNewBean',
                'c0-methodName':'getPlanCourseDetail',
                'c0-id': 0,
                'c0-param0':'string:' + m.group('courseid'),
                'c0-param1':'number:0',
                'c0-param2':'null:null',                
                'batchId':434820, #arbitrarily
                }
    course_detail_dwr_url = 'http://study.163.com/dwr/call/plaincall/PlanNewBean.getPlanCourseDetail.dwr'
    
    session = requests.Session()
    session.headers.update(headers)    
    r = session.post(course_detail_dwr_url, data = post_data)
    
    if r.status_code is not 200:
        print('Failed to get .dwr file.')
        sys.exit(0)

    print ('Parsing...', end="") 
        
    syllabus = parse_syllabus_study163(session, r.content)
    
    if syllabus:
        print ('Successful.')
    else:
        print ('Failed.')
    
    download_syllabus_study163(session, syllabus, path, overwrite)
    
if __name__ == '__main__':
    main()