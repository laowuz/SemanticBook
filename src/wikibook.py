#! /usr/bin/python
#-*- coding: utf-8 -*-
import json, urllib2, re, codecs

class Wikibook():
    def __init__(self,bookname,tocfile):
        self.bookname = bookname
        self.tocfile = tocfile
        self.ToC = []
        self.initToC()

    def __str__(self):
        return self.bookname

    def initToC(self):
        toc = open(self.tocfile).read().strip().split('\n')
        for line in toc:
            line = line.strip()
            if not line[0].isdigit():
                continue
            i = line.find(' ')
            section = line[:i]
            title = line[i+1:line.rfind(' ')]
            j = line.find(' . . . .')
            if j>=0:
                title = line[i+1:j]
            self.ToC.append((section,title))


    def link2Wiki(self):
        wiki_api = r'http://en.wikipedia.org/w/api.php?action=query&list=search&srlimit=1&format=json&srsearch='
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent','Mozilla/5.0')]
        fw = open(r'../test/PRML.wikibook','w')
        for sec,title in self.ToC:
            url = wiki_api+re.sub('\s+','%20',title)
            try:
                js = json.loads(opener.open(url).read())
                wiki_title = js['query']['search'][0]['title']
            except:
                wiki_title = ''
            fw.write(sec+' '+wiki_title.encode('utf-8')+'\n')
            print sec,title,len(title),':::',wiki_title,len(wiki_title)
        fw.close()





if __name__ == '__main__':
    wb = Wikibook('machine learning and pattern recognition',r'/home/zzw109/project/bookgen/test/PRML.toc')
    wb.link2Wiki()
