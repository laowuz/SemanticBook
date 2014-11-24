import urllib2,os

dir = r'/home/zzw109/project/book/structureextraction/'
url_100 = dir + r'groundtruth100/' + r'100_books.txt'
url_2011 = dir + r'groundtruth2011/' + r'2011_books.txt'
url_2009 = dir + r'groundtruth2009/' + r'2009_books.txt'

for line in open(url_2009):
    print line
    u = line.split()[1][:-4]+'_djvu.xml'
    req = urllib2.urlopen(u)
    content = req.read()
    req.close()
    f = open(dir+r'groundtruth2009/'+u[u.rfind(r'/')+1:],'w')
    f.write(content)
    f.close()
