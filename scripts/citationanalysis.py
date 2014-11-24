#! /usr/bin/python
#-*- coding: utf-8 -*-
import re,os,random
from shutil import copy2
#import matplotlib.pyplot as plt

class Reference:
    def __init__(self,ref_str):
        self.ref_str = ref_str
        self.authors = []
        self.title = ""
        self.publisher = ""
        self.venue = ""
        self.proceeding = ""
        self.journal = ""
        self.date = ""
        self.year = ""
        self.vol = ""
        self.no = ""
        self.pp = ""
        self.parse()

    def parse(self):
        name = re.compile('[A-Z][\w’]{1,20},?\s([A-Z]\.){1,3}|([A-Z]\.){1,3}\s[\w’]{1,20}|[A-Z]\s[\wö]{1,10},?\s([A-Z]\.){1,3}|[A-Z][\w’]{1,20}\s[A-Z][\w’]{1,20}[,.]')
        #name1 = re.compile('[A-Z][\w’]{1,20}\s[A-Z][\w’]{1,20}[,.]')
        title = re.compile('[“"\']?([A-Za-z:,\r\n]{2,}\s?){3,}[”"\']?')
        proceedings = re.compile('Proceedings|Proc.|Conference|Conf.|Symposium|Workshop',re.I)
        journals = re.compile('Transactions|Trans. On|IEEE Tr.|IEEE J.|Journal|Int. J.',re.I)
        year = re.compile('1\d\d\d|200\d|201[0-3]')
        se = name.search(self.ref_str)
        end_author = -1
        while se is not None and (se.start()-end_author < 10 or se.start() < 10):
            self.authors.append(se.group())
            end_author = se.end()
            se = name.search(self.ref_str,end_author)
        ref_str = self.ref_str[max(0,end_author+1):]
        title_end = ref_str.find(',')
        self.title = ref_str[1:title_end].strip('“”')
        subs = re.split(',\s+',ref_str[title_end+1:].strip(',” '))
        for sub in subs:
            if re.search(proceedings,sub) is not None:
                self.proceeding = sub
                continue
            if re.search(journals,sub) is not None:
                self.journal = sub
                continue
            if sub.startswith('Vol.'):
                self.vol = sub
                continue
            if sub.startswith('no.'):
                self.no = sub
                continue
            if sub.startswith('pp.'):
                self.pp = sub
                continue
            if len(sub)>= 4 and re.search(year,sub) is not None:
                self.date = sub
                self.year = re.search(year,sub).group()
                continue
        self.venue = self.proceeding+self.journal
        if len(self.venue) == 0:
            self.venue = subs[0]

    def out(self):
        print 'Authors:',str(self.authors)
        print 'Title:',self.title
        print 'proceeding:',self.proceeding
        print 'journal:',self.journal
        print 'Venue:',self.venue
        print 'Year:',self.year

class References:
    def __init__(self,file):
        self.text = open(file).read().strip()
        self.ref_strs = self.text.split('\n\n')
        self.references = []
    def getItem(self,i):
        return self.references[i]
    def length(self):
        return len(self.ref_strs)
    def setRefs(self):
        self.references = [Reference(ref_str) for ref_str in self.ref_strs]
    def getAllRefs(self):
        return self.references

def clean2venue(infile,outfile):
    out = open(outfile,'w')
    p_err = re.compile('pages|vol\.|no.|http|University of|School of|Department of|\xc3',re.I)
    lines = open(infile).read().strip().split('\n')
    p = re.compile('Transactions|Trans\. On|IEEE Tr\.|IEEE J\.|Journal|Int\. J\.|Proceedings|Proc\.|Conference|Conf\.|Symposium|Workshop',re.I)
    for line in lines:
        venue = line.split('::: ')[0]
        if re.search('\d',venue) is not None:
            continue
        if len(venue)<5:
            continue
        if line.startswith('\'and') or line.startswith('\'University') or venue.endswith('University\''):
            continue
        if re.search(p_err,line) is not None:
            continue
        num = line.split('::: ')[1]
        if num.isdigit() and int(num) < 12:
            if re.search(p,venue) is None:
                continue
        if line[1:3]=='" ':
            line=line.replace('" ','')
        out.write(line+'\n')
    out.close()

def clean2institue(infile,outfile):
    base_dir = r'/home/zzw109/project/book/'
    venues = open(base_dir+'venue_dist.top.new2').read().strip().split('\n')[:2000]
    locations = open(base_dir+'venue_dist.location').read().strip().split('\n')[:153]
    out = open(outfile,'w')
    p_yes = re.compile('Institute|University|Laborator|Corporation|Lab|College|Center|Centre|Research|Office|Associat|Society|Agency|Company|Corp\.|Division|Organization',re.I)
    p_not = re.compile('\d|pages|volume|edition|paper|vol\.|no\.|http|\xc3|Transactions|Trans\.|IEEE|ACM|Journal|Int\. J\.|Proceedings|Proc\.|Conference|Conf\.|Symposium|Workshop|Department of|School of|Ph\.|Master|Press|Publisher|\'[\w][a-z0-9_\.]+\'',re.I)
    lines = open(infile).read().strip().split('\n')
    for line in lines:
        venue = line.split('::: ')[0]
        num = line.split('::: ')[1]
        if len(venue) < 5:
            continue
        if re.search(p_not,venue) is not None:
            continue
        if line in venues or line in locations:
            continue
        if num.isdigit() and int(num) < 10:
            if re.search(p_yes,venue) is None:
                continue
        if line[1:3] == '" ':
            line = line.replace('" ','')
        out.write(line+'\n')
    out.close()

def clean2title(infile,outfile):
    out = open(outfile,'w')
    p_err = re.compile('Phys\. Rev\.|Phys\. Lett\.|et al\.\'|([A-Z]\.\s){1,3}[A-Z][a-z]{1,}\'|[A-Z]\.-[A-Z]\.\s[A-Z][a-z]{1,}\'')
    lines = open(infile).read().strip().split('\n')
    p = re.compile('Transactions|Trans\. On|IEEE Tr\.|IEEE J\.|Journal|Int\. J\.|Proceedings|Proc\.|Conference|Conf\.|Symposium|Workshop',re.I)
    c = 0
    for line in lines:
        c = c + 1
        words = line.split('::: ')[0].strip('\'').split()
        if c<1050:
            out.write(line+'\n')
            continue
        if len(words)<4:
            continue
        if re.search(p_err,line) is not None:
            continue
        subs = re.split('\.\s',line)
        if len(subs)>2 and len(subs[1].split())>1:
            line = '\''+'. '.join(subs[1:])
        out.write(line+'\n')
    out.close()

def clean2author(infile,outfile):
    out = open(outfile,'w')
    p_err = re.compile('^[A-Z]\.?\s[A-Z]\.?$|and|AND|the|THE|The|:::')
    lines = open(infile).read().strip().split('\n')
    for line in lines:
        subs = line.split('::: ')
        if len(subs)>2:
            continue
        author = line.split('::: ')[0].strip('\'')
        if re.search(p_err,author) is not None:
            continue
        out.write(line+'\n')
    out.close()

def rank_venue(infile,outfile):
    lines = open(infile).read().strip().split('\n')[:1000]
    venues = [line.split('::: ')[0].strip('\'') for line in lines]
    #venues = ['Cambridge University Press','Wiley']
    v_dic = {}
    for v in venues:
        v_dic[v] = 0
    ref_dir = r'/home/zzw109/project/book/references/'
    for f in os.listdir(ref_dir):
        print f
        refs = References(ref_dir+f)
        for v in venues:
            #print v
            p = re.compile(v.replace('(','\(').replace(')','\)'))
            num=len(re.findall(p,refs.text))
            if num > refs.length():
                num = refs.length()/2
                print v,'Impossible!!!!!!!!!!!!!!!'
                #raw_input()
            v_dic[v] = v_dic[v] + num
    sort_v = sorted(v_dic.items(), key=lambda s:s[1], reverse=True)
    open(outfile,'w').write(str(sort_v).strip('[()]').replace('), (','\n').replace(',',':::'))

def rank_institute(infile,outfile):
    lines = open(infile).read().strip().split('\n')[:1000]
    venues = [line.split('::: ')[0].strip('\'') for line in lines]
    v_dic = {}
    for v in venues:
        v_dic[v] = 0
    ref_dir = r'/home/zzw109/project/book/references/'
    for f in os.listdir(ref_dir):
        print f
        refs = References(ref_dir+f)
        for v in v_dic:
            #print v
            p = re.compile(v.replace('(','\(').replace(')','\)'))
            num=len(re.findall(p,refs.text))
            if num > refs.length():
                num = refs.length()
                print v,'Impossible!!!!!!!!!!!!!!!'
                #raw_input()
            v_dic[v] = v_dic[v] + num
    sort_v = sorted(v_dic.items(), key=lambda s:s[1], reverse=True)
    open(outfile,'w').write(str(sort_v).strip('[()]').replace('), (','\n').replace(',',':::'))

def rank_citation(infile,outfile):
    lines = open(infile).readlines()[:1000]
    venues = [line.split('::: ')[0].strip('\'') for line in lines]
    v_dic = {}
    for v in venues:
        v_dic[v] = 0
    ref_dir = r'/home/zzw109/project/book/references/'
    for f in os.listdir(ref_dir):
        print f
        refs = References(ref_dir+f)
        for v in venues:
            #print v
            v1 = v.replace('+','\+').replace('[','\[').replace(']','\[').replace('(','\(').replace(')','\)')
            p = re.compile(v1)
            num=len(re.findall(p,refs.text))
            if num > refs.length():
                num = refs.length()
                print v,'Impossible!!!!!!!!!!!!!!!'
                #raw_input()
            v_dic[v] = v_dic[v] + num
    sort_v = sorted(v_dic.items(), key=lambda s:s[1], reverse=True)
    open(outfile,'w').write(str(sort_v).strip('[()]').replace('), (','\n').replace(',',':::'))

def rank_venue2(infile,outfile):#rank by #books
    lines = open(infile).readlines()
    #venues = [line.split('::: ')[0].strip('\'') for line in lines]
    venues = ['Neural Networks for Pattern Recognition. Oxford University Press','Neural Networks for Pattern Recognition']
    num_book_dic = {}
    num_citing_dic = {}
    for v in venues:
        num_book_dic[v] = 0
        num_citing_dic[v] = 0
    ref_dir = r'/home/zzw109/project/book/references/'
    for f in os.listdir(ref_dir):
        print f
        refs = References(ref_dir+f)
        for v in venues:
            #print v
            v1 = v.replace('+','\+').replace('[','\[').replace(']','\[').replace('(','\(').replace(')','\)')
            #v1 = '[\.,]\s{1,3}'+v+'[\.:\s]\d?'
            p = re.compile(v1)
            num=len(re.findall(p,refs.text))
            if num > refs.length():
                num = refs.length()
            #    print v,'Impossible!!!!!!!!!!!!!!!'
                #raw_input()
            num_citing_dic[v] = num_citing_dic[v] + num
            if num > 0:
                num_book_dic[v] = num_book_dic[v] + 1
    sort_v1 = sorted(num_book_dic.items(), key=lambda s:s[1], reverse=True)
    sort_v2 = sorted(num_citing_dic.items(), key=lambda s:s[1], reverse=True)
    open(outfile+'.bybooknum','w').write(str(sort_v1).strip('[()]').replace('), (','\n').replace(',',':::'))
    open(outfile+'.bycitingnum','w').write(str(sort_v2).strip('[()]').replace('), (','\n').replace(',',':::'))

def rank_institute2(infile,outfile):#rank by #books
    lines = open(infile).readlines()
    venues = [line.split('::: ')[0].strip('\'') for line in lines]
    num_book_dic = {}
    #num_citing_dic = {}
    for v in venues:
        num_book_dic[v] = 0
        #num_citing_dic[v] = 0
    ref_dir = r'/home/zzw109/project/book/references/'
    for f in os.listdir(ref_dir):
        print f
        refs = References(ref_dir+f)
        for v in venues:
            #print v
            v1 = v.replace('+','\+').replace('[','\[').replace(']','\[').replace('(','\(').replace(')','\)')
            p = re.compile(v1)
            num=len(re.findall(p,refs.text))
            #if num > refs.length():
            #    num = refs.length()
            #    print v,'Impossible!!!!!!!!!!!!!!!'
                #raw_input()
            #num_citing_dic[v] = num_citing_dic[v] + num
            if num > 0:
                num_book_dic[v] = num_book_dic[v] + 1
    sort_v1 = sorted(num_book_dic.items(), key=lambda s:s[1], reverse=True)
    #sort_v2 = sorted(num_citing_dic.items(), key=lambda s:s[1], reverse=True)
    open(outfile+'.bybooknum','w').write(str(sort_v1).strip('[()]').replace('), (','\n').replace(',',':::'))
    #open(outfile+'.bycitingnum','w').write(str(sort_v2).strip('[()]').replace('), (','\n').replace(',',':::'))


def rank_citation2(infile,outfile):#rank by #books
    lines = open(infile).readlines()
    venues = [line.split('::: ')[0].strip('\'') for line in lines]
    num_book_dic = {}
    num_citing_dic = {}
    for v in venues:
        num_book_dic[v] = 0
        num_citing_dic[v] = 0
    ref_dir = r'/home/zzw109/project/book/references/'
    for f in os.listdir(ref_dir):
        print f
        refs = References(ref_dir+f)
        for v in num_book_dic:
            #print v
            v1 = v.replace('+','\+').replace('[','\[').replace(']','\[').replace('(','\(').replace(')','\)')
            p = re.compile(v1)
            num=len(re.findall(p,refs.text))
            if num > refs.length():
                num = refs.length()
                print v,'Impossible!!!!!!!!!!!!!!!'
                #raw_input()
            num_citing_dic[v] = num_citing_dic[v] + num
            if num > 0:
                num_book_dic[v] = num_book_dic[v] + 1
    sort_v1 = sorted(num_book_dic.items(), key=lambda s:s[1], reverse=True)
    sort_v2 = sorted(num_citing_dic.items(), key=lambda s:s[1], reverse=True)
    open(outfile+'.bybooknum1','w').write(str(sort_v1).strip('[()]').replace('), (','\n').replace(',',':::'))
    open(outfile+'.bycitingnum1','w').write(str(sort_v2).strip('[()]').replace('), (','\n').replace(',',':::'))

def rank_author2(infile,outfile):#rank by #books and #citings
    lines = open(infile).readlines()[:3000]
    venues = [line.split('::: ')[0].strip('\'') for line in lines]
    num_book_dic = {}
    num_citing_dic = {}
    for v in venues:
        num_book_dic[v] = 0
        num_citing_dic[v] = 0
    ref_dir = r'/home/zzw109/project/book/references/'
    for f in os.listdir(ref_dir):
        print f
        refs = References(ref_dir+f)
        for v in venues:
            v1 = v.replace('.','\.')
            p = re.compile(v1)
            num=len(re.findall(p,refs.text))
            if num > refs.length():
                num = refs.length()
                print v,'Impossible!!!!!!!!!!!!!!!'
                #raw_input()
            num_citing_dic[v] = num_citing_dic[v] + num
            if num > 0:
                num_book_dic[v] = num_book_dic[v] + 1
    sort_v1 = sorted(num_book_dic.items(), key=lambda s:s[1], reverse=True)
    sort_v2 = sorted(num_citing_dic.items(), key=lambda s:s[1], reverse=True)
    open(outfile+'.bybooknum','w').write(str(sort_v1).strip('[()]').replace('), (','\n').replace(',',':::'))
    open(outfile+'.bycitingnum','w').write(str(sort_v2).strip('[()]').replace('), (','\n').replace(',',':::'))

def getTotalNumberofCitations():
    ref_dir = r'/home/zzw109/project/book/references/'
    base_dir = r'/home/zzw109/project/book/'
    num1 = sum([int(i) for i in open(base_dir+r'degree_dist.txt').read().strip().split('\n')])
    num2 = 0
    for f in os.listdir(ref_dir):
        refs = References(ref_dir+f)
        num2 = num2 + refs.length()
    print num1, num2

def findBooksbyCitationNum(num):
    ref_dir = r'/home/zzw109/project/book/references/'
    base_dir = r'/home/zzw109/project/book/'
    books = []
    for f in os.listdir(ref_dir):
        refs = References(ref_dir+f)
        if refs.length()>=num:
            books.append(f)
    print books


def random_sample_books():
    ref_dir = r'/home/zzw109/project/book/references/'
    sample_dir = r'/home/zzw109/project/book/goodbooks/sample/'
    pdf_dir = r'/home/zzw109/project/book/pdfs/'
    book_list = os.listdir(ref_dir)
    samples = random.sample(book_list,100)
    for samp in samples:
        pdf = samp.replace('txt','pdf')
        copy2(pdf_dir+pdf,sample_dir+pdf)
    print 'Done!'

def getISICSBooks():
    base_dir = r'/home/zzw109/project/book/'
    ISIhtm = 'ISIBookCitationIndex.htm'

def getAllID():
    base_dir = r'/home/zzw109/project/book/'
    f=open(base_dir+'IDofBookwithBibliography.txt','w')
    for txt in os.listdir(base_dir+'references'):
        f.write(txt[:-4]+'\n')
    f.close()
if __name__ == "__main__":
    findBooksbyCitationNum(1000)
    #getTotalNumberofCitations()
    #random_sample_books()
    #ref_dir = r'/home/zzw109/project/book/references/'
    #base_dir = r'/home/zzw109/project/book/'
    #rank_citation2(base_dir+r'title_dist.all.title.top1000',base_dir+r'title.rank')
    #rank_venue2(base_dir+r'venue_dist.top.new4',base_dir+r'Neural.test')
    #rank_institute2(base_dir+r'venue_dist.all.institue.top1000',base_dir+'institute.rank')
    #rank_author2(base_dir+r'author_dist.new2',base_dir+'author.rank')
    
    #clean2venue(base_dir+'venue_dist.top.new3',base_dir+'venue_dist.top.new4')
    #clean2institute(base_dir+'venue_dist.institue.new',base_dir+'venue_dist.institue.new1')
    #clean2title(base_dir+'title_dist.new1',base_dir+'title_dist.new2')
    #clean2author(base_dir+'author_dist.new1',base_dir+'author_dist.new2')
    #while 1:
      #  print 'OK'
     #   continue

    #file = '10.1.1.99.9919.txt'
    #refs = References(ref_dir+file)
    #for ref in refs.getAllRefs():
    #    ref.out()

    #print refs.length()
    #while 1:
    #    continue

    #degree_dist = [0]*6000
    if 0:
        dic_venue = {}
        dic_author = {}
        dic_year = {}
        dic_title = {}
        c = 0
        for f in os.listdir(ref_dir):
            c = c + 1
            refs = References(ref_dir+f)
            refs.setRefs()
            print f,refs.length(),c
            #degree_dist[refs.length()] = degree_dist[refs.length()] + 1
            #if refs.length()>100 or refs.length()<80:
            #    continue
            for ref in refs.getAllRefs():
                if len(re.split('[a-z]{2}\.\s',ref.ref_str)) > 5:
                    continue
                #venue = ref.venue
                #authors = ref.authors
                title = ref.title
                if len(title.split())>30:
                    continue
                if dic_title.has_key(title):
                    dic_title[title] = dic_title[title] + 1
                else:
                    dic_title[title] = 1
                if 0:
                    if len(authors)>0:
                        for a in authors:
                            if dic_author.has_key(a):
                                dic_author[a] = dic_author[a] + 1
                            else:
                                dic_author[a] = 1

                    year = ref.year
                    if year.isdigit() and len(year) == 4:
                        if dic_year.has_key(year):
                            dic_year[year] = dic_year[year] + 1
                        else:
                            dic_year[year] = 1
                    continue
                    if len(venue.split())>10:
                        #venue = ' '.join(venue.split()[:20])
                        continue
                    if dic_venue.has_key(venue):
                        dic_venue[venue] = dic_venue[venue] + 1
                    else:
                        dic_venue[venue] = 1
        #print degree_dist
        #print dic_venue
        #open(base_dir+os.sep+'authors_dist.txt','w').write(str(degree_dist).strip('[]').replace(', ','\n'))
        #list_tit = [(k,v) for (k,v) in dic_title.items()]
        #sort_tit = sorted(list_tit, key=lambda x:x[1], reverse=True)
        #open(base_dir+'title_dist.txt','w').write(str(sort_tit).strip('[()]').replace('), (','\n').replace(',',':::'))
        


    if 0:
        list_author = [(k,v) for (k,v) in dic_author.items()]
        list_year = [(k,v) for (k,v) in dic_year.items()]
        sort_list_author = sorted(list_author, key=lambda s:s[1], reverse=True)
        sort_list_year = sorted(list_year, key=lambda s:s[1], reverse=True)
        open(base_dir+os.sep+'author_dist.txt','w').write(str(sort_list_author).strip('[()]').replace('), (','\n').replace(',',':::'))
        open(base_dir+os.sep+'year_dist.txt','w').write(str(sort_list_year).strip('[()]').replace('), (','\n').replace(',',':::'))
        #open(base_dir+os.sep+'venue_dist.txt','w').write(str(sort_list).strip('[()]').replace('), (','\n').replace(',',':::'))

