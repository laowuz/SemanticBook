#import urllib.request,json,os,re
#import urllib.error
import urllib2,os,pickle,re
submited = []
candidate = []
ids = []
mykey0 = 'AIzaSyD5gCerVMM0UC6xI9OXIizH2DRY49wayVE'
mykey1 = 'AIzaSyCT75-69Bl2UAJIhFnb3uI7pgH0iiWdzWs'
mykey2 = 'AIzaSyBadhoX9-OYNQ2xJ7XSoo_FVdPp1TWIvIw'
mykey3 = 'AIzaSyA_7vnud69XlFc3mW07TzrXJXO-jmaI2co'
mykey4 = 'AIzaSyC-KZpUbKkz-kMmUyQfhpnMc_a_qZNSmD4'
#parameters = '&filter=free-ebooks&maxResults=40'
url_pre = r'https://www.googleapis.com/books/v1/volumes?q=isbn:'
#bookinfo = open(r'/home/zzw109/project/book/bookinfogoogle.txt','w')
book_isbn = open(r'/home/zzw109/project/book/isbninfo/isbn.all.out').read().strip().split('\n')
query_dir = r'/home/zzw109/project/book/google'
google_dir = r'/home/zzw109/project/book/solr_xml_googlemetadata'
store_dir = r'/home/zzw109/project/book/activelearning'

engine_dic = {'isbnsearch':r'http://www.isbnsearch.org/isbn/','abebooks':r'http://www.abebooks.com/servlet/SearchResults?isbn=','amazon':r'http://www.amazon.com/gp/search/ref=sr_adv_b/?field-isbn=','bookfinder4u':r'http://www.bookfinder4u.com/IsbnSearch.aspx?mode=direct&isbn='}
book_metadata = {'abebooks':{},'isbnsearch':{},'amazon':{},'bookfinder4u':{}}

def googlebookmetadata():
    dic = {}
    for xml in os.listdir(google_dir):
        id = xml[:-4]
        text = open(google_dir+os.sep+xml).read()
        title = re.search(r'<field name="title">(.*?)</field>',text).group(1)
        subtitle = re.search(r'<field name="subtitle">(.*?)</field>',text).group(1)
        if len(subtitle)>0:
            title = title.strip() + ' ' + subtitle
        authors = re.search(r'<field name="authors">(.*?)</field>',text).group(1)
        if len(authors) > 1:
            authors = authors.split(',')
        authors1 = [a.strip() for a in authors]
        dic[id] = (title.strip(),authors1)
    pkl_out = open(store_dir+'/googlemetadata.pkl','wb')
    pickle.dump(dic,pkl_out)
    pkl_out.close()
#googlebookmetadata()

def dicBookLines():
    dic = {}
    text = open(store_dir+r'/booklines4.txt').read().strip()
    p = re.compile(r'/home/zzw109/project/book/pdfs/10.1.1.*\n')
    id_lines = re.findall(p,text)
    book_lines = p.split(text)
    for i in range(len(id_lines)):
        id = re.search(r'/pdfs/(.*?)\.pdf',id_lines[i]).group(1)
        lines = book_lines[i]
        contents = re.compile(r'avgfontsize.*?\n').split(lines)
        features = re.findall(r'avgfontsize.*?\n',lines)
        if len(contents) > 1:
            print id,len(contents),len(features)
            dic[id] = [(contents[i].strip('\n| '),features[i][:-5]) for i in range(len(features))]
    pkl = open(store_dir+r'/dicbooklines.pkl','wb')
    pickle.dump(dic,pkl)
    pkl.close()
#dicBookLines()

def getBookLineFeatures():
    out = open(r'booksneedfeatures.txt','w')
    google_dic = pickle.load(open(store_dir+r'/googlemetadata.pkl','rb'))
    dic_booklines = pickle.load(open(store_dir+r'/dicbooklines.pkl','rb'))
    booklines = {}#for libsvm
    for id in google_dic:
        title,authors = google_dic[id]
        if len(title)<1:
            print id
            continue
        if id in dic_booklines:
            lines = dic_booklines[id]
            y,x = [],[]
            for line in lines:
                content,feature = line
                vect = [float(v) for v in re.findall(r':(-?\d+\.\d+)',feature)]
                content1 = ' '.join(re.sub('[^ \w]','',content.lower()).split())
                title = ' '.join(title.lower().split())
                if title.find(content1) > -1 and len(content1)>2:
                    y.append(1)
                elif len(set(content.split())&set(' '.join(authors).split())) >= len(set(content.split()))/2.0 > 0:
                    y.append(2)
                else:
                    y.append(0)
                x.append(vect)
            booklines[id] = (y,x)
            continue
        out.write(id+'\n')
    pkl = open(store_dir+r'/dicbooklines4libsvm.pkl','wb')
    pickle.dump(booklines,pkl)
    pkl.close()
    print len(booklines)
#getBookLineFeatures()


def truthFinder():
    for engine in engine_dic:
        for book in os.listdir(store_dir+os.sep+engine):
            print book
            s = open(store_dir+os.sep+engine+os.sep+book).read()
            title,authors = '',[]
            if engine == 'abebooks':
                if re.search('sorry|not valid',s):
                    continue
                p_title = r'<h2 class="title"><a  href=".*?"  title="(.*?)">'
                p_author = r'<div class="author"><strong>(.*?)</strong>'
                #p_isbn = r'<div class="isbn">ISBN: <a href=.*?>(.*?)</a> / <a href=.*?>(.*?)</a>'
                title = re.search(p_title,s).group(1)
                authors = re.search(p_author,s).group(1).strip().split(';')
            if engine == 'isbnsearch':
                if re.search('Invald|Sorry',s):
                    continue
                title = re.search(r'<title>(.*?)</title>',s).group(1).split(' | ')[1]
                s_author = re.search(r'<p><strong>Authors?:</strong>(.*?)</p>',s)
                if s_author is not None:
                    authors = s_author.group(1).strip().split(';')
            if engine == 'amazon':
                if (s.find('did not match')>=0):
                    continue
                title = re.search(r'<div class="productTitle"><a href=".*?">(.*?)</a> ',s)
                if title is None:
                    continue
                title = title.group(1)
                s_author = re.search(r'<span class="ptBrand">(.*?)</span>',s)
                if s_author is not None:
                    s_author = re.sub('</a>|by|<a.*?>','',s_author.group(1))
                    pp = re.compile('\sand\s|,&#32;|,')
                    authors = pp.split(s_author)
            if engine == 'bookfinder4u':
                if re.search('be found|Format Error',s):
                    continue
                authors = re.findall(r'<a href="/search_author/.*?">(.*?)</a>',s)
                title = re.search(r'<title>BookFinder4u\s\-\s(.*?),\sISBN.*?</title>',s).group(1)
            authors1 = []
            if len(authors)>0:
                authors1 = [a.strip() for a in authors]
            book_metadata[engine][book[:book[:-6].rfind('.')]]=(title.strip(),authors1)
    pkl_out = open(store_dir+'/bookmetadata.pkl','wb')
    pickle.dump(book_metadata,pkl_out)
    pkl_out.close()
        

#truthFinder()
def queryByISBN(bookid,engine,isbn):#for other book engines
    url = engine_dic[engine]+isbn
    print(url)
    #req = urllib.request.urlopen(url)
    #encoding = req.headers.get_content_charset()
    #text = req.read().decode(encoding)
    req = urllib2.urlopen(url)
    text = req.read()
    req.close()
    f=open(store_dir+r'/'+engine+r'/'+bookid+'.'+engine+'.html','w')
    f.write(text)
    f.close()



def query(bookid,q,mykey):#for Google book
    url = url_pre+q+'&key='+mykey
    print (url)
    req = urllib2.urlopen(url)
    #encoding = req.headers.get_content_charset()
    #print(encoding)
    #except urllib.error.HTTPError:
    #    print ('HTTPError')
    text = req.read()
    req.close()
    open(query_dir+r'/'+bookid+'.json','w').write(text)

def writeXML(indir,outdir):
    for f in os.listdir(indir):
        if f.startswith('10.1.1.') is not True:
            continue
        js = json.loads(open(indir+os.sep+f).read())
        if js['totalItems']<1:
            continue
        gid = js['items'][0]['id']
        info = js['items'][0]['volumeInfo']
        title = info['title'] if 'title' in info.keys() else 'untitled'
        subtitle = info['subtitle'] if 'subtitle' in info.keys() else ''
        authors = info['authors'] if 'authors' in info.keys() else []
        date = info['publishedDate'] if 'publishedDate' in info.keys() else ''
        isbn = info['industryIdentifiers'] if 'industryIdentifiers' in info.keys() else []
        isbn_str = ''
        if len(isbn)>0:
            isbn_str = isbn[0]['type']+':'+isbn[0]['identifier']
        if len(isbn)>1:
            isbn_str = isbn_str + ', ' + isbn[1]['type']+':'+isbn[1]['identifier']
        fw = open(outdir+os.sep+f[:-5]+'.xml','w')
        fw.write('<add>\n  <doc>\n')
        fw.write('  <field name="id">'+f[:-5]+'</field>\n')
        fw.write('  <field name="title">'+title.replace('&',' ')+'</field>\n')
        fw.write('  <field name="subtitle">'+subtitle.replace('&', ' ')+'</field>\n')
        fw.write('  <field name="authors">'+','.join(authors).replace('&',' ')+'</field>\n')
        fw.write('  <field name="publishDate">'+date+'</field>\n')
        fw.write('  <field name="googleid">'+gid+'</field>\n')
        fw.write('  <field name="isbn">'+isbn_str+'</field>\n')
        if f[:-5]+'.xml' in os.listdir(r'../solrxml'):
            print (f[:-5])
            txt = open(r'../solrxml/'+f[:-5]+'.xml').read()
            fs = re.findall('<field name="contents">.*?</field>|<field name="chapter_title">.*?</field>',txt,re.S)
            s1,s2 = '<field name="contents">', '<field name="chapter_title">'
            for f in fs:
                if f.startswith(s1):
                    fw.write(s1+re.sub('[<>&]',' ',f[len(s1):-8])+'</field>')
                if f.startswith(s2):
                    fw.write(s2+re.sub('[<>&]',' ',f[len(s2):-8])+'</field>')
        fw.write('  </doc>\n</add>\n')
        fw.close()
from datetime import datetime,timedelta
time={}
for i in range(1):
    for eng in book_metadata:
        if eng =='bookfinder4u':
            continue
        t0 = datetime.now()
        queryByISBN('10.1.1.134.2057',eng,'0321445619')
        t = datetime.now() - t0
        if eng not in time:
            time[eng] = t
        else:
            time[eng]+=t
print time
T = timedelta(0,0,0)
for i in range(10):
    t0 = datetime.now()
    query('10.1.1.134.2057','0321445619',mykey0)
    t = datetime.now() - t0
    T += t
print T



#writeXML(query_dir,google_dir)
if 0:
    count = 0
    keys = [mykey0,mykey1,mykey2,mykey3,mykey4]
    for it in book_isbn:
        bookid,isbn = it.split(':')[0],it.split(':')[1]
        print(bookid, isbn)
        if bookid+'.json' in os.listdir(query_dir):
            continue
        #query(bookid,isbn)
        try:
            query(bookid,isbn,keys[int(count/1000)])
            count = count + 1
        except (UnicodeEncodeError, urllib.error.HTTPError):
            print('Error')
            continue
if 0:
    t1 = open(r'../isbn.html.out').read().strip().split('\n')
    l1 = len(t1)
    t2 = open(r'../isbn.txt.out').read().strip().split('\n')
    for t in t2:
        if t not in t1:
            t1.append(t)
    if len(t1)>l1:
        print (len(t1),l1)
        open(r'../isbn.all.out','w').write('\n'.join(t1))

    c = 0
    engine = 'amazon'
    for it in book_isbn:
        bookid,isbn = it.split(':')[0],it.split(':')[1]
        print(bookid,isbn,c)
        try:
            queryByISBN(bookid,engine,isbn.replace('-',''))
            c += 1
        except:
            print('error')
            continue
