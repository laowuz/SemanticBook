#! /usr/bin/python
import os

if 1:
    indir = r'../solr_xml'
    outdir = r'../solrxml'
    for xml in os.listdir(indir):
        xml_file = indir+os.sep+xml
        xml_content = open(xml_file).read()
        xml_content = xml_content.replace('&','')
        #xml_content = xml_content.encode('utf-8','ignore')
        open(outdir+os.sep+xml,'w').write(xml_content)
        print xml
while True:
    print "true"

input_file = r'../booksandnumofpages.txt'
file1 = open(r'../40to100.txt','w')
file2 = open(r'../101to200.txt','w')
file3 = open(r'../201to...txt','w')
file4 = open(r'../151to200.txt','w')

lines = open(input_file).read().strip().split('\n')
for line in lines:
    id,num = line.split()
    if 150<int(num)<=200:
        file4.write(line+'\n')
        print line
   # continue
    if int(num)<101:
        file1.write(line+'\n')
    elif int(num)<201:
        file2.write(line+'\n')
    else:
        file3.write(line+'\n')
    print line


