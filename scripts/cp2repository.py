#! /usr/bin/python

import os
import subprocess

dic = {}
for pdf in os.listdir(r'./pdfs/'):
  i = int(pdf.split('.')[-3])
  if i not in range(140,156):
    continue
  subprocess.call(['cp','./pdfs/'+pdf,'./repository/'+str(i)])
  if i not in dic.keys():
    dic[i] = 1
  else:
    dic[i] = dic[i] + 1

print str(dic)
