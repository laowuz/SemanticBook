#! /user/bin/python
#-*- coding: utf-8 -*-
import os,re,random,time,subprocess,logging
import urllib2,codecs,json
from extractor import BookDoc
from ToCdetection import ToC_detection
import networkx as nx
import Stemmer
import shelve,cPickle
from sets import Set
from math import log,exp
from nltk import pos_tag
from nltk import word_tokenize
from gensim import corpora, models, similarities
from datetime import datetime
from csterms_experiments import cosineSim2,cosineSim, jaccardSim

def dictGen(start,end,out):#generate the DF info of all words in book set
    home_dir = r'/home/zzw109/project/book'
    home_dir1 = r'/home/zzw109/project/bookgen'
    books = open(home_dir+os.sep+'numofpages/101to...txt').read().strip().split('\n')
    book_txt = [book.split()[0].replace('pdf','txt') for book in books]
    txt_dir = r'/home/zzw109/project/book/allbookstxt'
    tag_txt_dir = r'/home/zzw109/project/bookgen/tagallbooktxt'
    stopwords = open(home_dir1+os.sep+'StopWords').read().strip().split()
    word_dic = {}
    doc_dic = {}
    for id in os.listdir(tag_txt_dir)[start:end]:
        print id 
        try:
            f = open(tag_txt_dir+os.sep+id)
            text = f.read().strip()
            sents = re.split('\s+[\.:;?,]_[\.:,]\s+',text)
            id = id[7:-4]
            for sent in sents:
                sent = sent.strip()
                w_ts = [(wt[:wt.rfind('_')],wt[wt.rfind('_')+1:]) for wt in re.split('\s+',sent)]
                words = [w[0] for w in w_ts if w[1].startswith('N')]
                grams2,grams3,grams4 = [],[],[]
                N = len(w_ts)
                if N > 1:
                    grams2 = [w_ts[i][0]+' '+w_ts[i+1][0] for i in range(N-1) if w_ts[i+1][1].startswith('N')]
                if N > 2:
                    grams3 = [w_ts[i][0]+' '+w_ts[i+1][0]+' '+w_ts[i+2][0] for i in range(N-2) if w_ts[i+2][1].startswith('N')]
                if N > 3:
                    grams4 = [w_ts[i][0]+' '+w_ts[i+1][0]+' '+w_ts[i+2][0]+' '+w_ts[i+3][0] for i in range(N-3) if w_ts[i+3][1].startswith('N')]
                words = words + grams2 + grams3 + grams4
                for w in words:
                    w = w.lower()
                    if w.isdigit() or w in stopwords or len(w)<2 or (len(w)==2 and w[1].isalpha() is False):
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
    fopen = open(home_dir1+os.sep+out,'w')
    for it in sorted_dic:
        fopen.write(str(it[0])+':'+str(len(it[1]))+'\n')
    fopen.close()

def commonWordsGen(dictlist):
    dic = {}
    for dict in dictlist:
        print dict
        num_line = 0
        for line in open(dict):
            num_line += 1
            if num_line > 50000:
                break
            w,df = line[:line.rfind(':')],line[line.rfind(':')+1:]
            if w in dic:
                dic[w] += int(df)
            else:
                dic[w] = int(df)
    s_dic = sorted(dic.items(),key=lambda x:x[1],reverse=True)
    open(r'../commonwords','w').write(str(s_dic).strip('[()]').replace('), (','\n').replace(',',':').replace('\'',''))
    
def commonWordsClean():
    f1 = open(r'../commonwords.1','w')
    f2 = open(r'../commonwords.2','w')
    f3 = open(r'../commonwords.3','w')
    stopwords = open(r'../StopWords').read().strip().split('\n')
    for line in open(r'../commonwords'):
        w,df = line.split(': ')
        ws = w.split()
        if ws[-1] in stopwords or len(ws[-1])==1 or ws[-1][-1] in ['.','"','/']:
            continue
        if len(ws) == 2 and (ws[0] in stopwords or len(ws[0])==1):
            continue
        if len(ws) == 3 and ws[0] in stopwords and ws[1] in stopwords:
            continue
        if len(ws) == 4 and ws[0] in stopwords and ws[1] in stopwords and ws[2] in stopwords:
            continue
        if len(ws) == 1:
            f1.write(w+':'+df)
        if len(ws) == 2:
            f2.write(w+':'+df)
        if len(ws) >2:
            f3.write(w+':'+df)
    f1.close()
    f2.close()
    f3.close()

def tagAllBook():# POS tag all books 
    home_dir = r'/home/zzw109/project/book'
    books = open(home_dir+os.sep+'numofpages/101to...txt').read().strip().split('\n')
    book_txt = [book.split()[0].replace('pdf','txt') for book in books]
    #txt_dir = r'/home/zzw109/project/book/allbookstxt'
    txt_dir = r'/home/zzw109/project/bookgen/datasets/BackOfTheBookIndexBenchmark/corpus/History+Art'
    tag_dir = r'/home/zzw109/download/stanford-postagger-full-2012-07-09'
    tagger = tag_dir+r'/stanford-postagger.sh'
    model = tag_dir+r'/models/wsj-0-18-left3words-distsim.tagger'
    out_dir = r'/home/zzw109/project/bookgen/tagallbooktxt'
    #for txt in book_txt[:3]:
    for txt in os.listdir(txt_dir):
        if not txt.endswith('text'):
            continue
        in_file = txt_dir+os.sep+txt
        out_file = out_dir+os.sep+txt
        #subprocess.call([tagger,model,in_file,'>',out_file])
        os.system(tagger + ' ' + model + ' '+in_file + '>'+out_file)

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
        #print q
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
                #print 'local hit'
                content = open(local_cache_path+q).read()
            else:
                content = opener.open(url).read()
                open(r'../queries/'+q,'w').write(content)
            try:
                js = json.loads(content)
                rs = js['query']['search']
                #totalhits = js['query']['searchinfo']['totalhits']
                #query_results[q]=(totalhits,[(r['title'],re.sub('<.*?>','',r['snippet'])) for r in rs])
                query_results[q]=[re.sub('<.*?>','',r['snippet']) for r in rs]
            except:
                print q,'getQueryResutls Error'
                query_results[q]=[]
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


def getCandidatesBySentence(input,id,stopwords,commonwords):#the input is output of stanford postagger
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
            if tag.startswith('N') is False or len(w)>100:
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
                if w not in sent_dic[i]:
                    sent_dic[i].append(w)
                if w not in cands:
                    cands[w] = [i]
                else:
                    cands[w].append(i)
            w1,tag1 = tag_words[j-1]
            if j > 0 and w1 not in stopwords and tag1[0] in ['J','N','I'] and re.search('[^a-zA-Z0-9_-]',w1) is None:
                if w1 == w1.capitalize():
                    w1 = w1.lower()
                w = w1 + ' ' + w
                if w not in commonwords[1]:
                    if w not in sent_dic[i]:
                        sent_dic[i].append(w)
                    if w not in cands:
                        cands[w]=[i]
                    else:
                        cands[w].append(i)
                w1,tag1 = tag_words[j-2]
                if j > 1 and w1 not in stopwords and tag1[0] in ['J','N','I'] and re.search('[^a-zA-Z0-9_-]',w1) is None:
                    if w1 == w1.capitalize():
                        w1 = w1.lower()
                    w = w1 + ' ' + w
                    if w not in commonwords[2]:
                        if w not in sent_dic[i]:
                            sent_dic[i].append(w)
                        if w not in cands:
                            cands[w]=[i]
                        else:
                            cands[w].append(i)
                    w1,tag1 = tag_words[j-3]
                    if j > 2 and w1 not in stopwords and tag1[0] in ['J','N','I'] and re.search('[^a-zA-Z0-9_-]',w1) is None:
                        if w1 == w1.capitalize():
                            w1 = w1.lower()
                        w = w1 + ' ' + w
                        if w not in commonwords[2]:
                            if w not in sent_dic[i]:
                                sent_dic[i].append(w)
                            if w not in cands:
                                cands[w]=[i]
                            else:
                                cands[w].append(i)
    open(r'../candidate/'+id,'w').write('\n'.join([k+':'+str(v) for k,v in cands.items()]))
    #return cands
    return without_tag_sents,sent_dic,cands

def contextSimilarityRank3(doc,stopwords,commonwords):#input is a stanford postagger tagged file
    index_dic = {}
    #stopwords = open(r'../StopWords').read().strip().split('\n')
    f = open(doc+'.indexbyRank3','w')
    sents,sent_dic,cand_dic = getCandidatesBySentence(open(doc).read(),doc[doc.rfind('/')+1:],stopwords,commonwords)
    q_rs = getQueryResults(cand_dic.keys(),'wiki')
    for i in range(len(sents)):
        score_dic={}
        for q in sent_dic[i]:
            snippts = q_rs[q]
            score = 0
            for j in range(len(snippts)):
                sim = jaccardSim(sents[i],snippts[j].split(),stopwords)
                #sim = cosineSim2(sent_dic[i],sents[i],snippts[j])
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

def contextSimilarityRank4(start,end):
    docs = open(r'../goodbooklist').read().strip().split('\n')[start:end]
    docs = [line.split(':')[0] for line in docs]
    fout = open(r'../rank4.out-goodbooklist'+str(start)+'to'+str(end),'w')
    stopwords = open(r'../StopWords').read().strip().split('\n')
    ftime = open(r'../rank4.runningtime','w')
    for doc in docs:
        print doc
        t0 = datetime.now()
        #f = open(r'../rank3results/'+doc,'w')
        sents = re.split(r'_\.\n+',open(r'../tagallbooktxt/'+doc).read().strip())
        cands = open(r'../candidate/'+doc).read().strip().split('\n')
        sent_dic,words = {},[]
        for cand in cands:
            w,nums = cand.split(':')
            if len(w) > 100:
                continue
            if len(w)==2 and w[0].isalpha() and re.search('[0-9ijk\.]',w[1]):
                continue
            words.append(w)
            nums = nums.strip('[]').split(', ')
            for num in nums:
                if int(num) in sent_dic:
                    sent_dic[int(num)].append(w)
                else:
                    sent_dic[int(num)] = [w]
        q_rs = getQueryResults(words,'wiki')
        index_dic = {}
        for cand in cands:
            w,nums = cand.split(':')
            if len(w) > 100:
                continue
            if len(w)==2 and w[0].isalpha() and re.search('[0-9ijk\.]',w[1]):
                continue
            nums = nums.strip('[]').split(', ')
            nums = [int(n) for n in nums]
            snippts = q_rs[w]
            context_from_wiki = []
            context_from_doc = []
            for s in snippts:
                context_from_wiki.extend(s.split())
            for i in nums:
                sent_i = sents[i].strip().split()
                sent = [g[:g.rfind('_')].lower() for g in sent_i]
                context_from_doc.extend(sent)
            index_dic[w] = jaccardSim(context_from_doc,context_from_wiki,stopwords)
            #print w,index_dic[w]
        sorted_by_score = sorted(index_dic.items(),key=lambda x:x[1],reverse=True)
        top_cands = [it[0] for it in sorted_by_score[:len(sent_dic)]]
        dt = datetime.now()-t0
        num_words = len(re.split('\s+',open(r'/home/zzw109/project/book/allbookstxt/'+doc).read().strip()))
        ftime.write(str(num_words)+'\t'+str(len(sents))+'\t'+str(len(cands))+'\t'+str(dt.seconds)+'\n')
        index = ''
        recall_words,index_words = [],[]
        if os.path.exists(r'/home/zzw109/project/book/index/'+doc):
            index = open(r'/home/zzw109/project/book/index/'+doc).read().strip()
            recall_words,index_words = recall_untag(top_cands,index)
        else:
            index = open(r'../tagindex/'+doc).read().strip()
            recall_words,index_words = recall(top_cands,index)
        print len(recall_words),len(top_cands),len(index_words)
        fout.write(doc+':'+str(len(recall_words))+':'+str(len(top_cands))+':'+str(len(index_words))+'\n')
        fo = open(r'../rank4results/'+doc+'.index','w')
        for k in top_cands:
            out = ''
            if k in recall_words:
                out = '@@@'+k+':'+str(index_dic[k])
            else:
                out = k+':'+str(index_dic[k])
            fo.write(out+'\n')
        fo.close()
    fout.close()
    ftime.close()

def contextSimilarityRank3onLargeDataset(start,end):
    docs = open(r'../candidate.recall.75.100').read().strip().split('\n')[start:end]
    docs = [line.split(':')[0] for line in docs]
    fout = open(r'../rank3.out'+str(start)+'to'+str(end),'w')
    stopwords = open(r'../StopWords').read().strip().split('\n')
    for doc in docs:
        print doc
        #f = open(r'../rank3results/'+doc,'w')
        sents = re.split(r'_\.\n+',open(r'../tagallbooktxt/'+doc).read().strip())
        cands = open(r'../candidate/'+doc).read().strip().split('\n')
        sent_dic,words = {},[]
        for cand in cands:
            w,nums = cand.split(':')
            if len(w) > 100:
                continue
            if len(w)==2 and w[0].isalpha() and re.search('[0-9ijk\.]',w[1]):
                continue
            words.append(w)
            nums = nums.strip('[]').split(', ')
            for num in nums:
                if int(num) in sent_dic:
                    sent_dic[int(num)].append(w)
                else:
                    sent_dic[int(num)] = [w]
        q_rs = getQueryResults(words,'wiki')
        index_dic = {}
        for i in range(len(sents)):
            if i not in sent_dic or len(Set(sent_dic[i]))<3:
                continue
            score_dic={}
            sent_i = sents[i].strip().split()
            #sent_dic_i = sent_dic[i]
            #if len(sent_i) < 10 and 0<i<len(sents)-1:
            #    sent_i = sents[i-1].strip().split()+sent_i+sents[i+1].strip().split()
            #    if i-1 in sent_dic and i+1 in sent_dic:
            #        sent_dic_i = sent_dic[i-1]+sent_dic[i]+sent_dic[i+1]
            sent = [w[:w.rfind('_')].lower() for w in sent_i]
            #print i,sent_dic[i]
            for q in Set(sent_dic[i]):
                #totalhits = q_rs[q][0]
                #snippts = q_rs[q][1]
                snippts = q_rs[q][:10]
                score = 0
                #if q == 'fq':
                #    print sent_dic[i],sent,snippts
                #    time.sleep(10)
                for j in range(len(snippts)):
                    sim = 0
                    if len(Set(sent)&Set([s.lower() for s in snippts[j].split()])&Set(sent_dic[i])) > 1:
                        sim = cosineSim2(Set(sent_dic[i]),' '.join(sent),snippts[j])
                    else:
                        sim = 0.0001
                    #if len(Set(sent)&Set([s.lower() for s in snippts[j][1].split()])&Set(sent_dic_i)) > 1:
                        #sim = cosineSim2(Set(sent_dic_i),' '.join(sent),snippts[j][1])
                        #sim = jaccardSim(sent,snippts[j].split(),stopwords)
                    #if q.lower() == snippts[j][0].lower():
                    #    sim += 1.0
                    if j > 0:
                        score = score + sim/log(j+1,2)
                    else:
                        score = score + sim
                score_dic[q] = score
            rank_list = sorted(score_dic.items(),key=lambda x:x[1],reverse=True)
            TOP_K = max(1,len(rank_list)/8)
            if rank_list[0][1] == 0:
                Top_K = len(rank_list)
            for k,score in rank_list[:TOP_K]:
                print k,score
                if score == 0:
                    continue
                if k not in index_dic:
                    index_dic[k] = [(i,score)]
                else:
                    index_dic[k].append((i,score))
                #f.write(k+':'+str(score)+':'+str(i)+'\n')
        #f.close()
        sorted_by_score = sorted(index_dic.items(),key=lambda x:sum(s[1] for s in x[1]),reverse=True)
        N = len(sorted_by_score)
        for i in range(len(sorted_by_score)-1,1,-1):
            if len(sorted_by_score[i][1]) > 1:
                N = i
                break
        top_cands = [it[0] for it in sorted_by_score[:N]]
        index = ''
        #c1,c2 = 0,0
        recall_words,index_words = [],[]
        if os.path.exists(r'/home/zzw109/project/book/index/'+doc):
            index = open(r'/home/zzw109/project/book/index/'+doc).read().strip()
            recall_words,index_words = recall_untag(top_cands,index)
        else:
            index = open(r'../tagindex/'+doc).read().strip()
            recall_words,index_words = recall(top_cands,index)
        print len(recall_words),len(top_cands),len(index_words)
        fout.write(doc+':'+str(len(recall_words))+':'+str(len(top_cands))+':'+str(len(index_words))+'\n')
        fo = open(r'../rank3results/'+doc+'.index','w')
        for k in top_cands:
            out = ''
            if k in recall_words:
                out = '@@@'+k+':'+str(index_dic[k])
            else:
                out = k+':'+str(index_dic[k])
            fo.write(out+'\n')
        fo.close()
    fout.close()

def baselineWholeDoc():
    D = 3504.0
    tfdf_dic = {}
    #for doc in os.listdir(r'../candidatesortedbytf/'):
    docs_gut = [d for d in os.listdir(r'../candidatesortedbytf/') if not d.startswith('10')]
    for doc in docs_gut:
        print doc
        for line in open(r'../candidatesortedbytf/'+doc).read().strip().split('\n'):
            w,s = line.split(':')
            tf,df,tfidf = s.split()
            tf = int(tf)
            df = int(df)
            tfidf = float(tfidf)
            if w not in tfdf_dic:
                tfdf_dic[w] = [tf,df]
            else:
                tfdf_dic[w][0] += tf
    print 'computing burstiness, gain'
    word_dic = {}
    for w in tfdf_dic:
        tf,df = tfdf_dic[w]
        idf = log(D/df,2)
        bur = tf/(df+0.0)
        ridf = idf + log(1-exp(-tf/D),2)
        n_df = df/D
        gain = n_df*(n_df-1-log(n_df,2))
        word_dic[w] = (tf,df,idf,bur,ridf,gain)
    print 'computing variance'
    var_dic = {}
    #for doc in os.listdir(r'../candidatesortedbytf'):
    for doc in docs_gut:
        for line in open(r'../candidatesortedbytf/'+doc).read().strip().split('\n'):
            w,s = line.split(':')
            tf,df,tfidf = s.split()
            tf = int(tf)
            df = int(df)
            tfidf = float(tfidf)
            if w not in var_dic:
                var_dic[w] = (tf-tfdf_dic[w][0]/D)**2
            else:
                var_dic[w] += (tf-tfdf_dic[w][0]/D)**2
    for w in var_dic:
        var_dic[w] /= D-1
    #f=open(r'../words.baselines','w')
    f = open(r'../words.baselines.gutenburg','w')
    for w in var_dic:
        f.write(w+':'+str(word_dic[w]).strip('()')+', '+str(var_dic[w])+'\n')
    f.close()

def baselineWholeDoc2(start,end):
    #pkl_file = open('words.baseline.pkl','rb')
    #tf_all,df,idf,bur,ridf,gain,var,tf,tfidf
    #w_dic = cPickle.load(pkl_file)
    #pkl_file.close()
    w_dic = {}
    for line in open(r'../words.baselines').read().strip().split('\n'):
        s,w = line.split(':')
        w_dic[s] = [float(i) for i in w.split(', ')]
    print 'out close',len(w_dic)
    while 1:
        continue
    docs = open(r'../candidate.recall.75.100').read().strip().split('\n')[start:end]
    docs = [line.split(':')[0] for line in docs]
    #fout = open(r'../baseline.out'+str(end),'w')
    #docs = ['10.1.1.115.8313.txt','10.1.1.84.419.txt','10.1.1.116.7219.txt']
    for doc in docs:
        print doc
        index_dic = {}
        #k = len(re.split(r'\.\n+',open(r'../tagallbooktxt/'+doc).read().strip()))
        #k = len(open(r'../rank3results/'+doc+'.index').read().strip().split('\n'))
        for line in open(r'../candidatesortedbytf/'+doc).read().strip().split('\n'):
            w,s = line.split(':')
            tf,df,tfidf = [float(i) for i in s.split()]
            index_dic[w] = w_dic[w]+[tf,tfidf]
        #index = open(r'../tagindex/'+doc).read()
        index = open(r'/home/zzw109/project/book/index/'+doc).read().strip()
        #fout.write(doc+': ')
        for k in [133,266,399]:
            for i in range(9):
                tops = []
                if i == 2:
                    tops = sorted(index_dic.items(),key=lambda x:x[1][i])[:k]
                else:
                    tops = sorted(index_dic.items(),key=lambda x:x[1][i],reverse=True)[:k]
                c1,c2 = recall_untag([it[0] for it in tops],index)
                print i,c1,k,c2
                #fout.write(str(i)+':'+str(c1)+','+str(k)+','+str(c2)+';')
        #fout.write('\n')


def baselineBySentence(start,end,baseline):
    docs = open(r'../candidate.recall.75.100').read().strip().split('\n')[start:end]
    docs = [line.split(':')[0] for line in docs]
    fout = open(r'../rank3.out'+str(end),'w')
    for doc in docs:
        print doc
        t = open(r'../tagallbooktxt/'+doc).read()
        sents = re.split(r'_\.\n+',t.strip())
        cands = open(r'../candidate/'+doc).read().strip().split('\n')
        sent_dic,words = {},[]
        tfidf_dic = {}
        for cand in cands:
            w,nums = cand.split(':')
            if len(w)==2 and w[0].isalpha() and re.search('[0-9ijk\.]',w[1]):
                continue
            words.append(w)
            nums = nums.strip('[]').split(', ')
            for num in nums:
                if int(num) in sent_dic:
                    sent_dic[int(num)].append(w)
                else:
                    sent_dic[int(num)] = [w]
        #q_rs = getQueryResults(words,'wiki')
        index_dic = {}
        for i in range(len(sents)):
            if i not in sent_dic:
                continue
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
            #print sents[i]
            for k,score in rank_list[:1]:
                print k,score
                if k not in index_dic:
                    index_dic[k] = [(i,score)]
                else:
                    index_dic[k].append((i,score))
                #f.write(k+':'+str(score)+':'+str(i)+'\n')
        #f.close()
        index = open(r'/home/zzw109/project/book/index/'+doc).read().strip()
        #index = open(r'../tagindex/'+doc).read()
        c1,c2 = recall(index_dic.keys(),index)
        print c1,len(index_dic),c2
        fout.write(doc+':'+str(c1)+':'+str(len(index_dic))+':'+str(c2)+'\n')
        open(r'../rank3results/'+doc+'.index','w').write('\n'.join(k+':'+str(index_dic[k]) for k in index_dic))
    fout.close()

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
        if len(aw)<1 or aw[0] != w[0]:
            continue
        if w == aw:
            return True
        if len(set(w)| set(aw)) >= 2*min(len(w),len(aw)):
            continue
        if len_w/levenshtein(aw,w) > 6:
            return True
    return False
        

def evaluate(doc,index_doc):
    candidate_index_words = [w.lower()[:w.find(':')] for w in open(doc)]
    #candidate_index_words = [w.lower()[1:w.find('\'',1)] for w in open(doc)]
    original_index_list = [re.split(',\s+',line)[0].lower() for line in open(index_doc) if line.find(',')>0]
    recalled_index_words = [w for w in original_index_list if w in candidate_index_words]
    text = open(r'../PRML2LDA.txt').read().lower()
    matched_index = [w for w in original_index_list if re.search(w,text) is not None]
    unmatched_index = [w for w in original_index_list if re.search(w,text) is None]
    missed_index_words = [w for w in matched_index if w not in candidate_index_words]
    fuzzy_missed_index_words = [w for w in candidate_index_words if fuzzy_match(w,missed_index_words)]
    print 'words recalled:',len(recalled_index_words)/(len(matched_index)+0.0)
    print 'index entries matched in text:',len(matched_index)
    print 'missing matched entries:',len(missed_index_words)
    print 'total index entries:',len(original_index_list)
    #print missed_index_words, len(missed_index_words)
    print 'fuzzy_missed_index_words',len(fuzzy_missed_index_words)

def recall_untag(cand,index,multiFlag=False):
    index_words = [line[:line.find(',')].lower() for line in index.split('\n') if len(line)>5 and line.find(',')>=0 and line[0].isdigit() is False ]
    #print index_words
    if multiFlag:
        N = len(index_words)
        recalls = [0]
        for i in range(5):
            recall_words = [w for w in cand[i*N:(i+1)*N] if fuzzy_match(w.lower(),index_words)]
            recalls.append(recalls[-1]+len(recall_words))
        recalls = [float(r)/N for r in recalls[1:]]
        #precision = [recalls[i]/float(i*N)]
        return recalls
    recall_words = [w for w in cand if fuzzy_match(w.lower(),index_words)]
    return recall_words,index_words

def recall(cand,index):
    p = re.compile('([\w\s#%&@\.?]+_[A-Z]+\s(,_,\s\d+_CD)+)',re.I)
    tag_words = [w[0].split(',_,')[0].strip() for w in re.findall(p,index)] 
    index_words = [' '.join(s[:s.rfind('_')] for s in w.split()).lower() for w in tag_words if not w.endswith('_CD')]
    index_text = ' '.join(index_words)
    #recalled_words = [w for w in cand if re.search(w.lower(),index_text) is not None]
    recalled_words = [w for w in cand if fuzzy_match(w.lower(),index_words)]
    #print recalled_words
    return recalled_words,index_words

def testRecall():
    f = open('../candidate.recall.more','w')
    for line in open(r'../linenum.index').read().strip().split('\n')[2482:]:
        id,linenum = line.strip().split(':')
        n1,n2 = linenum.split()
        t = open(r'../tagallbooktxt/'+id).read()
        lines = re.split('\n+',t.replace('\x0c','\n'))
        text = '\n'.join(lines[:int(n1)])
        index = '\n'.join(lines[int(n1):int(n2)+1])
        stopwords = open(r'../StopWords').read().strip().split('\n')
        cw1 = [line.split(':')[0] for line in open(r'../commonwords.1').read().split('\n')[:1000]]
        cw2 = [line.split(':')[0] for line in open(r'../commonwords.2').read().split('\n')[:300]]
        cw3 = [line.split(':')[0] for line in open(r'../commonwords.3').read().split('\n')[:300]]
        cand = getCandidatesBySentence(text,id,stopwords,[cw1,cw2,cw3])
        c1,c2 = recall(cand,index)
        #print id,len(cand),c1,c2
        f.write(id+':'+str(c1)+' '+str(c2)+'\n')
    f.close()

def selectFromRecall():
    f = open(r'../candidate.recall.75.100','w')
    for line in open(r'../candidate.recall'):
        id,num = line.strip().split(':')
        n1,n2 = num.split()
        if int(n2) > 75 and int(n1)/(int(n2)+0.0)>=1:
            f.write(id+':'+n1+' '+n2+'\n')
    f.close()
    
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
    out = [t[0]+'\n'+t[1].strip() for t in terms]
    open(r'../csterms','w').write('\n\n'.join(out))

def candidateWordsClean():
    dic_df = {}
    D = 3504
    #for candfile in os.listdir(r'../candidate'):
    #    for line in open(r'../candidate/'+candfile):
    #        w,s = line.strip().split(':[')
    #        if w in dic_df:
    #            dic_df[w] += 1
    #        else:
    #            dic_df[w] = 1
    for line in open(r'../candidateWords').read().strip().split('\n'):
        w,df = line[:line.rfind(':')],int(line[line.rfind(':')+1:])
        #print w,df
        dic_df[w] = df
    for candfile in [cf for cf in os.listdir(r'../candidate') if not cf.startswith('10')]:
        dic_tf = {}
        print candfile
        for line in open(r'../candidate/'+candfile):
            w,s = line.strip().split(':[')
            tf = len(s.split(', '))
            dic_tf[w] = tf
        s_dic_tf = sorted(dic_tf.items(), key=lambda x:x[1], reverse=True)
        fo = open(r'../candidatesortedbytf/'+candfile, 'w')
        for k,v in s_dic_tf:
            df = 1
            if k in dic_df:
                df = dic_df[k]
            tfidf = v*log(D/(df+0.0),2)
            #print str(tfidf)
            fo.write(k+':'+str(v)+' '+str(df)+' '+str(tfidf)+'\n')
        fo.close()
    #s_dic_df = sorted(dic_df.items(), key=lambda x:x[1], reverse=True)
    #open(r'../candidateWords','w').write('\n'.join([k+':'+str(v) for k,v in s_dic_df]))

def wikiQuery():
    query_list = open(r'../cands2wiki').read().strip().split('\n')[1500000:2000000]
    limit = 50
    ferr = open(r'../querieswitherrors1500000','w')
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

def queryClean():
    #f = open(r'../emptyQueries','w')
    for q in os.listdir(r'../query'):
        if len(open(r'../query/'+q).read()) < 1:
            print q
            os.remove(r'../query/'+q)

def candidate2Wiki():
    f = open(r'../cands2wiki','w')
    for line in open(r'../candidateWords'):
        w,df = line[:line.rfind(':')],line[line.rfind(':')+1:]
        df = int(df)
        if df > 1000 or (w.upper()!=w and len(w)<4):
            continue
        f.write(w+'\n')

def selectBooks():
    f=open(r'../rank3.recall','w')
    c = 0
    for doc in [line.split(':')[0] for line in open(r'../candidate.recall.new').read().strip().split('\n')]:
        print doc
        cands = [line[:line.find(':')] for line in open(r'..rank3results/'+doc+'.index').read().strip().split('\n')]
        index = open(r'../tagindex/'+doc).read()
        x,y= recall(cands,index)
        if y < 50:
            continue
        f.write(doc+':'+str(x)+' '+str(y)+'\n')
        if x/(y+0.0)>0.2:
            c += 1
    f.close()
    print c

def testRank3():
    docs = [line[:line.find(':')] for line in open(r'../rank3.out0to1').read().strip().split('\n')]
    for doc in docs:
        cands = [line[:line.find(':')] for line in open(r'../candidate/'+doc).read().strip().split('\n')]
        #cands = [line[:line.find(':')] for line in open(r'../rank3results/'+doc+'.index').read().strip().split('\n')]
        index = ''
        if os.path.exists(r'/home/zzw109/project/book/index/'+doc):
            index = open(r'/home/zzw109/project/book/index/'+doc).read().strip()
            #index = open(r'../tagindex/'+doc).read().strip()
            print recall_untag(cands[:200],index)
            print recall_untag(cands[:400],index)
            print recall_untag(cands[:800],index)
            print recall_untag(cands,index)
        else:
            index = open(r'../tagindex/'+doc).read().strip()
            print recall(cands[:200],index)
            print recall(cands[:400],index)
            print recall(cands[:800],index)
            print recall(cands,index)

def testBaselines():#tf_all,df,idf,bur,ridf,gain,var,tf,tfidf
    w_dic = {}
    f = open(r'../words.baselines')
    #f = open(r'../words.baselines.gutenburg')
    for line in f.read().strip().split('\n'):
        s,w = line.split(':')
        w_dic[s] = [float(i) for i in w.split(', ')]
    f.close()
    docs = open(r'../goodbooklist').read().strip().split('\n')
    #fout = open(r'../baseline.out'+str(end),'w')
    res = {}
    C = 0
    for doc in docs:
        doc,x,y,z = doc.split(':')
        print doc
        index_dic = {}
        #k = len(re.split(r'\.\n+',open(r'../tagallbooktxt/'+doc).read().strip()))
        #k = len(open(r'../rank3results/'+doc+'.index').read().strip().split('\n'))
        for line in open(r'../candidatesortedbytf/'+doc).read().strip().split('\n'):
            w,s = line.split(':')
            tf,df,tfidf = [float(i) for i in s.split()]
            index_dic[w] = w_dic[w]+[tf,tfidf]
        #index = open(r'../tagindex/'+doc).read()
        if os.path.exists(r'/home/zzw109/project/book/index/'+doc):
            index = open(r'/home/zzw109/project/book/index/'+doc).read().strip()
            C += 1
            for i in [3,4,5,6,8]:
                tops = []
                if i == 2:
                    tops = sorted(index_dic.items(),key=lambda x:x[1][i])
                else:
                    tops = sorted(index_dic.items(),key=lambda x:x[1][i],reverse=True)
                #if i == 8:
                #    open(r'../'+doc+'.tfidf','w').write('\n'.join(t[0] for t in tops))
                r = recall_untag([it[0] for it in tops],index,multiFlag=True)
                if i not in res:
                    res[i]=r
                else:
                    res_i = res[i]
                    res[i]=[r[j]+res_i[j] for j in range(5)]
                print res[i]
                #print i,len(c1),k,len(c2)," $ ",x,y,z
        else:
            continue
            index = open(r'../tagindex/'+doc).read().strip()
            for k in [int(y)]:
                for i in range(9):
                    tops = []
                    if i == 2:
                        tops = sorted(index_dic.items(),key=lambda x:x[1][i])[:k]
                    else:
                        tops = sorted(index_dic.items(),key=lambda x:x[1][i],reverse=True)[:k]
                    c1,c2 = recall([it[0] for it in tops],index)
                    print i,c1,k,c2,'$',x,y,z
    print 'Average Result over', C
    for i in [3,4,5,6,8]:
        res_av = [re/C for re in res[i]]
        print res_av

def testRank3withTfidf():
    docs = open(r'../goodbooklist').read().strip().split('\n')
    #fout = open(r'../baseline.out'+str(end),'w')
    res = [0]*5
    C = 0
    for doc in docs:
        doc,x,y,z = doc.split(':')
        print doc
        if int(y)/int(z)<5:
            continue
        C += 1
        #if doc+'.tfidf' not in os.listdir(r'../'):
        #    continue
        #ws_tfidf = open(r'../'+doc+'.tfidf').read().strip().split('\n')
        ws_rank3 = open(r'../rank3results/'+doc+'.index').read().strip().split('\n')
        rs = [0]
        for i in range(5):
            recalled_rank3 = [line_num for line_num in range(i*int(z),(i+1)*int(z)) if ws_rank3[line_num].startswith('@@@')]
            rs.append(rs[-1]+len(recalled_rank3)/float(z))
        print C,rs
        res1 = res
        res = [rs[j+1]+res1[j] for j in range(5)]
    print [re/C for re in res]
    if 0:
        if os.path.exists(r'/home/zzw109/project/book/index/'+doc):
            index = open(r'/home/zzw109/project/book/index/'+doc).read().strip()
            c1,c2 = recall_untag(ws_tfidf[:int(z)],index)
            c11,c21 = recall_untag(ws_tfidf[:int(z)*2],index)
            print len(c1),z,len(c2)," $ ",len(recalled_rank3),len(recalled_rank3_2),len(Set([w.lower() for w in c1])& Set([w.lower() for w in recalled_rank3])),len(Set([w.lower() for w in c11])& Set([w.lower() for w in recalled_rank3_2]))
        else:
            index = open(r'../tagindex/'+doc).read().strip()
            c1,c2 = recall(ws_tfidf[:int(z)],index)
            print len(c1),z,len(c2),'$',x,z,z


def selectGoodBooks():
    f = open(r'../goodbooklist.550-600-700-750','w')
    for line in open(r'../rank3.out550-600-700-750'):
        id,x,y,z = line.strip().split(':')
        if int(x) > 0 and int(z)/int(x) < 10:
            f.write(line)
    f.close()

def runGutenBurg():
    stopwords = open(r'../StopWords').read().strip().split('\n')
    cw1 = [line.split(':')[0] for line in open(r'../commonwords.1').read().split('\n')[:1000]]
    cw2 = [line.split(':')[0] for line in open(r'../commonwords.2').read().split('\n')[:300]]
    cw3 = [line.split(':')[0] for line in open(r'../commonwords.3').read().split('\n')[:300]]
    doc_dir = r'/home/zzw109/project/bookgen/datasets/BackOfTheBookIndexBenchmark/tagtext'
    for f in os.listdir(doc_dir):
        contextSimilarityRank3(doc_dir+os.sep+f,stopwords,[cw1,cw2,cw3])

def estimateIndexRatio():
    dist = [0]*20
    out = open(r'../IndexRatioDist.txt','w')
    for line in open(r'../goodbooklist').read().strip().split():
        doc,x,y,z = line.split(':')
        num_words = len(re.split('\s+',open(r'/home/zzw109/project/book/allbookstxt/'+doc).read().strip()))
        #print y,num_cands
        #num_tags = len(re.split(r'\s+',open(r'../tagallbooktxt/'+doc).read().strip()))
        #num_sents = len(re.split(r'_\.\n+',open(r'../tagallbooktxt/'+doc).read().strip()))
        #num_cands = len(open(r'../candidate/'+doc).read().strip().split('\n'))
        #print y,num_cands
        r = float(z)/num_words
        dist[int(round(r*1000))] += 1
    out.write(str(dist).strip('[]').replace(', ','\n'))
        #out.write(z+'\t'+str(num_words)+'\t'+str(num_tags)+'\t'+str(num_sents)+'\t'+str(num_cands)+'\n')
    out.close()


if __name__ == "__main__":
    #estimateIndexRatio()
    print datetime.now()
    contextSimilarityRank4(0,30)
    print datetime.now()
    #testRank3withTfidf()
    #selectGoodBooks()
    #testRank3()
    #testBaselines()
    #recall_untag(['www'],open('/home/zzw109/project/book/index/10.1.1.173.5842.txt').read().strip())
    #selectBooks()
    #baselineWholeDoc()
    #contextSimilarityRank3onLargeDataset(750,800)
    #wikiQuery()
    #candidate2Wiki()
    #queryClean()
    #candidateWordsClean()
    #selectFromRecall()
    #extractCSterms()
    #testRecall()
    #evaluate(r'../candidate/PRML',r'../PRML.index')
    #evaluate(r'candidate.out',r'../PRML.index')
    #cmd = "python -m gensim.scripts.make_wikicorpus /home/zzw109/download/enwiki-latest-pages-articles.xml.bz2 /home/zzw109/project/bookgen/gensim/wiki_en"
    #t1 = datetime.now()
    #print t1
    #os.system(cmd)
    ##subprocess.call(cmd)
    #t2 = datetime.now()
    #print t2
    #open('wiki_cost.time','w').write(str(t2-t1))
    #tes#tGensim()
        #print getKScore(s,'Sequential methods','wiki')
    #contextSimilarityRank3(r'../PRML.tag')
    #topicTextRank(open(r'../PRML2LDA.data').read().split('\n')[4])
    #genLDATrainingData()
    #dictGen(5000,6000,'5000-6000.df')
