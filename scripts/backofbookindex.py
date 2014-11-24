#! /user/bin/python
#-*- coding: utf-8 -*-
import os,re,random,time,subprocess
import urllib2
from extractor import BookDoc
from ToCdetection import ToC_detection

class IndexWord:
    def __init__(self,word,subentry,see,seealso,locator):
        self.word = word
        self.subentry = subentry
        self.see = see
        self.seealso = seealso
        self.locator = locator
    
    def addSubentry(self,w):
        if w not in self.subentry:
            self.subentry.append(w)

    def addSeealso(self,w):
        if w not in self.seealso:
            self.seealso.append(w)

    def addSee(self,w):
        if w not in self.see:
            self.see.append(w)

    def addLocator(self,w):
        if w not in self.locator:
            self.locator.append(w)

    def toString(self):
        return str(self.word)+str(self.subentry)+str(self.see)+str(self.seealso)+str(self.locator)


class BookIndex:
    def __init__(self,book,index_file):
        self.filename = book.file_name
        self.filepath = book.file_path
        self.text = book.text
        self.lines = book.lines
        self.indextext = open(index_file).read().strip()
        self.indexwords = {}
        self.words = []
        self.toc = ToC_detection(self.filepath)
    
    def autoIndexGen(self):
        toc,toc_begin,toc_end = self.toc
        stopwords = []
        #get keywords from Contents

        #for every paragraph, find the most informative keywords


    def startswithSubentryPrefix(self,s):
        prefixs = ['see ','as ','in ','and ','of ','on ','by ','a ','an ','from ','vs. ','at ','with ','through ']
        for p in prefixs:
            if s.startswith(p):
                return True
        return False
    
    def indexParse(self):
        indexlines = re.split('\n+',self.indextext)
        p_index = ['index','Index','INDEX']
        sample_lines = [indexlines[i] for i in random.sample(xrange(len(indexlines)/3),20)]
        i = 1
        while i < len(indexlines)-1:
            line = indexlines[i]
            last_line = indexlines[i-1]
            next_line = indexlines[i+1]
            if len(line) == 1 and line.isalpha():#single letter A, B, C, ...
                i = i + 1
                continue
            if len(line)>10:
                if line[-1] in [',','-'] or line[-3:]=='–' or (len(line)>30 and line[-1].isalpha() and next_line.startswith('and ')):#join the next line
                    line = line + next_line
            if len(last_line)>10:
                if last_line[-1] in [',','-'] or last_line[-3:]=='–':
                    i = i + 1
                    continue
            if i > 20 and line.isdigit() and last_line[-1].isdigit():#page number
                i = i + 1
                continue
            #if len(line.split())==1:#only one word
            #    #to be done
            #    #....
            #    i = i + 1
            #    continue
            words = re.split(',\s*',line.strip())
            #print i,line,words
            len_words = len(words)
            if (len_words <= 2 and words[0] in p_index) or line.isdigit():#index or page number
                i = i + 1
                continue
            word = words[0]
            locator,subentries,see,seealso = [],[],[],[]
            f = word.rfind(' ')
            if 0<f<len(word)-1:
                if word[f+1].isdigit():
                    locator.append(word[f+1:])
                    word = word[:f]
            for j in range(1,len(words)):
                w = words[j]
                if w[-1].isdigit():
                    locator.append(w)
                    continue
                if w in ['see','See'] and j+1<len(words):
                    if words[j+1] == 'also':
                        if j+2<len(words):
                            for wd in words[j+2:]:
                                seealso.append(wd)
                    else:
                        for wd in words[j+1:]:
                            see.append(wd)
            #print word,locator,subentries,see,seealso
            indexword = IndexWord(word,subentries,see,seealso,locator)
            self.indexwords[word] = indexword
            self.words.append(word)
            i = i + 1
            #time.sleep(1)
        prefix = 'a'
        start = 0
        for j in range(len(self.words)):
            if self.words[j][0] == prefix:
                start = j
                break
        k = -1
        for j in range(start,len(self.words)-2):
            if j < k:
                continue
            w = self.words[j]
            w_l = w.lower()
            if self.startswithSubentryPrefix(w_l):
                continue
            k = j + 1
            w1 = self.words[k]
            w2 = self.words[k+1]
            w1_l = w1.lower()
            w2_l = w2.lower()
            if len(w_l)>3 and len(w1_l)>3 and w_l[:3]==w1_l[:3]:
                continue
            print j,k,w,':',w1,':',w2
            #time.sleep(2)
            while self.startswithSubentryPrefix(w1_l) or (w1_l<w2_l and (w1_l<w_l or ord(w1_l[0])-ord(w_l[0])>1) or ord(w2_l[0])-ord(w_l[0])>1):
                if self.startswithSubentryPrefix(w1_l):
                    if w1_l.startswith('see also'):
                        self.indexwords[w].addSeealso(w1[9:])
                    elif w1_l.startswith('see'):
                        self.indexwords[w].addSee(w1[4:])
                    else:
                        self.indexwords[w].addSubentry(w1)
                else:
                    self.indexwords[w].addSubentry(w1)
                    self.indexwords[w].addSubentry(w2)
                k = k + 1
                if k > len(self.words)-2:
                    break
                w1,w2 = self.words[k],self.words[k+1]
                w1_l,w2_l = w1.lower(),w2.lower()
            if not self.startswithSubentryPrefix(self.words[k-1]) and k>j+1:
                k = k + 1
        out = open(r'/home/zzw109/Desktop/out.txt','w')
        for w in self.words:
            out.write(self.indexwords[w].toString()+'\n')
        #print self.indexwords.keys()
  

def dictGen():
    home_dir = r'/home/zzw109/project/book'
    home_dir1 = r'/home/zzw109/project/bookgen'
    books = open(home_dir+os.sep+'numofpages/101to...txt').read().strip().split('\n')
    book_txt = [book.split()[0].replace('pdf','txt') for book in books]
    txt_dir = r'/home/zzw109/project/book/allbookstxt'
    stopwords = open(home_dir1+os.sep+'StopWords').read().strip().split()
    word_dic = {}
    doc_dic = {}
    for id in book_txt[:1000]:
        print id
        try:
            f = open(txt_dir+os.sep+id)
            text = f.read().strip()
            paras = re.split('\n+',text)
            id = id[7:-4]
            for para in paras:
                para = para.strip().strip('.?!')
                words = re.split('\s+',para)
                grams2,grams3 = [],[]
                N = len(words)
                if N > 1:
                    grams2 = [words[i]+' '+words[i+1] for i in range(N-1)]
                if N > 2:
                    grams3 = [words[i]+' '+words[i+1]+' '+words[i+2] for i in range(N-2)]
                words = words + grams2 + grams3
                for w in words:
                    w = w.lower()
                    if w.isdigit() or w in stopwords:
                        continue
                    if w not in word_dic:
                        word_dic[w] = {}
                        word_dic[w][id] = 1
                    else:
                        if id not in word_dic[w]:
                            word_dic[w][id] = 1
                        else:
                            word_dic[w][id] = word_dic[w][id] + 1
            f.close()
        except IOError:
            print 'file error'
            continue
    print 'Begin to sort...'
    sorted_dic = sorted(word_dic.items(),key=lambda x: len(x[1]), reverse=True)
    fopen = open(home_dir1+os.sep+'dict.txt','w')
    for it in sorted_dic[:3000]:
        fopen.write(str(it[0])+':'+str(len(it[1]))+'\n')
    fopen.close()

def tagAllBook():
    home_dir = r'/home/zzw109/project/book'
    books = open(home_dir+os.sep+'numofpages/101to...txt').read().strip().split('\n')
    book_txt = [book.split()[0].replace('pdf','txt') for book in books]
    txt_dir = r'/home/zzw109/project/book/allbookstxt'
    tag_dir = r'/home/zzw109/download/stanford-postagger-full-2012-07-09'
    tagger = tag_dir+r'/stanford-postagger.sh'
    model = tag_dir+r'/models/wsj-0-18-left3words-distsim.tagger'
    out_dir = r'/home/zzw109/project/bookgen/tagallbooktxt'
    for txt in book_txt[:3]:
        in_file = txt_dir+os.sep+txt
        out_file = out_dir+os.sep+txt
        subprocess.call([tagger,model,in_file,'>',out_file])

def getGoogleContext(query,api=True):
    query = re.sub('\s+','+',query.strip())
    url = ''
    if api is True:
        url = r'https://ajax.googleapis.com/ajax/services/search/web?v=1.0&rsz=8&q='+query
    else:
        url = r'http://www.google.com/search?q='+query
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent','Mozilla/5.0')]
    try:
        f = opener.open(url)
        rs = f.read()
    except HTTPError:
        print 'HTTPError'
        return
    if api is True:
        js = json.loads(rs)

    else:
        #parse the html

def getSimilarity(w1,w2):
#calculate different relatedness of two words using three knoweldge base, Citeseer, Wikipedia, Google


if __name__ == "__main__":
        #dictGen()
        home_dir = r'/home/zzw109/project/book'
        books = open(home_dir+os.sep+'numofpages/101to...txt').read().strip().split('\n')
        book_txt = [book.split()[0].replace('pdf','txt') for book in books]
        txt_dir = r'/home/zzw109/project/book/allbookstxt'
        txt_dir1 = r'/home/zzw109/project/book/goodbooks/books'
        xml_dir = r'/home/zzw109/project/book/xml'
        ref_dir = home_dir + os.sep + 'references'
        index_dir = home_dir + os.sep + 'index'
        txt = '10.1.1.139.8180.txt'
        txt1= r'Pattern Recognition and Machine Learning.txt'
        bk = BookDoc(txt1, txt_dir1, xml_dir, ref_dir)
        bi = BookIndex(bk,index_dir+os.sep+txt)
        #bi.autoIndexGen()
        #bi.indexParse()
    
