import urllib.request,json
import urllib.error
seeds = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
submited = []
candidate = []
ids = []
mykey = 'AIzaSyD5gCerVMM0UC6xI9OXIizH2DRY49wayVE'
parameters = '&filter=free-ebooks&maxResults=40'
url_pre = r'https://www.googleapis.com/books/v1/volumes?q='
file_id_f = open(r'/home/zzw109/project/book/googleid.txt','a')
query_dir = r'/home/zzw109/project/book/google'

def query(q):
    url = url_pre+q+'&filter=free-ebooks&key='+mykey+parameters
    print (url)
    req = urllib.request.urlopen(url)
    encoding = req.headers.get_content_charset()
    #print(encoding)
    #except urllib.error.HTTPError:
    #    print ('HTTPError')
    text = req.read().decode(encoding)
    open(query_dir+r'/'+q+'.json','w').write(text)
    submited.append(q)
    js = json.loads(text)
    for item in js['items']:
        id = item['id']
        if id not in ids:
            ids.append(id)
            file_id_f.write(id+'\n')
            print(id)
        words = []
        if 'title' in item['volumeInfo'].keys():
            title = item['volumeInfo']['title'].split()
            words.extend(title)
        if 'authors' in item['volumeInfo'].keys():
            authors = ' '.join(item['volumeInfo']['authors']).split()
            words.extend(authors)
        if 'description' in item['volumeInfo'].keys():
            description = item['volumeInfo']['description'].split()
            words.extend(description)
        for w in words:
            if w not in candidate:
                candidate.append(w)


for q in seeds:
    try:
        query(q)
    except (UnicodeEncodeError, urllib.error.HTTPError):
        print('Error')
        continue
while len(candidate):
    q = candidate[0]
    del candidate[0]
    if q.isalnum() is False:
        continue
    try:
        query(q)
    except (UnicodeEncodeError,urllib.error.HTTPError):
        print ('Error')
        continue
    print(len(ids))




