#! /usr/bin/python
#-*- coding: utf-8 -*-
import os,urllib2,json,codecs
from collections import deque
class WikiPage:
    def __init__(self,title,ns,id,redirect,text,category):
        self.title = title
        self.ns = ns
        self.id = id
        self.redirect = redirect
        self.text = text
        self.category = category

    def getTitle(self):
        return self.title



def getWikiCategory(title):#get all subcategories and pages by wiki api
    url_c = r'https://en.wikipedia.org/w/api.php?format=json&action=query&list=categorymembers&cmlimit=500&cmtitle='
    url_p = r'http://en.wikipedia.org/w/api.php?format=json&action=query&prop=revisions&rvprop=content&titles='
    #url = r'http://en.wikipedia.org/wiki/Category:Technology'
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent','Mozilla/5.0')]
    rs = ''
    q = deque([title])
    while len(q):
        title = q.popleft().strip().replace(' ','%20')
        if title.startswith('Category:'):
            try:
                rs = opener.open(url_c+title).read()
                js = json.loads(rs)
                for cm in js['query']['categorymembers']:
                    q.append(cm['title'])
            except:
                print 'Error'
                continue
        else:
            try:
                rs = opener.open(url_p+title).read()
                js = json.loads(rs)
                rs = js['query']['pages'].values()[0]['revisions'][0]['*']
            except:
                print 'Error'
                continue
        print title
        if rs is not '':
            title = title.replace('%20',' ').replace('/','|')
            f = codecs.open(r'../wikipedia/'+title.replace('%20',' '),encoding='utf-8',mode='w')
            f.write(rs)
            f.close()
    
def wikiDumpProcess(xmldump):
    title,ns,id,redirect,text,category = '','','','','',''
    page = WikiPage
    for line in open(xmldump):
        line = line.strip()
        if line == '<page>':
            #...
            return


if __name__ == "__main__":
    getWikiCategory('Category:Technology')
