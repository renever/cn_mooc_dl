# -*- coding: utf-8 -*-

from __future__ import print_function

import json
import logging
import re
import sys
import os
import requests
from bs4 import BeautifulSoup
import HTMLParser

from utils import *

def main():

    args = parse_args()

    if args.username is None:
        print ('No username specified.')
        sys.exit(1)
    if args.password is None:
        print ('No password specified.')
        sys.exit(1)

    user_email = args.username
    user_pswd = args.password
    course_link = args.course_url[0]
    path = args.path
    overwrite = args.overwrite

    regex = r'(?:https?://)?(?P<site>[^/]+)/(?P<baseurl>[^/]+)/(?P<institution>[^/]+)/(?P<coursename>[^/]+)/(?P<offering>[^/]+).*'
    m = re.match(regex, course_link)  

    if m is None:
        print ('The URL provided is not valid for xuetangx.')
        sys.exit(0)

    if m.group('site') in ['www.xuetangx.com']:
        login_suffix = 'login_ajax'
    else:
        print ('The URL provided is not valid for xuetangx.')
        sys.exit(0)

    homepage = 'https://' + m.group('site')
    login_url = homepage + '/' + login_suffix
    dashboard = homepage + '/dashboard'
    coursename = m.group('coursename')
    course_id = '%s/%s/%s' % (m.group('institution'),
                              m.group('coursename'),
                              m.group('offering'))

    session = requests.Session()
    session.get(homepage)
    csrftoken = session.cookies['csrftoken']

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,zh-TW;q=0.4',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
        'Referer': homepage + '/login',
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': csrftoken,
    }

    post_data = {
                'email': user_email,
                'password': user_pswd
                }
    session.headers.update(headers)
    r = session.post(login_url, data=post_data)
    data = r.content.decode('utf-8')
    resp = json.loads(data)

    if not resp.get('success', False):
        print('Problems suppling credentials to xuetangx.')
        exit(2)

    print ('Login done...')

    print ('Parsing...', end="")
    course_urls = []
    new_url = "%s/courses/%s/courseware" % (homepage, course_id)
    course_urls.append(new_url)
    url = course_urls[0]
    r = session.get(url)
    courseware = r.content
    soup = BeautifulSoup(courseware)
    data = soup.find('nav',{'aria-label':'课程导航'})

    syllabus = []

    for week in data.find_all('div', {'class':'chapter'}):
        week_name = clean_filename(week.h3.a.string)
        week_content = []
        for lesson in week.ul.find_all('a'):
            lesson_name = lesson.p.getText()
            lesson_url = homepage + lesson['href']

            r = session.get(lesson_url)
            lesson_page = HTMLParser.HTMLParser().unescape(r.content.decode('utf8'))
            lesson_soup = BeautifulSoup(lesson_page)

            lec_map = {}
            tab_lists = lesson_soup.find_all('a',{'role':'tab'})
            for tab in tab_lists:
                lec_map[tab.get('id')] = tab.get('title')
            
            lesson_content = []
            for tab in lesson_soup.find_all('div', attrs={'class':"seq_contents tex2jax_ignore asciimath2jax_ignore"}):
                if tab.video is not None:
                    get_vid_url = 'https://www.xuetangx.com/videoid2source/' + tab.source.get('src')
                    r = session.get(get_vid_url)
                    data = r.content
                    resp = json.loads(data)
                    if resp['sources']!=None: 
                        if resp['sources']['quality20']:
                            tab_video_link = resp['sources']['quality20'][0]
                        elif resp['sources']['quality10']:
                            tab_video_link = resp['sources']['quality10'][0]
                        else:
                            print('\nATTENTION: Video Missed for \"%s\"' %lec_map[tab.get('aria-labelledby')])
                            continue
                    else:
                        print('\nATTENTION: Faile to git video for \"%s\"' %lec_map[tab.get('aria-labelledby')])
                        continue
                    
                    tab_title = lec_map[tab.get('aria-labelledby')]
                    tab_subs = tab.find_all('track',attrs={'kind':'subtitles'})
                    tab_subs_url = []
                    for sub in tab_subs:
                        sub_url = 'https://www.xuetangx.com' + sub.get('src')
                        tab_subs_url.append((sub_url, sub.get('srclang')))
                    lesson_content.append((tab_title,tab_video_link,tab_subs_url)) 
            
            # exclude lessons without video                           
            if lesson_content:
                week_content.append((lesson_name, lesson_content))

            print ('.', end="")
        if week_content:
            syllabus.append((week_name, week_content))

    print ("Done.")

    print ("Downloading...")

    retry_list = []
    for (week_num, (week_name, week_content)) in enumerate(syllabus):
        week_name = '%02d %s' %(week_num+1, clean_filename(week_name))
        for (lesson_num,(lesson_name, lesson_content)) in enumerate(week_content):

            lesson_name = '%02d %s' %(lesson_num+1, clean_filename(lesson_name))
            dir = os.path.join(path, coursename, week_name, lesson_name)
            if not os.path.exists(dir):
                mkdir_p(dir)

            for (lec_num, (lec_title, lec_video_url, lec_subtitle)) in enumerate(lesson_content):
                lec_title = '%02d %s' %(lec_num+1, clean_filename(lec_title))
                vfilename = os.path.join(dir, lec_title)
                print (lec_video_url)
                print (vfilename + '.mp4')
                try:
                    resume_download_file(session, lec_video_url, vfilename + '.mp4', overwrite )
                except Exception as e:
                    print(e)
                    print('Error, add it to retry list')
                    retry_list.append((lec_video_url, vfilename + '.mp4'))

                for (sub_url, language) in lec_subtitle:
                    sfilename = vfilename + '.' + language
                    print (sub_url)
                    print (sfilename + '.srt')
                    if not os.path.exists(sfilename + '.srt') or overwrite:
                        try:
                            download_file(session, sub_url, sfilename + '.srt')
                        except Exception as e:
                            print (e)
                            print('Error, add it to retry list')
                            retry_list.append((sub_url, sfilename + '.srt'))
                            continue
                    else:
                        print ('Already downloaded.')

    retry_times = 0
    while len(retry_list) != 0 and retry_times < 3:
        print('%d items should be retried, retrying...' % len(retry_list))
        retry_times += 1
        for (url, filename) in retry_list:
            try:
                print(url)
                print(filename)
                resume_download_file(session, url, filename, overwrite )
            except Exception as e:
                print(e)
                print('Error, add it to retry list')
                continue

            retry_list.remove((url, filename)) 
    
    if len(retry_list) != 0:
        print('%d items failed, please check it' % len(retry_list))
    else:
        print('All done.')


if __name__ == '__main__':
    main()
