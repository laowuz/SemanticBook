#! /user/bin/python
#-*- coding: utf-8 -*-
import os,re
from auto_indexer_experiments import fuzzy_match
from shutil import copy2

def recall(cands,index_words,N=0):
    if N > 0:
        recalls = [0]
        for i in range(5):
            recall_words = [w for w in cands[i*N:(i+1)*N] if fuzzy_match(w.lower(),index_words)]
            recalls.append(recalls[-1]+len(recall_words))
        recalls = [float(r)/N for r in recalls[1:]]
        #precision = [recalls[i]/float(i*N)]
        return recalls
    recall_words = [w for w in cands if fuzzy_match(w.lower(),index_words)]
    return recall_words


def recall_by_file(input_index,groundtruth_index,flag=False):
    lines = open(input_index).read().strip().split('\n')
    cands = [line[:line.find(':')] for line in lines]
    index = open(groundtruth).read().strip().split('\n')
    index_words = [w.lower() for w in index]
    if flag:
        print len(cands),len(index_words)
        return recall(cands,index_words,len(index_words))
    return recall(cands,index_words),index_words

def testBaselines():#tf_all,df,idf,bur,ridf,gain,var,tf,tfidf
    w_dic = {}
    f = open(r'../words.baselines.gutenburg')
    for line in f.read().strip().split('\n'):
        s,w = line.split(':')
        w_dic[s] = [float(i) for i in w.split(', ')]
    f.close()
    res = {}
    C = 0
    home = r'/home/zzw109/project/bookgen/datasets/BackOfTheBookIndexBenchmark'
    for doc in [d for d in os.listdir(r'../candidatesortedbytf') if not d.startswith('10')]:
        index_dic = {}
        print doc
        for line in open(r'../candidatesortedbytf/'+doc).read().strip().split('\n'):
            w,s = line.split(':')
            tf,df,tfidf = [float(i) for i in s.split()]
            index_dic[w] = w_dic[w]+[tf,tfidf]
        index_file = home+r'/index/'+doc[:doc.rfind('.')]+'.index.trimmed'
        if os.path.exists(index_file):
            C += 1
            index_words = open(index_file).read().strip().split('\n')
            for i in [3,4,5,6,8]:
                tops = sorted(index_dic.items(),key=lambda x:x[1][i],reverse=True)
                #print tops[:10],index_words[:10]
                r = recall([it[0] for it in tops],[iw.lower() for iw in index_words],len(index_words))
                print r
                if i not in res:
                    res[i] = r
                else:
                    res_i = res[i]
                    res[i] = [r[j]+res_i[j] for j in range(5)]
    for i in [3,4,5,6,8]:
        print [re/C for re in res[i]]

def testRank3():
    home = r'/home/zzw109/project/bookgen/datasets/BackOfTheBookIndexBenchmark'
    res = [0]*5
    C = 0
    for doc in os.listdir(home+os.sep+'rank3results'):
        print doc
        cands = [line[:line.find(':')] for line in open(home+r'/rank3results/'+doc).read().strip().split('\n')]
        index_file = home+r'/index/'+doc[:doc.find('.')]+'.index.trimmed'
        if os.path.exists(index_file):
            C += 1
            index_words = open(index_file).read().strip().split('\n')
            r = recall(cands,[iw.lower() for iw in index_words],len(index_words))
            print r
            res1 = res
            res = [r[j]+res1[j] for j in range(5)]
    print [re/C for re in res]

def copyindex():
    home = r'/home/zzw109/project/bookgen/datasets/BackOfTheBookIndexBenchmark'
    for dir in os.listdir(home+os.sep+'corpus'):
        for f in os.listdir(home+os.sep+'corpus'+os.sep+dir):
            if f.endswith('index'):
                try:
                    copy2(home+'/corpus/'+dir+os.sep+f,home+os.sep+'index'+os.sep+f)
                except:
                    continue
    for f in os.listdir(home+'/corpus/LOCCcategories/Zen'):
        if f.endswith('index'):
            copy2(home+'/corpus/LOCCcategories/Zen/'+f,home+os.sep+'index'+os.sep+f)
    for d in os.listdir(home+'/corpus/LOCCcategories/Science'):
        for f in os.listdir(home+'/corpus/LOCCcategories/Science/'+d):
            if f.endswith('index'):
                copy2(home+'/corpus/LOCCcategories/Science/'+d+os.sep+f,home+os.sep+'index'+os.sep+f)


def statistics():
    dir = r'/home/zzw109/project/bookgen/datasets/BackOfTheBookIndexBenchmark/text'
    dir1 = r'/home/zzw109/project/bookgen/datasets/BackOfTheBookIndexBenchmark/tagtext'
    n_words,n_context,n_tagcontext = 0, 0,  0
    for txt in os.listdir(dir):
        t = open(dir+os.sep+txt).read().strip()
        t1 = open(dir1+os.sep+txt).read().strip()
        n_words += len(re.split('\s+',t))
        n_context += len(re.split('[\.\?\!]\n+',t))
        n_tagcontext += len(re.split('_\.\n+',t1))
    print n_words,n_context,n_tagcontext



if __name__ == '__main__':
    statistics()
    #copyindex()
    #testRank3()
    #home = r'/home/zzw109/project/bookgen/datasets/BackOfTheBookIndexBenchmark'
    #input = home+r'/tagtext/The Explorers of Australia and their.text.indexbyRank3'
    #groundtruth = home+r'/corpus/Geography/'+r'The Explorers of Australia and their.index.trimmed'
    #x,y=recall_by_file(input,groundtruth)
    #print len(x),len(y)
    #print recall_by_file(input,groundtruth,True)
