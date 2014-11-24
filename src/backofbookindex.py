#! /user/bin/python
#-*- coding: utf-8 -*-
import os,re,random,time,subprocess,time
import urllib2,codecs,json
from extractor import BookDoc
from ToCdetection import ToC_detection
import networkx as nx
import Stemmer
from sets import Set
from math import log
from nltk import pos_tag
from nltk import word_tokenize

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
  

def dictGen():#generate the tfidf info of all words in books
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

def tagAllBook():# POS tag all books 
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

def genLDATrainingData(txt=r'../PRML2LDA.txt'):
    t = open(txt).read()
    docs = re.split('[$]{8,}',t)
    out = str(len(docs))+'\n'
    stopwords = open(r'../StopWords').read().strip().split()
    print out
    for doc in docs:
        doc = re.sub('-\n+','',doc)
        doc = re.sub('\n+',' ',doc)
        doc1 = ''
        for w in doc.split():
            if w.lower() in stopwords or w.isdigit() or len(w)<2 or re.search('[^a-zA-Z0-9_-]',w) is not None:
                continue
            if len(w)==2 and w[0].isalpha() and w[1].isdigit():
                continue
            doc1 = doc1 + w + ' '
        out = out + doc1 + '\n'
    open(r'../PRML2LDA.data','w').write(out)

def getQueryResults(query_list,knowledgebase):
    limit = 10
    google_api = 'https://ajax.googleapis.com/ajax/services/search/web?v=1.0&rsz=8&userip=130.203.154.184&q='
    wiki_api = 'http://en.wikipedia.org/w/api.php?action=query&list=search&srlimit='+str(limit)+r'&srprop=snippet&format=json&srsearch='
    wiki_api2 = 'http://en.wikipedia.org/w/api.php?action=query&list=search&srlimit='+str(limit)+r'&srprop=snippet|titlesnippet|sectionsnippet&format=json&srsearch='
    query_results = {}
    url = ''
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent','Mozilla/5.0')]
    kb = knowledgebase.lower()
    for q in query_list:
        print q
        query = re.sub('\s+','%20',q.strip())
        if kb is 'google':
            url = google_api+query
        elif kb.startswith('wiki'):
            url = wiki_api+query
        else:
            print 'please specify the right knowledgebase'
            return None
        try:
            js = json.loads(opener.open(url).read())
        except:
            print 'Error'
            query_results[q]=[]
            continue
        if kb is 'google':
            rs = js['responseData']['results']
            query_results[q]= [r['content'] for r in rs]
        if kb.startswith('wiki'):
            try:
                rs = js['query']['search']
                query_results[q]=[re.sub('<.*?>','',r['snippet']) for r in rs]
                open(r'../query/'+q,'w').write('\n\n'.join(query_results[q]))
            except:
                print 'Error'
                query_results[q]=[]
                continue
    return query_results

def getKScore(content,query,knowledgebase):
    limit = 10
    google_api = 'https://ajax.googleapis.com/ajax/services/search/web?v=1.0&rsz=8&userip=130.203.154.184&q='
    wiki_api = 'http://en.wikipedia.org/w/api.php?action=query&list=search&srlimit='+str(limit)+r'&srprop=snippet&format=json&srsearch='
    wiki_api2 = 'http://en.wikipedia.org/w/api.php?action=query&list=search&srlimit='+str(limit)+r'&srprop=snippet|titlesnippet|sectionsnippet&format=json&srsearch='
    query = re.sub('\s+','%20',query.strip())
    score = 0
    url = ''
    kb = knowledgebase.lower()
    if kb is 'google':
        url = google_api+query
    elif kb.startswith('wiki'):
        url = wiki_api+query
    else:
        print 'please specify the right knowledgebase'
        return
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent','Mozilla/5.0')]
    try:
        t = opener.open(url).read()
        js = json.loads(t)
    except:
        print 'Error'
        return -1
    if kb is 'google':
        rs = js['responseData']['results']
        contents = [r['content'] for r in rs]
        for i in range(len(contents)):
            sim = simContent(content,contents[i])
            if i > 0:
                score = score + sim/log(i+1,2)
            else:
                score = score + sim
    if kb.startswith('wiki'):
        try:
            rs = js['query']['search']
            i = 0
            for r in rs:
                snippet = re.sub('<.*?>','',r['snippet'])
                title = r['title']
                sim = simContent(content,snippet)
                if i > 0:
                    score = score + sim/log(i+1,2)
                else:
                    score = score + sim
                i = i + 1
        except:
            print 'Error'
            return -1
    return score

def simContent(p1,p2,metric='jaccard'):
    s1 = Set(p1.strip().split())
    s2 = Set(p2.strip().split())
    return len(s1&s2)/(len(s1|s2)+0.0)
def jaccardSim(s1,s2):#s1 and s2 are lists or sets
    s1 = Set([ w.lower() for w in s1])
    s2 = Set([w.lower() for w in s2])
    return len(s1&s2)/(len(s1|s2)+0.0)


def getSimilarity(w1,w2):
#calculate different relatedness of two words using three knoweldge base, Citeseer, Wikipedia, Google
    return

def getCandidates(input):
    stopwords = open(r'../StopWords').read().strip().split()
    cands = {}
    tag_words = []
    if len(input)<100:
        tag_words = pos_tag(word_tokenize(input))
    else:
        sents = re.split('\.\n+',input)
        for sent in sents:
            print sent,'@@@@'
            tag_words.extend(pos_tag(word_tokenize(sent)))
    #open(r'../PRML.token.tag','w').write(str(tag_words).strip('[]()').replace('), (','\n'))
    #print tag_words
    for i in range(len(tag_words)):
        w,tag = tag_words[i]
        if w.lower() in stopwords or w.isdigit() or len(w)<2 or re.search('[^a-zA-Z0-9_-]',w) is not None:
                continue
        if len(w)==2 and w[0].isalpha() and w[1].isdigit():
                continue
        if tag.startswith('N'):
            if w not in cands:
                cands[w]=[(i,1)]
            else:
                cands[w].append((i,1))
            if i > 0 and tag_words[i-1][0] not in stopwords and tag_words[i-1][1][0] in ['J','N']:
                w2=tag_words[i-1][0]+' '+w
                if w2 not in cands:
                    cands[w2]=[(i-1,2)]
                else:
                    cands[w2].append((i-1,2))
                if i > 1 and tag_words[i-2][0] not in stopwords and tag_words[i-2][1][0] in ['J','N']:
                    w3=tag_words[i-2][0]+' '+tag_words[i-1][0]+' '+w
                    if w3 not in cands:
                        cands[w3]=[(i-2,3)]
                    else:
                        cands[w3].append((i-2,3))
    return cands

def getCandidates2(input):#the input is tagged by stanford postagger
    stopwords = open(r'../StopWords').read().strip().split()
    cands = {}
    words = input.split()
    tag_words = [(wt[:wt.rfind('_')],wt[wt.rfind('_')+1:]) for wt in words]
    #open(r'../PRML.token.tag','w').write(str(tag_words).strip('[]()').replace('), (','\n'))
    for i in range(len(tag_words)):
        w,tag = tag_words[i]
        if w == w.capitalize():
            w = w.lower()
        if w.lower() in stopwords or w.isdigit() or len(w)<2 or re.search('[^a-zA-Z0-9_-]',w) is not None:
                continue
        if len(w)==2 and w[0].isalpha() and w[1].isdigit():
                continue
        if tag.startswith('N'):
            if w not in cands:
                cands[w]=[i]
            else:
                cands[w].append(i)
            if i > 0 and tag_words[i-1][0] not in stopwords and tag_words[i-1][1][0] in ['J','N']:
                w2=tag_words[i-1][0]+' '+w
                if w2 not in cands:
                    cands[w2]=[i-1]
                else:
                    cands[w2].append(i-1)
                if i > 1 and tag_words[i-2][0] not in stopwords and tag_words[i-2][1][0] in ['J','N']:
                    w3=tag_words[i-2][0]+' '+tag_words[i-1][0]+' '+w
                    if w3 not in cands:
                        cands[w3]=[i-2]
                    else:
                        cands[w3].append(i-2)
    #index = open(r'../PRML.index').read()
    #p=0
    f=open(r'../PRML.candidates','w')
    for it in cands.items():
        f.write(str(it)[1:-1]+'\n')
        try:
            if re.search(it[0],index) is not None:
                p = p + 1
                print it[0]
        except:
            print 'Error'
            continue
    f.close()
    #print p,len(cands),len(index.split('\n'))
    #print 'precision:',p/(len(cands)+0.0)
    #print 'recall:',p/(len(index.split('\n'))+0.0)
    return tag_words,cands

def contextSimilarityRank(input, knowledgebase='wiki',direct=True):
    candidates=getCandidates(input)
    dic_score = {}
    for cand in candidates:
        dic_score[cand] = 0
    for cand in dic_score:
        print cand
        if direct is True:
            dic_score[cand] = getKScore(input,cand,knowledgebase)
        else:
            inputwithoutcand = input
            for w in cand.split():
                inputwithoutcand = inpputwithoutcand.replace(w,'')
            dic_score[cand] = getKScore(input,input,knowledgebase) - getKScore(input,inputwithoutcand,knowledgebase)
    ranklist = sorted(dic_score.items(),key=lambda x:x[1],reverse=True)
    return ranklist

def getCandidatesBySentence(input):#the input is tagged by stanford postagger
    stopwords = open(r'../StopWords').read().strip().split()
    cands = {}
    sents = re.split(r'_\.\n+',input.strip())
    without_tag_sents = []
    sent_dic = {}
    for i in range(len(sents)):
        sent = sents[i]
        sent_dic[i] = []
        tag_words = [(wt[:wt.rfind('_')],wt[wt.rfind('_')+1:]) for wt in sent.split()]
        without_tag_sents.append([tw[0] for tw in tag_words])
        for j in range(len(tag_words)):
            w,tag = tag_words[j]
            if w == w.capitalize():
                w = w.lower()
            if w.lower() in stopwords or w.isdigit() or len(w)<2 or re.search('[^a-zA-Z0-9_-]',w) is not None:
                    continue
            if len(w)==2 and w[0].isalpha() and w[1].isdigit():
                    continue
            if tag.startswith('N'):
                if w not in cands:
                    cands[w]=[i]
                    sent_dic[i].append(w)
                else:
                    cands[w].append(i)
                if j > 0 and tag_words[j-1][0] not in stopwords and tag_words[j-1][1][0] in ['J','N']:
                    w2=tag_words[j-1][0]+' '+w
                    if w2 not in cands:
                        cands[w2]=[i]
                        sent_dic[i].append(w2)
                    else:
                        cands[w2].append(i)
                    if j > 1 and tag_words[j-2][0] not in stopwords and tag_words[j-2][1][0] in ['J','N']:
                        w3=tag_words[j-2][0]+' '+tag_words[j-1][0]+' '+w
                        if w3 not in cands:
                            cands[w3]=[i]
                            sent_dic[i].append(w3)
                        else:
                            cands[w3].append(i)
    return without_tag_sents,sent_dic,cands

def contextSimilarityRank2(doc):
    index_list = []
    f = open(r'../index_list.out','w')
    text = open(doc).read()
    paras = re.split('\.\n+',text)
    for p in paras:
        print 'begin a para...'
        s = p.replace('\n',' ')
        if len(s.split()) < 50:
            index_list.extend(contextSimilarityRank(s)[:5])
        else:
            sents = re.split('[\.\?!]\s+',s)
            new_sents = [sents[0]]
            for i in range(1,len(sents)):
                if len(sents[i].split()) < 10:
                    new_sents[-1] = new_sents[-1]+' '+sents[i]
                else:
                    new_sents.append(sents[i])
            for sent in new_sents:
                index_list.extend(contextSimilarityRank(sent)[:5])
        f.write('\n'.join([str(item) for item in index_list])+'\n')
        print 'writing...'
    f.close()
    return index_list

def contextSimilarityRank3(doc):#input is a stanford postagger tagged file
    index_dic = {}
    f = open(doc+'.indexbyRank3','w')
    sents,sent_dic,cand_dic = getCandidatesBySentence(open(doc).read())
    q_rs = getQueryResults(cand_dic.keys(),'wiki')
    for i in range(len(sents)):
        score_dic={}
        for q in sent_dic[i]:
            snippts = q_rs[q]
            score = 0
            for j in range(len(snippts)):
                sim = jaccardSim(sents[i],snippts[j].split())
                if j > 0:
                    score = score + sim/log(j+1,2)
                else:
                    score = score + sim
            score_dic[q] = score
        rank_list = sorted(score_dic.items(),key=lambda x:x[1],reverse=True)
        for k,score in rank_list[:2]:
            print k,score
            if k not in index_dic:
                index_dic[k] = [i]
            else:
                index_dic[k].append(i)
            f.write(k+':'+str(score)+':'+str(i)+'\n')
    f.close()
    return index_dic

def topicTextRank(doc, flag_stemmer=False, flag_topic=False, flag_pos=False):
    doc_content = open(doc).read()
    topic_content = ''
    #if flag_topic is True:

    ws = 3 #context window size
    paras = re.split('\n+',doc_content.strip())
    dic = {}
    G = nx.DiGraph()
    stemmer = Stemmer.Stemmer('english')
    for p in paras:
        words = [w.lower() for w in p.split()]
        if flag_stemmer is True:
            words = stemmer.stemWords(words)
        n = len(words)-ws + 1
        m = min(len(words),ws)
        print len(words)
        if n <= 0:
            n = 1
        for i in range(n):
            if words[i] not in dic:
                dic[words[i]] = {}
            for w in words[i+1:i+1+m]:
                if w not in dic[words[i]]:
                    dic[words[i]][w] = 1
                else:
                    dic[words[i]][w] = dic[words[i]][w] + 1
    for k in dic:
        G.add_weighted_edges_from([(k,v,w) for (v,w) in dic[k].items()])
    pr = nx.pagerank(G,max_iter=200)
    s_pr = sorted(pr.items(),key=lambda x:x[1],reverse=True)
    #print s_pr[:500]
    D_in = G.in_degree()
    D = G.degree()
    #print sorted(D.items(),key=lambda x:x[1],reverse=True)[:100]
    #print sorted(D_in.items(),key=lambda x:x[1],reverse=True)[:100]
    pred = G.predecessors('function')
    deg = [(x,G.in_degree(x)) for x in pred]
    print sorted(pred),sorted(deg,key=lambda x:x[1],reverse=True)


if __name__ == "__main__":
    s=r'Sequential methods allow data points to be processed one at a time and then discarded and are important for on-line applications and also where large data sets are involved so that batch processing of all data points at once is infeasible'
    s1=r'A distribution is said to be invariant, or stationary, with respect to a Markov chain if each step in the chain leaves that distribution invariant.'
    s2=r'We see that there is an intimate relationship between data compression and density estimation (i.e., the problem of modelling an unknown probability distribution) because the most efficient compression is achieved when we know the true distribution.'
    #s=open(r'../test.txt').read()
    print getCandidatesBySentence(s)
    #print getKScore(s,'Sequential methods','wiki')
    #contextSimilarityRank3(r'../PRML.tag')
    #topicTextRank(open(r'../PRML2LDA.data').read().split('\n')[4])
    #genLDATrainingData()
    #dictGen()
    #home_dir = r'/home/zzw109/project/book'
    #books = open(home_dir+os.sep+'numofpages/101to...txt').read().strip().split('\n')
    #book_txt = [book.split()[0].replace('pdf','txt') for book in books]
    #txt_dir = r'/home/zzw109/project/book/allbookstxt'
    #txt_dir1 = r'/home/zzw109/project/book/goodbooks/books'
    #xml_dir = r'/home/zzw109/project/book/xml'
    #ref_dir = home_dir + os.sep + 'references'
    #index_dir = home_dir + os.sep + 'index'
    #txt = '10.1.1.139.8180.txt'
    #txt1= r'Pattern Recognition and Machine Learning.txt'
    #bk = BookDoc(txt1, txt_dir1, xml_dir, ref_dir)
    #bi = BookIndex(bk,index_dir+os.sep+txt)
    ##bi.autoIndexGen()
    #bi.indexParse()

