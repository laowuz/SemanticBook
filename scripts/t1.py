#! /usr/bin/python

import os

list1 = [f[:-5] for f in os.listdir(r'../html')]

list2 = open(r'../201to...txt').read().strip().split('\n')
list3 = open(r'../151to200.txt').read().strip().split('\n')
f = open(r'../201to...new','w')
f1 = open(r'../151to200.new','w')
i = 0
for it in list2:
    if it.split()[0] not in list1:
        f.write(it.split()[0]+'\n')
        i = i + 1
for it in list3:
    if it.split()[0] not in list1:
        f1.write(it.split()[0]+'\n')
        i = i + 1

f1.close()
f.close()
print len(list1),i,len(list2)+len(list3)
