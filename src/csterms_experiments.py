#! /user/bin/python
#-*- coding: utf-8 -*-
import os,re,random,time,subprocess,logging
import urllib2,codecs,json,pickle
import networkx as nx
import Stemmer
from sets import Set
from math import log
from nltk import pos_tag
from nltk import word_tokenize
from gensim import corpora, models, similarities
from datetime import datetime
from nltk.tag.stanford import POSTagger
from math import sqrt

def getQueryResults(query_list,knowledgebase):
    limit = 20
    local_cache_path = r'../query/'
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
            try:
                js = json.loads(opener.open(url).read())
            except:
                print 'Error'
                query_results[q]=[]
                continue
            rs = js['responseData']['results']
            query_results[q]= [r['content'] for r in rs]
        elif kb.startswith('wiki'):
            url = wiki_api+query
            content = ''
            if os.path.exists(local_cache_path+q):
                print 'local hit'
                content = open(local_cache_path+q).read()
            else:
                print 'go to wiki'
                content = opener.open(url).read()
                open(r'../query/'+q,'w').write(content)
            try:
                js = json.loads(content)
                rs = js['query']['search']
                query_results[q]=[re.sub('<.*?>','',r['snippet']) for r in rs]
            except:
                print 'Error',query
                query_results[q]=[]
                #continue
        else:
            print 'please specify the right knowledgebase'
            return None
    return query_results

def cosineSim2(s1,p1,p2):#s1 is the word vector. p1 and p2 are two paragraphs.
    dic = {}
    for w in s1:
        w = w.lower()
        dic[w] = [len(re.findall(w,p1.lower())),len(re.findall(w,p2.lower()))]
    total = sum(dic[w][0]*dic[w][1] for w in dic)
    scalar1 = sqrt(sum(dic[w][0]*dic[w][0] for w in dic))
    scalar2 = sqrt(sum(dic[w][1]*dic[w][1] for w in dic))
    if scalar1*scalar2 == 0:
        return 0
    #print dic, total, scalar1,scalar2
    return float(total)/(scalar1*scalar2)

def cosineSim(s1,s2):#
    dic = {}
    for w in s1:
        if w==w.capitalize():
            w = w.lower()
        if w not in dic:
            dic[w] = [1,0]
        else:
            dic[w][0] += 1
    for w in s2:
        if w==w.capitalize():
            w = w.lower()
        if w not in dic:
            dic[w] = [0,1]
        else:
            dic[w][1] += 1
    total = sum(dic[w][0]*dic[w][1] for w in dic)
    scalar1 = sqrt(sum(dic[w][0]*dic[w][0] for w in dic))
    scalar2 = sqrt(sum(dic[w][1]*dic[w][1] for w in dic))
    #print dic, total, scalar1,scalar2
    return float(total)/(scalar1*scalar2)

def jaccardSim(s1,s2,stopwords):#s1 and s2 are lists or sets
    #stopwords = open(r'../StopWords').read().strip().split('\n')
    s1 = Set([w.lower() for w in s1 if w not in stopwords])
    s2 = Set([w.lower() for w in s2 if w not in stopwords])
    score = len(s1&s2)/(len(s1|s2)+0.0)
    #print s1,s2,score
    return score

def getCandidates(input,output,stopwords,commonwords):
    cands = {}
    sents = re.split(r'\.\.\._: \.\.\._: \._\.',input.replace('\n',' '))
    #sents = [sent.split('\n')[0] for sent in sents]
    #st = POSTagger(r'/home/zzw109/download/stanford-postagger-full-2012-07-09/models/english-bidirectional-distsim.tagger',r'/home/zzw109/download/stanford-postagger-full-2012-07-09/stanford-postagger.jar')
    sent_dic = {}
    print len(sents)
    for i in range(len(sents)):
        sent = sents[i]
        sent_dic[i] = []
        tag_words = [(wt[:wt.rfind('_')],wt[wt.rfind('_')+1:]) for wt in sent.split()]
        #tag_words = st.tag(sent.split())
        #without_tag_sents.append([tw[0] for tw in tag_words])
        for j in range(len(tag_words)):
            w,tag = tag_words[j]
            if tag.startswith('N') is False:
                continue
            if w == w.capitalize():
                w = w.lower()
            if w.lower() in stopwords or w.isdigit() or len(w)<2 or re.search('[^a-zA-Z0-9_#\$-]',w) is not None:
                continue
            if len(w)==2 and w[0].isalpha() and re.search('[0-9ijk\.]',w[1]):
                continue
            if len(w)==3 and w[1] in ['i','j','k'] and w[2] in ['i','j','k']:
                continue
            if w not in commonwords[0]:
                if w not in cands:
                    cands[w] = [i]
                else:
                    cands[w].append(i)
                if w not in sent_dic[i]:
                    sent_dic[i].append(w)
            w1,tag1 = tag_words[j-1]
            if j > 0 and w1 not in stopwords and tag1[0] in ['J','N','I','D'] and re.search('[^a-zA-Z0-9_-]',w1) is None:
                if w1 == w1.capitalize():
                    w1 = w1.lower()
                if w in commonwords[0] and tag1[0] in ['I','D']:
                        continue
                w = w1 + ' ' + w
                if w not in commonwords[1]:
                    if w not in cands:
                        cands[w]=[i]
                    else:
                        cands[w].append(i)
                    if w not in sent_dic[i]:
                        sent_dic[i].append(w)
                w1,tag1 = tag_words[j-2]
                if j > 1 and w1 not in stopwords and tag1[0] in ['J','N','I','D'] and re.search('[^a-zA-Z0-9_-]',w1) is None:
                    if w1 == w1.capitalize():
                        w1 = w1.lower()
                    w = w1 + ' ' + w
                    if w not in commonwords[2]:
                        if w not in cands:
                            cands[w]=[i]
                        else:
                            cands[w].append(i)
                        if w not in sent_dic[i]:
                            sent_dic[i].append(w)
                    w1,tag1 = tag_words[j-3]
                    if j > 2 and w1 not in stopwords and tag1[0] in ['J','N','I','D'] and re.search('[^a-zA-Z0-9_-]',w1) is None:
                        if w1 == w1.capitalize():
                            w1 = w1.lower()
                        w = w1 + ' ' + w
                        if w not in commonwords[2]:
                            if w not in cands:
                                cands[w]=[i]
                            else:
                                cands[w].append(i)
                            if w not in sent_dic[i]:
                                sent_dic[i].append(w)
    open(output,'w').write('\n'.join([k+':'+str(v) for k,v in cands.items()]))
    #return cands
    return sent_dic,cands


def tfidfRank(doc):
    index_dic = {}
    f = open(doc+'.indexbytfidf','w')
    stopwords = open(r'../StopWords').read().strip().split('\n')
    cw1 = [line.split(':')[0] for line in open(r'../commonwords.1').read().split('\n')[:1000]]
    cw2 = [line.split(':')[0] for line in open(r'../commonwords.2').read().split('\n')[:300]]
    cw3 = [line.split(':')[0] for line in open(r'../commonwords.3').read().split('\n')[:300]]
    terms,sents = open(r'../cs.terms').read().strip().split('\n'),open(r'../csterms.txt').read().strip().split('\n*****************\n')
    #first_sents = [sent.split('. ')[0] for sent in sents]
    sent_dic,cand_dic = getCandidates(open(doc).read().strip(), r'../csterms.cands',stopwords,[cw1,cw2,cw3])
    df_dic = {}
    for q in set(cand_dic)|set(' '.join(terms).split()):
        if not os.path.exists(r'../queries/'+q):
            continue
        sr = re.search('{"totalhits":(\d+)}',open(r'../queries/'+q).read())
        df = 0
        if sr is not None:
            df = int(sr.group(1))
        df_dic[q] = df
        print q,df
    recall,prec,tk = 0, 0, 1
    for i in range(len(sent_dic)):
        print i
        score_dic = {}
        for q in set(sent_dic[i])|set(terms[i].split()):
        #for q in sent_dic[i]:
            try:
                finding = re.findall(q.lower(),sents[i].lower())
            except:
                continue
            tf = len(re.findall(q.lower(),sents[i].lower()))
            df = 1
            #if q not in df_dic:
            #    df = 1
            #else:
            #    df = df_dic[q]
            score_dic[q] = tf
            #score_dic[q] = tf*log(4150790/(df+1))
        rank_list = sorted(score_dic.items(),key=lambda x:x[1],reverse=True)
        for k,score in rank_list[:tk]:
            if re.search(k.lower(),terms[i].lower()) is not None:
                prec +=1
        for k,score in rank_list[:tk]:
            if re.search(k.lower(),terms[i].lower()) is not None:
                recall +=1
                break
        for k,score in rank_list[:tk]:
            if k not in index_dic:
                index_dic[k] = [i]
            else:
                index_dic[k].append(i)
            f.write(k+':'+str(score)+':'+str(i)+'\n')
    f.close()
    print recall/1255.0,prec/1255.0

def getWikiDF(q):
    wiki_api = 'http://en.wikipedia.org/w/api.php?action=query&list=search&srsearch='
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent','Mozilla/5.0')]
    query = re.sub('\s+','%20',q.strip())
    url = wiki_api+query
    t = opener.open(url).read()
    #print t
    df = re.search(r'totalhits=&quot;(\d+)&quot;',t).group(1)
    return int(df)
    

def contextSimilarityRank3(doc):
    top_k = 10
    index_dic = {}
    stopwords = open(r'../StopWords').read().strip().split('\n')
    cw1 = [line.split(':')[0] for line in open(r'../commonwords.1').read().split('\n')[:1000]]
    cw2 = [line.split(':')[0] for line in open(r'../commonwords.2').read().split('\n')[:300]]
    cw3 = [line.split(':')[0] for line in open(r'../commonwords.3').read().split('\n')[:300]]
    f = open(doc+'.indexbyRank3','w')
    terms,sents = open(r'../cs.terms').read().strip().split('\n'),open(r'../csterms.txt').read().strip().split('\n*****************\n')
    #first_sents = [sent.split('. ')[0] for sent in sents]
    sent_dic,cand_dic = getCandidates(open(doc).read().strip(), r'../csterms.cands',stopwords,[cw1,cw2,cw3])
    q_rs = getQueryResults(cand_dic.keys(),'wiki')
    recall,prec,tk=0,0,10
    for i in range(len(sent_dic)):
        print i
        #print sents[i],sent_dic[i]
        score_dic={}
        for q in sent_dic[i]:
            snippts = q_rs[q][:top_k]
            score = 0
            for j in range(len(snippts)):
                #sim = jaccardSim(sents[i].split(),snippts[j].split())
                sim = cosineSim2(sent_dic[i],sents[i],snippts[j])
                #print q,snippts[j],sim
                if j > 0:
                    score = score + sim/log(j+1,2)
                else:
                    score = score + sim
            score_dic[q] = score
        rank_list = sorted(score_dic.items(),key=lambda x:x[1],reverse=True)
        for k,score in rank_list[:tk]:
            if re.search(k.lower(),terms[i].lower()) is not None:
                prec +=1
        for k,score in rank_list[:tk]:
            if re.search(k.lower(),terms[i].lower()) is not None:
                recall +=1
                break
        for k,score in rank_list[:tk]:
            print k,score
            #if levenshtein(terms[i].lower(),k.lower())<=min(len(terms[i]),len(k))/6:recall +=1
            if k not in index_dic:
                index_dic[k] = [i]
            else:
                index_dic[k].append(i)
            f.write(k+':'+str(score)+':'+str(i)+'\n')
    f.close()
    print recall,prec,len(terms)
    return index_dic

def levenshtein(a,b):
    "Calculates the Levenshtein distance between a and b."
    n, m = len(a), len(b)
    if n > m:
    # Make sure n <= m, to use O(min(n,m)) space
        a,b = b,a
        n,m = m,n
    current = range(n+1)
    for i in range(1,m+1):
        previous, current = current, [i]+[0]*n
        for j in range(1,n+1):
            add, delete = previous[j]+1, current[j-1]+1
            change = previous[j-1]
            if a[j-1] != b[i-1]:
                change = change + 1
            current[j] = min(add, delete, change)
    return current[n]

def fuzzy_match(w,w_list):
    len_w = len(w)
    if len_w < 7:
        return False
    for aw in w_list:
        if aw[0] != w[0]:
            continue
        if w == aw:
            return True
        if len(set(w)| set(aw)) >= 2*min(len(w),len(aw)):
            continue
        if len_w/levenshtein(aw,w) > 6:
            return True
    return False

class MyCorpus(object):
    def __iter__(self):
        for line in open('test.data'):
            yield dictionary.doc2bow(line.lower().split())

def testGensim0():
    docs = [line.lower().split() for line in open('test.data')]
    dictionary = corpora.Dictionary(docs)
    stoplist = open(r'../StopWords').read().strip().split()
    stop_ids = [dictionary.token2id[sw] for sw in stoplist if sw in dictionary.token2id]
    dictionary.filter_tokens(stop_ids)
    dictionary.compactify()
    print dictionary
    dictionary.save('test.dict')
    #myCorpus = MyCorpus()
    cps = [dictionary.doc2bow(doc) for doc in docs]
    corpora.MmCorpus.serialize('test.mm', cps)
    corpora.BleiCorpus.serialize('test.lda-c',cps)
    corpora.SvmLightCorpus.serialize('test.svmlight',cps)
    corpora.LowCorpus.serialize('test.low',cps)

def testGensim():
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    dict = corpora.Dictionary.load('test.dict')
    cps = corpora.MmCorpus('test.mm')
    print cps
    
    tfidf = models.TfidfModel(cps)
    cps_tfidf = tfidf[cps]

    lsi = models.LsiModel(cps_tfidf, id2word=dict, num_topics=20)
    cps_lsi = lsi[cps_tfidf]
    lsi.print_topics(2)

    lda = models.LdaModel(cps_tfidf,num_topics=20)
    print lda[cps[0]]

def extractCSterms():#List of programming and computer science terms
    t = open(r'../List_of_programming_and_computer_science_terms.html').read().replace('\n',' ')
    p = re.compile('<li><b>(.*?)</b>(.*?)</li>')
    terms = re.findall(p,t)
    #out = [t[0]+'\n'+t[1].strip() for t in terms]
    out1 = [t[0] for t in terms]
    out2 = [t[1].strip() for t in terms]
    open(r'../csterms.txt','w').write('\n*****************\n'.join(out2))
    open(r'../cs.terms','w').write('\n'.join(out1))

def wikiQuery():
    query_list = open(r'../cands2wiki').read().strip().split('\n')[900000:1500000]
    limit = 50
    ferr = open(r'../querieswitherrors900000','w')
    wiki_api = 'http://en.wikipedia.org/w/api.php?action=query&list=search&srlimit='+str(limit)+r'&srprop=snippet&format=json&srsearch='
    wiki_api2 = 'http://en.wikipedia.org/w/api.php?action=query&list=search&srlimit='+str(limit)+r'&srprop=snippet|titlesnippet|sectionsnippet&format=json&srsearch='
    url = ''
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent','Mozilla/5.0')]
    for q in query_list:
        print q
        query = re.sub('\s+','%20',q.strip())
        url = wiki_api+query
        try:
            #js = json.loads(opener.open(url).read())
            #rs = js['query']['search']
            #query_results[q]=[re.sub('<.*?>','',r['snippet']) for r in rs]
            t = opener.open(url).read()
            open(r'../queries/'+q,'w').write(t)
        except:
            print 'Error'
            ferr.write(q+'\n')
            continue
    ferr.close()

def copy2Queries():
    for f in os.listdir(r'../query'):
        if os.path.getctime(r'../query/'+f) > 1345041379 and os.path.exists(r'../queries/'+f) is False:
            print 'copy2...'
            shutil.copy2(r'../query/'+f,r'../queries/'+f)

from datetime import datetime
import shutil
if __name__ == "__main__":
    #s1 = " AARON is a screensaver program written by artist  Harold Cohen who created the original artistic images. AARON utilizes  artificial intelligence to continuously create original paintings on  PCs."
    #l1 = ['AARON', 'screensaver', 'screensaver program', 'artist', 'harold', 'artist harold', 'cohen', 'harold cohen', 'artist harold cohen', 'artistic images', 'original artistic images', 'intelligence', 'paintings', 'original paintings', 'PCs']
    #s2 = "Harold Cohen may refer to: Harold Cohen (artist) Harold Cohen (politician), Australian politician and brigadier. Harold Cohen Library , ..."
    #l2 = s2.split()
    #print cosineSim(s1.split(),l2)
    #extractCSterms()
    #t=datetime.now()
    #contextSimilarityRank3(r'../csterms.tag')
    #print(datetime.now()-t)
    #copy2Queries()
    tfidfRank(r'../csterms.tag')
