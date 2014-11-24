#! /user/bin/python
#-*- coding: utf-8 -*-
import os,re,random,time,subprocess,logging
import urllib2,codecs,json
from extractor import BookDoc
from ToCdetection import ToC_detection
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

class KeywordsExtraction():

    def __init__(self,home_dir=r'~',doc_dir='',cands_dir='',index_dir='',docs=[],doc_keys = {},stopwords=[],commonwords=[],tagged=True,top_k=5):
        self._home_dir = home_dir
        self._doc_dir = doc_dir
        self._cands_dir = cands_dir
        self._index_dir = index_dir
        self.docs = docs
        self.doc_keys = doc_keys
        self._stopwords = stopwords
        self._commonwords = commonwords
        self._tagged = tagged
        self.keys_top_k = top_k
        if not tagged:
            self._tagger4short = POSTagger(r'/home/zzw109/download/stanford-postagger-full-2012-07-09/models/english-bidirectional-distsim.tagger',r'/home/zzw109/download/stanford-postagger-full-2012-07-09/stanford-postagger.jar')
            self._tag_dir = r'/home/zzw109/download/stanford-postagger-full-2012-07-09'
            self._classpath = self._tag_dir+r'/stanford-postagger.jar edu.stanford.nlp.tagger.maxent.MaxentTagger'
            self._model = self._tag_dir+r'/models/wsj-0-18-left3words-distsim.tagger'

    def pos_tag_for_short_text(self,sent):
        return self._tagger4short.tag(sent.split())

    def pos_tag(self,infile,outfile):
        cmd = "java -mx2000m -classpath "+self._classpath+" -model "+self._model+" -textFile "+infile+" > "+outfile
        os.system(cmd)
    
    def pos_tag_all_docs(self,out_dir):
        for doc in self.docs:
            self.pos_tag(self._doc_dir+os.sep+doc,out_dir+os.sep+doc)

    def getQueryResults(self,query_list,knowledgebase):
        limit = 20
        local_cache_path = r'../queries/'
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
                try:
                    js = json.loads(content)
                    rs = js['query']['search']
                    query_results[q]=[re.sub('<.*?>','',r['snippet']) for r in rs]
                    open(r'../queries/'+q,'w').write(content)
                except:
                    print 'Error',query
                    query_results[q]=[]
                    #continue
            else:
                print 'please specify the right knowledgebase'
                return None
        opener.close()
        return query_results

    def _cosineSim2(self,s1,p1,p2):#s1 is the word vector. p1 and p2 are two paragraphs.
        dic = {}
        for w in s1:
            w = w.lower()
            dic[w] = [len(re.findall(w,p1.lower())),len(re.findall(w,p2.lower()))]
        total = sum(dic[w][0]*dic[w][1] for w in dic)
        scalar1 = sqrt(sum(dic[w][0]*dic[w][0] for w in dic))
        scalar2 = sqrt(sum(dic[w][1]*dic[w][1] for w in dic))
        if scalar1*scalar2 == 0:
            return 0
        return float(total)/(scalar1*scalar2)

    def _cosineSim(self,s1,s2):#
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

    def _jaccardSim(self,s1,s2):#s1 and s2 are lists or sets
        stopwords = open(r'../StopWords').read().strip().split('\n')
        s1 = Set([w.lower() for w in s1 if w not in stopwords])
        s2 = Set([w.lower() for w in s2 if w not in stopwords])
        score = len(s1&s2)/(len(s1|s2)+0.0)
        #print s1,s2,score
        return score

    def getCandidates(self,input,outputfile):
        cands = {}
        sents = re.split(r'_\.\n+',input.strip())
        sent_dic = {}
        untagged_sents = []
        commonwords = self._commonwords
        stopwords = self._stopwords
        print len(sents)
        for i in range(len(sents)):
            sent = sents[i]
            sent_dic[i] = []
            tag_words = [(wt[:wt.rfind('_')],wt[wt.rfind('_')+1:]) for wt in sent.split()]
            untagged_sents.append([tw[0] for tw in tag_words])
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
                if len(w)==3 and w[1].lower() in ['i','j','k'] and w[2].lower() in ['i','j','k']:
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
        open(outputfile,'w').write('\n'.join([k+':'+str(v) for k,v in cands.items()]))
        return untagged_sents,sent_dic,cands

    def contextSimilarityRank(self,doc):
        top_k = 20
        keys_top_k = self.keys_top_k
        index_dic = {}
        stopwords = self._stopwords
        sents,sent_dic,cand_dic = self.getCandidates(open(self._doc_dir+os.sep+doc).read().strip(), self._cands_dir+os.sep+doc+'.cands.out')
        q_rs =self.getQueryResults(cand_dic.keys(),'wiki')
        for i in range(len(sent_dic)):
            #print i
            #print sents[i],sent_dic[i]
            score_dic={}
            for q in sent_dic[i]:
                snippts = q_rs[q][:top_k]
                score = 0
                for j in range(len(snippts)):
                    #sim = self._jaccardSim(sents[i],snippts[j].split())
                    sim = self._cosineSim2(sent_dic[i],' '.join(sents[i]), snippts[j])
                    if j > 0:
                        score = score + sim/log(j+1,2)
                    else:
                        score = score + sim
                score_dic[q] = score
            rank_list = sorted(score_dic.items(),key=lambda x:x[1],reverse=True)
            N = max(1,len(rank_list)/10)
            for k,score in rank_list[:N]:
                #print k,score
                if k not in index_dic:
                    index_dic[k] = [(i,score)]
                else:
                    index_dic[k].append((i,score))
        #sorted_by_num = sorted(index_dic.items(),key=lambda x:len(x[1]),reverse=True)
        sorted_by_score = sorted(index_dic.items(),key=lambda x:sum(s[1] for s in x[1]),reverse=True)
        top_cands = [it[0].lower() for it in sorted_by_score[:keys_top_k]]
        wiki_titles = self.findWikipediaTitles(top_cands)
        open(self._index_dir+os.sep+doc+'.index','w').write('\n'.join(wiki_titles))
        #recall = Set(top_k) & Set(self.doc_keys[doc[:doc.rfind('.')]])
        keys = self.doc_keys[doc[:doc.rfind('.')]]
        recall = [w for w in wiki_titles if self.fuzzy_match(w,keys)]
        print recall,keys
        return len(recall), len(wiki_titles), len(keys)

    def findWikipediaTitles(self,q_list):
        api = r'http://en.wikipedia.org/w/api.php?action=query&titles='
        wiki_titles = []
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent','Mozilla/5.0')]
        for q in q_list:
            q1 = re.sub('\s+','%20',q.strip())
            try:
                #print api+q1
                t = opener.open(api+q1).read()
                if re.search('pageid',t) is not None:
                    wiki_titles.append(q)
            except:
                print 'Error'
                continue
        opener.close()
        return wiki_titles
        
    def contextSimilarityRankAll(self):
        f = open(self._home_dir+os.sep+'all.results','w')
        for doc in self.docs:
            x,y,z=self.contextSimilarityRank(doc)
            prec = x/(y+0.0)
            recall = x/(z+0.0)
            f.write(doc+':'+str(prec)+':'+str(recall)+'\n')
        f.close()

    def levenshtein(self,a,b):
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

    def fuzzy_match(self,w,w_list):
        len_w = len(w)
        if len_w < 4:
            return False
        for aw in w_list:
            if aw[0] != w[0]:
                continue
            if w == aw or (len(w)*2>len(aw) and re.search(w,aw) is not None):
                return True
            if len(set(w)| set(aw)) >= 2*min(len(w),len(aw)):
                continue
            if len_w/self.levenshtein(aw,w) > 6:
                return True
        return False

    def testGensim0(self):
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

    def testGensim(self):
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


    def wikiQuery(self):
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



def runWiki20():
    home = r'/home/zzw109/project/bookgen/datasets/wiki20'
    doc_dir = home+r'/tagdocs'
    cands_dir = home+r'/cands'
    index_dir = home+r'/index'
    cw1 = [line.split(':')[0] for line in open(r'../commonwords.1').read().split('\n')[:1000]]
    cw2 = [line.split(':')[0] for line in open(r'../commonwords.2').read().split('\n')[:300]]
    cw3 = [line.split(':')[0] for line in open(r'../commonwords.3').read().split('\n')[:300]]
    commonwords = [cw1,cw2,cw3]
    stopwords = open(r'../StopWords').read().strip().split('\n')
    doc_keys = {}
    for team in os.listdir(home+'/teams'):
        for id in os.listdir(home+'/teams/'+team):
            #print team,id
            keywords = [line.split(': ')[1].lower() for line in open(home+'/teams/'+team+'/'+id).read().strip().split('\n')]
            id = id[:id.find('.')]
            if id not in doc_keys:
                doc_keys[id] = Set(keywords)
            else:
                doc_keys[id] |= Set(keywords)
    ke = KeywordsExtraction(home,doc_dir,cands_dir,index_dir,os.listdir(doc_dir)[0:2],doc_keys,stopwords,commonwords,tagged=True)
    #ke.pos_tag_all_docs(home+'/tagdocs')
    ke.contextSimilarityRankAll()

def runSemeval2010():
    home = r'/home/zzw109/project/bookgen/datasets/semeval2010'
    #doc_dir = home+r'/tagdocs'
    doc_dir = home+r'/maui-semeval2010-train'
    cands_dir = home+r'/cands'
    index_dir = home+r'/index'
    cw1 = [line.split(':')[0] for line in open(r'../commonwords.1').read().split('\n')[:1000]]
    cw2 = [line.split(':')[0] for line in open(r'../commonwords.2').read().split('\n')[:300]]
    cw3 = [line.split(':')[0] for line in open(r'../commonwords.3').read().split('\n')[:300]]
    commonwords = [cw1,cw2,cw3]
    stopwords = open(r'../StopWords').read().strip().split('\n')
    doc_keys = {}
    for team in os.listdir(home+'/teams'):
        for id in os.listdir(home+'/teams/'+team):
            #print team,id
            keywords = [line.split(': ')[1].lower() for line in open(home+'/teams/'+team+'/'+id).read().strip().split('\n')]
            id = id[:id.find('.')]
            if id not in doc_keys:
                doc_keys[id] = Set(keywords)
            else:
                doc_keys[id] |= Set(keywords)
    #ke = KeywordsExtraction(home,doc_dir,cands_dir,index_dir,os.listdir(doc_dir)[2:20],doc_keys,stopwords,commonwords,tagged=False)
    ke = KeywordsExtraction(home,doc_dir,cands_dir,index_dir,os.listdir(doc_dir)[2:20],doc_keys,stopwords,commonwords,tagged=False)
    ke.pos_tag_all_docs(home+'/tagdocs')
    #ke.contextSimilarityRankAll()


if __name__ == "__main__":
    home = r'/home/zzw109/project/bookgen/datasets/BackOfTheBookIndexBenchmark/'
    tagdir = home+'tagtext'
    ke = KeywordsExtraction(home,home+'text','','',[f.replace(' ','\ ').replace('\'','\\\'').replace('&','\&') for f in os.listdir(home+'text')],{},[],[[],[],[]],tagged=False)
    ke.pos_tag_all_docs(tagdir)
    #runWiki20()
    #runSemeval2010()
    #for line in t:
    #    doc,p,r = line.split(':')
    #    pre += float(p)
    #    rec += float(r)
    #print pre/20,rec/20
