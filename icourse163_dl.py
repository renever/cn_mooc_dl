#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import md5
import re
import requests
import os

from utils import mkdir_p, download_file, parse_args

def main():
    args = parse_args()

    user_email = args.username
    user_pswd = args.password
    course_link = args.course_url[0]
    path = args.path
    overwrite = args.overwrite

    regex = r'(?:https?://)(?P<site>[^/]+)/(?P<baseurl>[^/]+)/(?P<coursename>[^/]+)/?'
    m = re.match(regex, args.course_url[0]) 
    if m is None:
        print ('The URL provided is not valid for icourse163.')
        sys.exit(0)

    if m.group('site') in ['www.icourse163.org']:
        path = os.path.join(path, m.group('coursename'))
    else:
        print ('The URL provided is not valid for icourse163.')
        sys.exit(0)

    login_url = 'https://reg.163.com/logins.jsp'

    headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,zh-TW;q=0.4',
                'Connection': 'keep-alive',
               }

    m = md5.new()
    m.update(user_pswd)
    encryptedpswd =  m.hexdigest()
    post_data = {
                'product': 'imooc',
                'url': 'http://www.icourse163.org/mooc.htm?#/index',
                'savelogin': 1,
                'domains': 'icourse163.org',
                'type': 0,
                'append': 1,
                'username': user_email,
                'password': encryptedpswd
                }


    session = requests.Session()
    session.headers.update(headers)
    r1 = session.post(login_url,data = post_data)

    
    success = re.search('正在登录，请稍等...',r1.content)
    if not success:
        print ('Fail to login.')
        exit(2)
    else:
        print ('Login successful...')
    
    se = re.search('window.location.replace\(\"(.+)\"\)',r1.content)
        
    r = session.get(se.group(1), allow_redirects=False, cookies = {'NTES_PASSPORT':session.cookies['NTES_PASSPORT']})

    # set-cookie: "STUDY_SESS"
    rr = session.get('http://www.icourse163.org/mooc.htm?',allow_redirects=False)
    rrr = session.get(rr.headers['Location'])

    # get course id, it's in cid.group(1)
    r2 = session.get(course_link)
    cid = re.search(r'window\.termDto = {             id:([0-9]+),', r2.content)
    if cid is None:
        cid = re.search(r'termId : \"([0-9]+)\",', r2.content)


    headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36',
                'Accept': '*/*' ,
                'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,zh-TW;q=0.4',
                'Connection': 'keep-alive',
                'Content-Type': 'text/plain',
                'Cookie':'STUDY_SESS=%s; '% session.cookies['STUDY_SESS'],
                'Host':'www.icourse163.org',
                'Origin':'http://www.icourse163.org',
                'Referer':'http://www.icourse163.org/learn/swjtu-94001',
               }

    session.headers.update(headers)

    params =  {
                'callCount':1,
                'scriptSessionId':'${scriptSessionId}190',
                'httpSessionId':'e8890caec7fe435d944c0f318b932719',
                'c0-scriptName':'CourseBean',
                'c0-id': 0,
                'c0-methodName':'getLastLearnedMocTermDto',
                'c0-param0':'number:' + cid.group(1),
                'batchId':434820, #arbitrarily
                }

    getcourse_url = 'http://www.icourse163.org/dwr/call/plaincall/CourseBean.getLastLearnedMocTermDto.dwr'

    r3 = session.post(getcourse_url,data = params)

    print ('Parsing...', end="")

    syllabus = parse_syllabus_icourse163(session, r3.content)

    if syllabus:
        print ('Successful.')
    else:
        print ('Failed.')

    print ('Save files to %s' % path)

    download_syllabus_icourse163(session, syllabus, path)


def download_syllabus_icourse163(session, leclist, path = '', overwrite = False):

    headers = {
                'Accept':'*/*',
                'Accept-Encoding':'gzip, deflate, sdch',
                'Accept-Language':'zh-CN,zh;q=0.8,en;q=0.6,zh-TW;q=0.4',
                'Connection':'keep-alive',
                'Host':'v.stu.126.net', #*
                'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36',
                'X-Requested-With':'ShockwaveFlash/15.0.0.239',
               }

    session.headers.update(headers)
	
    for week in leclist:
        cur_week = week[0]
        lessons = week[1]
        for lesson in lessons:
            cur_lesson = lesson[0]
            lectures = lesson[1]

            dir = os.path.join(path, cur_week, cur_lesson)
            if not os.path.exists(dir):
                mkdir_p(dir)

            for (lecnum, (lecture_url, lecture_name)) in enumerate(lectures):
                filename = os.path.join(dir,"%02d_%s.%s"%(lecnum+1, lecture_name, lecture_url[-3:]))
                if overwrite or not os.path.exists(filename):
                    print (filename)
                    print (lecture_url)
                    download_file(session, lecture_url, filename )
                else:
                    print ('%s already downloaded' % filename)



def parse_syllabus_icourse163(session, page):

    data = page.splitlines(True)

    vid_reg = b'contentId=([0-9]+);.+contentType=1;.+name=\"(.+)\";'
    doc_id_reg = b'contentId=([0-9]+);.+contentType=3;'
    lecture_reg = b'contentId=null.+name=\"(.+)\";.+releaseTime='
    week_reg = b'contentId=null.+lessons=.+name=\"(.+)\";.+releaseTime='

    geturl_url = 'http://www.icourse163.org/dwr/call/plaincall/CourseBean.getLessonUnitLearnVo.dwr'

    term = []
    lessons = []
    lectures = []
    cur_week = ''
    cur_lesson= ''

    for line in data:

        print ('.', end="")
        s1 = re.search(week_reg, line)
        if s1:
            if lectures:
                lessons.append((cur_lesson, lectures))
                lectures = []

            if lessons:
                term.append((cur_week, lessons))
                lessons = []
            cur_week = s1.group(1).decode('raw_unicode_escape')
            continue
        else:
            s2 = re.search(lecture_reg, line)
            if s2:
                if lectures:
                    lessons.append((cur_lesson, lectures))
                    lectures = []
                cur_lesson = s2.group(1).decode('raw_unicode_escape')
                continue
            else:
                # For video ID
                s3 = re.search(vid_reg, line)
                if s3:
                    lecture_name = s3.group(2).decode('raw_unicode_escape')
                    params =  {
                            'callCount':'1',
                            'scriptSessionId':'${scriptSessionId}100', #* , but arbitrarily
                            'c0-scriptName':'CourseBean',
                            'c0-methodName':'getLessonUnitLearnVo',
                            'c0-id':'0',
                            'c0-param0':'number:' + s3.group(1),
                            'c0-param1':'number:1',
                            'c0-param2':'number:0',
                            'c0-param3':'number:251189',
                            'batchId':'969403', #* , but arbitrarily
                            }
                    r = session.post(geturl_url, data = params, cookies = session.cookies)

                    # sd_url_reg = b'videoUrl:\"(.+)\"'
                    # hd_url_reg = b'videoHDUrl:\"(.+)\"'
                    # shd_url_reg = b'videoSHDUrl:\"(.+)\",'

                    # The regex here is not strict enough, should be improved further.
                    multi_resolution_reg = [b'videoSHDUrl:\"(.+)\",',b'videoHDUrl:\"(.+)\"',b'videoUrl:\"(.+)\"']

                    for reg in multi_resolution_reg:
                        s4 = re.search(reg, r.content)
                        if s4:
                            break
                    
                    lecture_url = s4.group(1)
                    lectures.append((lecture_url,lecture_name))
                    
                    continue

                #For pdf ID
                #s5 = re.search(doc_id_reg, line)
                #if s5:
                #    print ('      ' + s5.group(1) )

    lessons.append((cur_lesson, lectures))
    term.append((cur_week, lessons))

    return term


if __name__ == '__main__':
    main()