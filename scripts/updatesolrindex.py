#! /usr/bin/python

import subprocess,os,re


rep_dir = r'/home/zzw109/citeseerx_repository/rep1/10/1/1/'

url = r'http://localhost:8080/solr1/update?commit=true'

xml_dir0 = r'../solr_xml/'

xml_dir1 = r'../solrxml_fulltext/'

for x in os.listdir(xml_dir0)[34172:]:
    #t = open(xml_dir+os.sep+x).read().replace('&',' ')
    #open(xml_dir+os.sep+x,'w').write(t)
    #subprocess.call(['curl',url,'-H','"Content-Type: text/xml"','--data-binary',t])
    print x
    if x.endswith('xml') is False:
        continue
    t = open(xml_dir0+x).read()
    xs = x.split('.')
    body_f = rep_dir + xs[3]+'/'+xs[4]+'/'+x[:-3]+'body'
    body = ''
    if not os.path.exists(body_f):
        continue
    #body = open(body_f).read().replace('&',' ')
    body = re.sub('[^\w\s]','',open(body_f).read())
    t_new = t[:t.find('</doc>')]+'\n<field name="body">'+body+'</field>\n</doc>\n</add>'
    #subprocess.call('curl '+url+' -H "Content-Type: text/xml" --data-binary \''+t_new+'\'',shell=True)
    fw = open(xml_dir1+x,'w')
    fw.write(t_new)
    fw.close()
