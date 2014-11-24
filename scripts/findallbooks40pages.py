#!/usr/bin/python

import os


id_list = []
dir = r'/home/zzw109/project/book'
dir1 = dir+os.sep+'numofpages'
c = 0
for f in os.listdir(dir1):
    ids = open(dir1+os.sep+f).read().strip().split()
    for id in ids:
        if id not in id_list:
            id_list.append(id)
            c = c+1
            print id,c

out = dir+os.sep+'booksmorethan40pages.txt'
open(out,'w').write('\n'.join(id_list))

