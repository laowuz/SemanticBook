#! /usr/bin/python
import urllib2,re,os,time,random

#get books from intechopen

url = r'http://www.gutenberg.org/ebooks/search/?sort_order=downloads&start_index=151'
opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]
t=opener.open(url).read().replace('\n','')
links = re.findall('<li class="booklink">.*?</li>', t)
for link in links:
    id = re.search('href="/ebooks/(\d+)"', link).group(1)
    title = re.search('<span class="title">(.*?)</span>', link).group(1)
    print id, title
    if os.path.exists(r'../gutenberg/'+title.strip()+'.txt'):
        continue
    try:
        text = opener.open(r'http://www.gutenberg.org/ebooks/'+id+'.txt.utf-8').read()
        open(r'../gutenberg/'+title.strip()+'.txt','w').write(text)
    except:
        print 'error'
        continue
    time.sleep(10+random.randint(1,20))

if 0:
    url_pre = r'http://www.intechopen.com/source/finals/'
    for i in range(1,300):
        url = url_pre + str(i)+'/'+str(i)+'.zip'
        print url
        try:
            q = urllib2.urlopen(url)
            fn = r'/home/zzw109/project/book/intech'+os.sep+str(i)+'.zip'
            open(fn,'wb').write(q.read())
        except urllib2.HTTPError:
            print 'HTTPError'
            continue

if 0:
    url_pre = r'http://www.intechweb.org/books/az/page/'
    page_num_range = range(1,116)
    f = open(r'd:/intechbooks.txt','w')
    for i in page_num_range:
        t = urllib2.urlopen(url_pre + str(i)).read()
        books = re.findall('<a class="title".*?</p>',t,re.DOTALL)
        for book in books:
            f.write(book+'\n####\n')




            
        


    
    
    
