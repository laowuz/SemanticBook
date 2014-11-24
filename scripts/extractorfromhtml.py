#! /usr/bin/python
#-*- coding: utf-8 -*-
#from bs4 import BeautifulSoup
import re,sys,os

class HtmlExtractor:
    def __init__(self, html_file, xml_file, author_dic):
        self.text = open(html_file).read()
        self.xml_file = xml_file
        self.author_dic = author_dic
        self.title = ""
        self.ISBN = []
        self.authors = []
        self.pages = re.findall('<a name="\d{1,2}">Page \d{1,2}</a>',self.text)
        self.pages_index = [self.text.find(page) for page in self.pages]
        self.contents_page = self.getContents_Page() if len(self.pages)>10 else None
        self.preface_page = self.getPreface_Page() if len(self.pages)>10 else None
        self.copyright = ""

    def getPreface_Page(self):
        preface_search = re.search(re.compile('Preface.*?<a name="\d{1,2}">Page (\d{1,2})</a>',re.I|re.S),self.text[:self.pages_index[len(self.pages_index)-1]])
        self.preface_page = 10000
        if preface_search is not None:
            self.preface_page = int(preface_search.group(1))-1
        return self.preface_page

    def getCopyright(self):
        srh = re.search('copyright\s?\d{4}-\d{4}.*[\.\n]|copyright\s?©?\s?\d{4}.*?[\.\n]|©\s{,3}(copyright)?\s{,3}\d{4}.*?[\.\n]',self.text[self.pages_index[0]:self.pages_index[8]], re.I)
        if srh is not None:
            self.copyright = srh.group()
        return self.copyright

    def getContents_Page(self):
        contents_search = re.search(re.compile('(contents|table of contents).*?<a name="\d{1,2}">Page (\d{1,2})</a>',re.I|re.S),self.text[:self.pages_index[len(self.pages_index)-1]])
        self.contents_page = 10000
        if contents_search is not None:
            self.contents_page = int(contents_search.group(2))-1
        return self.contents_page

    def extractISBN(self):
        text = self.text[self.pages_index[0]:self.pages_index[8]]
        text = text.replace('–','-')
        p_isbn10 = re.compile('i\s?s\s?b\s?n(10|[\s-]10)?[:-]?[\s]{0,5}([\dx-]{13})',re.I)
        p_isbn13 = re.compile('i\s?s\s?b\s?n(13|[\s-]13)?[:-]?[\s]{0,5}([\dx-]{17})',re.I)
        r1 = re.search(p_isbn10,text)
        r2 = re.search(p_isbn13,text)
        if r2 is not None:
            self.ISBN.append(r2.group(2))
        if r1 is not None:
            if len(self.ISBN) == 0:
                self.ISBN.append(r1.group(2))
            elif self.ISBN[0].startswith(r1.group(2)):
                return self.ISBN
            else:
                self.ISBN.append(r1.group(2))
        return self.ISBN

    def extractTitle_Authors(self):
        titlecands = []
        authorcands = []
        end_page = min(self.contents_page-1,self.preface_page-1,10)
        print 'scan first %d pages' %end_page
        #scan all pages in front of table of contents
        for i in range(end_page):
            page_i = self.text[self.pages_index[i]:self.pages_index[i+1]]
            candidates = re.findall('<span style=".*?font-size:(\d{1,2})px">(.*?)(<br>)?</span>',page_i,re.S)
            #print 'candidates',candidates
            if len(candidates) == 0:
                continue
            modules = []
            modules_authors = [] #possible author modules(near title)
            max_size = 0
            j,max_j = 0,0
            for cand in candidates:
                fontsize,txt = int(cand[0]),cand[1]
                #find the max font size
                if fontsize > max_size and re.search('\S',txt) is not None:
                    max_size = fontsize
                    max_j = j
                j = j + 1
                words = []
                f1 = txt.find('</span>')
                if f1 != -1:#with sub-spans
                    words.append(txt[:f1])
                    #merge the sub-spans
                    words.extend(re.findall('<span.*?>(.*?)</span>',txt))
                    if txt.rfind('>') != -1:
                        words.append(txt[txt.rfind('>')+1:])
                    if len(words)>1:
                        txt = ''.join(words)
                else:#no sub-spans but mutiple lines
                    txt = txt.replace('\n<br>','  ')
                modules.append((fontsize,txt.strip()))
            title = modules[max_j][1]
            if title.endswith(':') and max_j < len(modules)-1:
                title = title + modules[max_j+1][1]
                if max_j < len(modules)-1 and modules[max_j+1][0] == modules[max_j][0]:
                    title = title + ' ' + modules[max_j+1][1]
            #print 'modules',modules
            titlecands.append((modules[max_j][0],title))
            if int(modules[max_j][0])<10:
                continue
            #find authors
            if len(modules) < 2:
                continue
            if max_j > 0:
                modules_authors.append(modules[max_j-1])
            if max_j < len(modules)-1:
                modules_authors.append(modules[max_j+1])
            if max_j < len(modules)-2:
                modules_authors.append(modules[max_j+2])
            if modules[0] not in modules_authors:
                modules_authors.append(modules[0])
            if modules[-1] not in modules_authors:
                modules_authors.append(modules[-1])
            #print 'modules_authors:',modules_authors
            for m in modules_authors:
                txt = m[1]
                if txt.startswith('By') or txt.startswith('by') or txt.startswith('Edited by:'):
                    authors = re.split('[,;]?\s*and\s*|\s{2,}|[;,]\s*',txt.strip('By|by|Edited by:').strip())
                    for a in authors:
                        for w in a.split():
                            if w in self.author_dic and a not in authorcands:
                                authorcands.append(a)
                count = 0
                words = re.split('[,;]?\s*and\s*|\s{2,}|[;,]\s*',txt)
                for w in words:
                    ws = w.split()
                    if len(ws) <2 or len(ws)>4:
                        continue
                    c = 0
                    for it in ws:
                        if it in self.author_dic or it.capitalize() in self.author_dic:
                            c = c+1
                    if c > len(ws)/2 and w not in authorcands:
                        authorcands.append(w)
                    else:
                        break
        max_size,max_title = 0,""
        title_dic = {}
        for t in titlecands:
            if int(t[0])>max_size:
                max_size,max_title = int(t[0]),t[1]
            if t[1].title() not in title_dic.keys():
                title_dic[t[1].title()] = 1
            else:
                title_dic[t[1].title()] = title_dic[t[1].title()] + 1
        #print 'max: ',max_size,max_title
        most_times, most_title = 0, ""
        for t in title_dic.keys():
            if title_dic[t] > most_times:
                most_times,most_title = title_dic[t],t
        if most_times > 1:
            self.title = most_title
        else:
            self.title = max_title
        self.authors = authorcands
        #print 'titlecands:',titlecands
        return self.title,self.authors

if __name__ == "__main__":
    if 0:
        base_dir = r'/home/zzw109/project/book'
        author_dic = open(base_dir+os.sep+'authornames.dic').read().strip().split()
        html_file = base_dir+os.sep+'goodbooks/books/'+sys.argv[1]
        #html_file = r'../goodbooks/books/10.1.1.115.1881.pdf.html'
        kb = HtmlExtractor(html_file,'',author_dic)
        isbn=kb.extractISBN()
        copyright = kb.getCopyright()
        title,authors = kb.extractTitle_Authors()
        print 'isbn:',isbn,'','copyright:',copyright,'title:',title,'author:',authors

    while 0:
        continue

    base_dir = r'/home/zzw109/project/book'
    out = open(base_dir+os.sep+'isbn.html.out','w')
    author_dic = open(base_dir+os.sep+'authornames.dic').read().strip().split()
    #in_dir = base_dir+os.sep+'goodbooks/books'
    in_dir = base_dir+os.sep+'html'
    for f in os.listdir(in_dir):
        if f.endswith('html') is not True:
            continue
        print f
        html_f = in_dir + os.sep + f
        kb = HtmlExtractor(html_f,'',author_dic)
        if len(kb.pages_index) < 20:
            continue
        #isbn,copyright = kb.extractISBN(), kb.getCopyright()
        #title,authors = kb.extractTitle_Authors()
        isbn = kb.extractISBN()
        print 'ISBN:',isbn
        if len(isbn)==0:
            continue
        to_write = f[:-9]+':'+isbn[0]+'\n'
        #print 'title:',title
        #to_write = f[:-9]+'=>ISBN:'+str(isbn)+'; Copyright:'+str(copyright)+'; Title:'+title+'; Authors:'+str(authors)+'\n\n'
        out.write(to_write)
    out.close()

    if False:
        html_file = base_dir+os.sep+'goodbooks/books/'+sys.argv[1]
        #html_file = r'../goodbooks/books/10.1.1.115.1881.pdf.html'
        kb = HtmlExtractor(html_file,'',author_dic)
        isbn=kb.extractISBN()
        copyright = kb.getCopyright()
        title,authors = kb.extractTitle_Authors()
        print 'isbn:',isbn,'','copyright:',copyright,'title:',title,'author:',authors


