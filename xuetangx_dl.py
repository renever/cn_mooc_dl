#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import json
import logging
import re
import sys
import os
import requests
from bs4 import BeautifulSoup


from utils import mkdir_p, download_file, parse_args

def main():

    args = parse_args()

    user_email = args.username
    user_pswd = args.password
    course_link = args.course_url[0]
    path = args.path
    overwrite = args.overwrite

    regex = r'(?:https?://)(?P<site>[^/]+)/(?P<baseurl>[^/]+)/(?P<institution>[^/]+)/(?P<coursename>[^/]+)/(?P<offering>[^/]+).*'
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

    print ('Login successful...')

    print ('Parsing...', end="")
    course_urls = []
    new_url = "%s/courses/%s/courseware" % (homepage, course_id)
    course_urls.append(new_url)
    url = course_urls[0]
    r = session.get(url)
    courseware = r.content
    soup = BeautifulSoup(courseware)
    data = soup.find('nav',
                     {'aria-label':'课程导航'})

    weeks_soup = data.find_all('div')
    weeks = []
    for week_soup in weeks_soup:
        week_name = week_soup.h3.a.string
        week_urls = [
            '%s/%s' % (homepage, a['href'])
            for a in week_soup.ul.find_all('a')
        ]

        weeks.append((week_name, week_urls))

    print ('.', end="")

    links = [lec_url for week in weeks for lec_url in week[1]]

    video_links = []
    subtitle_links = []

    for link in links:
        r = session.get(link)
        page = r.content
        vid_regexp = b'video/mp4&#34; src=&#34;(.+)&#34;'
        fn_regexp = b'&lt;h2&gt; (.+) &lt;/h2&gt;'


        id_container = re.findall(vid_regexp, page)
        fn_container = re.findall(fn_regexp, page)
        vid_container = zip(id_container, fn_container)

        for (id,fn) in vid_container:
            id2src_link = 'https://www.xuetangx.com/videoid2source/' + id
            r = session.get(id2src_link)
            data = r.content
            resp = json.loads(data)
            if resp['sources']!=None and resp['sources']['quality20']!=None:
                video_links.append((resp['sources']['quality20'][0],fn.decode('utf8')))
            else:
                print ('Fail to get real src by vid')
                exit(2)
            print ('.', end="")


    print ("successful")

    print ("Downloading...")

    dir = os.path.join(path, coursename)
    if not os.path.exists(dir):
        mkdir_p(dir)

    for (lecnum, (lecture_url, lecture_name)) in enumerate(video_links):
        filename = os.path.join(dir, '%02d_%s.mp4' %(lecnum+1, lecture_name))
        if overwrite or not os.path.exists(filename):
            print (filename)
            print (lecture_url)
            download_file(session, lecture_url, filename )
        else:
            print ('%s already downloaded' % filename)


if __name__ == '__main__':
    main()
