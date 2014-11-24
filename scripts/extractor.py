#! /usr/bin/python
#-*- coding: utf-8 -*-
import os,re,sys,time
import ToCdetection
from xml.dom.minidom import parseString
class BookChapter:
  def __init__(self, number, title, page_no, start_line):
    self.chapter_number = number
    self.title = title
    self.page_number = page_no
    self.start_line = start_line
    self.subchapters = []
    self.pre_chapter = None
    self.next_chapter = None

  def setPreChapter(self, pre):
    self.pre_chapter = pre

  def setNextChapter(self, next):
    self.next_chapter = next

  def addSubchapter(chapter):
    self.subchapters.append(chapter)


class BookDoc:
  def __init__(self, file_name, doc_path, xml_path, ref_dir=""):
    self.file_name = file_name
    self.file_path = doc_path+os.sep+file_name
    self.text = open(self.file_path).read()
    #self.xml_dom = parseString(open(xml_path+os.sep+file_name.replace('txt','xml')).read())
    self.lines = re.split('\n+',self.text.replace('\x0c','\n'))
    self.ToC = ToCdetection.ToC_detection(self.file_path)
    self.chapters = []
    self.dic_chapter = {}
    self.title = ""
    self.authors = []
    self.ISBN = []
    self.refs = []
    self.refs_dir = ref_dir

  def getRefs(self):
      ref_marks = re.compile('^References?:?|^Bibliography:?|^Sources:?',re.I)
      start_line = 100
      for line in range(start_line,len(self.lines)):
          s = re.search(ref_marks,self.lines[line]) 
          if s is not None:
              if s.group() == s.string:
                  start_line = line
                  i = start_line
                  print 'start line:',i,self.lines[start_line]
                  nonehits = 0
                  id = 1
                  while i < len(self.lines):
                      if re.search('^(\['+str(id)+'\]|'+str(id)+'\.\s|'+str(id)+'\s)',self.lines[i]) is not None:
                          if re.split('\s+',self.lines[i])>5:
                              self.refs.append(i)
                              nonehits = 0
                              id = id + 1
                          # elif re.search('[A-Z][a-z]+',self.line[i]) is not None:
                      else:
                          nonehits = nonehits + 1
                      if nonehits > 30:
                          print 'end of ref'
                          break
                      i = i + 1
      print 'num of refs:',len(self.refs)
      return self.refs

  def writeRefs(self):
      refs = self.getRefs()
      if len(refs) == 0:
          return 0
      ref_file = self.refs_dir + os.sep + self.file_name
      f_ref = open(ref_file,'w')
      if len(refs) == 1:
          f_ref.write(' '.join(self.lines[refs[0]:refs[0]+5]))
          return 1
      for i in range(len(refs)-1):
          ref_item = ' '.join(self.lines[refs[i]:refs[i+1]])
          f_ref.write(ref_item+'\n\n')
      f_ref.write(' '.join(self.lines[refs[-1]:refs[-1]+5]))
      f_ref.close()
      return len(refs)
   
  def getToC(self):
    toc,toc_begin,toc_end = self.ToC
    return toc
  def getChapters(self):
    return self.chapters
 
  def getHierachy(self):
    if self.ToC is None:
      return False
    toc,toc_begin,toc_end = self.ToC
    i = 0
    start_line_number = toc_end+1
    for i in range(0,len(toc)):
      words = re.split('\W+',toc[i])
      if len(words) < 3:
        continue
      if len(words) == 3:
        if words[0].isdigit() and words[1].isdigit() and words[2].isdigit() and i < len(toc)-1:
          if len(toc[i+1])<2 or re.split('\W+',toc[i+1])[0].isdigit():
            continue
      if words[0].isdigit():
        if words[-1].isdigit() is False and i < len(toc)-1:
          if re.split('\W+',toc[i+1])[-1].isdigit() and len(toc[i+1])>2:
            words.extend(re.split('\W+',toc[i+1]))
        #print words
        chapter_number = words[0]
        page_number = words[-1]
        title = words[1:-1]
        if words[1].isdigit():
          chapter_number = chapter_number+'.'+words[1]
          title = words[2:-1]
          if words[2].isdigit():
            chapter_number = chapter_number+'.'+words[2]
            title = words[3:-1]
            if words[3].isdigit():
              chapter_number = chapter_number+'.'+words[3]
              title = words[4:-1]
        line_number = self.searchChapter(toc[i], start_line_number)
        if line_number > start_line_number:
          start_line_number = line_number+1
          chapter = BookChapter(chapter_number, ' '.join(title), page_number, line_number)
          self.chapters.append(chapter)
          self.dic_chapter[chapter_number] = chapter
         # print chapter_number
    return True

  def searchChapter(self, title, start_line):
    i = start_line
    words = []
    title = title.lower()
    f = title.find(' ')
    number = title[0:f]
    if number.endswith('.'):
      number = number[0:-1]
    words.append(number)
    words.extend(re.split('\W+',title[f+1:-1])[0:-1])
    #print i,words
    ff = 0
    while i < len(self.lines)-1:
      l = self.lines[i].lower()
      ff = l.find(words[0])
      if ff >= 0:
        l = l+self.lines[i+1].lower()
        c = 0
        for w in words[1:len(words)]:
          f1 = ff
          ff = l.find(w,f1)
          if ff > f1:
            c = c+1
        if c >= len(words)/2:
          #print "line:",i
          return i
      i = i + 1
    return -1
    
  def writeXML(self,xml_dir):
    fw = open(xml_dir+os.sep+self.file_name[:-3]+r'xml','w')
    fw.write('<add>\n  <doc>\n')
    fw.write('  <field name="id">'+self.file_name.strip('txt')+'</field>\n')
    if self.title != "":
        t = self.title.encode('utf-8')
        t = t.replace('&','')
        fw.write('  <field name="title">'+t+'</field>\n')
    if self.ISBN != "":
        fw.write('  <field name="ISBN">'+self.ISBN+'</field>\n')
    if len(self.authors)>0:
        fw.write('  <field name="authors">'+str(self.authors)+'</field>\n')
    if self.ToC is not None:
        toc,l1,l2 = self.ToC
        if len(toc)>0:
            fw.write('  <field name="contents">'+'\n'.join(toc)+'</field>\n')
    j = 0
    for j in range(len(self.chapters)):
      chapter = self.chapters[j]
      #print chapter.start_line, chapter.page_number, chapter.chapter_number,chapter.title
      fw.write('  <field name="chapter_title">')
      fw.write(chapter.chapter_number+' '+chapter.title+'</field>\n')
      #if j < len(self.chapters)-1:
       # fw.write('\n'.join(self.lines[chapter.start_line:self.chapters[j+1].start_line]))
      #else:
       # fw.write('\n'.join(self.lines[chapter.start_line:-1]))
      j = j + 1
    fw.write('  </doc>\n</add>\n')

  def getCiatations(self):
    #simply extract the ciations from citeseer xml
    return ''
  def getAuthors(self):
    #extract the authors from citeseer xml
    nodes = self.xml_dom.getElementsByTagName('authors')[0].childNodes
    if len(nodes) == 0:
        return self.authors
    authors = []
    for node in nodes:
      author_name = node.getElementsByTagName('name')[0].childNodes[0].data
      affil = node.getElementsByTagName('affil')[0].childNodes[0].data
      authors.append((author_name,affil))
    self.authors = authors
    return self.authors
  def getAbstract(self):
    return self.xml_dom.getElementsByTagName('abstract')[0].childNodes[0].data
  
  def getIndex(self):
      p_index = re.compile('index\s*|numbers?|\w+,\s([A-Z]-)?\d+',re.I)
      p_num = re.compile('\d{1,6}')
      index_path = r'/home/zzw109/project/book/index/'
      if os.path.exists(index_path+self.file_name) is True:
          return 0
      end_line = len(self.lines)
      start_line = 3*end_line/4
      c1,c2 = 0,0
      line_i = start_line
      for line in self.lines[start_line:]:
          if len(line) <1:
              continue
          s1 = re.search(p_index,line)
          #s2 = re.search(p_num,line)
          words = re.split(',?\s*',line.strip())
          num_words = len(words)
          if s1 is not None and num_words < 3:
              index_entry_num = 0
              for entry in self.lines[line_i:line_i+20]:
                  ws = re.split(',\s*',entry)
                  if 1<len(ws)<10 and entry[0] in ['a','A'] and entry[-1].isdigit():
                      index_entry_num = index_entry_num + 1
              if index_entry_num > 3:
                  print self.lines[line_i:line_i+10]
                  open(index_path+self.file_name,'w').write('\n'.join(self.lines[line_i:]))
                  return line_i
          line_i = line_i + 1
      return 0

  def getISBN(self):
      p_isbn10 = re.compile('i\s?s\s?b\s?n(10|[\s-]10)?[:-]?[\s]{0,5}([\dx-]{13})',re.I)
      p_isbn13 = re.compile('i\s?s\s?b\s?n(13|[\s-]13)?[:-]?[\s]{0,5}([\dx-]{17})',re.I)
      end_line = min(len(self.lines)/10,1000)
      for line in self.lines[0:end_line]:
          line = line.replace('–','-')
          r1 = re.search(p_isbn10,line)
          r2 = re.search(p_isbn13,line)
          if r2 is not None:
           self.ISBN.append(r2.group(2))
           if r1 is not None:
               if len(self.ISBN) == 0:
                   self.ISBN.append(r1.group(2))
               elif self.ISBN[0].startswith(r1.group(2)):
                   return self.ISBN
               else:
                   self.ISBN.append(r1.group(2))
      return self.ISBN

  def getTitl(self):
      nodes = self.xml_dom.getElementsByTagName('title')[0].childNodes
      if len(nodes) > 0:
          self.title = nodes[0].data
      return self.title
  def getPublisher(self):
     # return self.xml_dom.getElementsByTagName('')
    return ''

if __name__ == "__main__":
    home_dir = r'/home/zzw109/project/book'
    books = open(home_dir+os.sep+'numofpages/101to...txt').read().strip().split('\n')
    book_txt = [book.split()[0].replace('pdf','txt') for book in books]
    base_dir = r'/home/zzw109/project/book'
    txt_dir = r'/home/zzw109/project/book/allbookstxt'
    xml_dir = r'/home/zzw109/project/book/xml'
    ref_dir = base_dir + os.sep + 'references'
    isbnout = open(base_dir + os.sep + 'isbn.txt.out','w')
    #txt = "10.1.1.115.1881.txt"
    #bk = BookDoc(txt, txt_dir, xml_dir, ref_dir)
    #bk.getIndex()
    for txt in book_txt:
        print txt
        bk = BookDoc(txt, txt_dir, xml_dir, ref_dir)
        bk.getIndex()
        #bk.writeRefs()
        #isbn = bk.getISBN()
       # if len(isbn)==0:
       #     print 'Donot find ISBN'
       #     continue
       # print txt[:-4],isbn
       # isbnout.write(txt[:-4]+':'+isbn[0]+'\n')
    #isbnout.close()


#    while True:
#        continue
#
##print ToCdetection.ToC_detection(r'/home/zzw109/project/book/test/10.1.1.193.87.txt')//TOC extraction incorrect!!!
#testfile = sys.argv[1]#r'10.1.1.100.4312.txt'
#base_dir = r'/home/zzw109/project/book'
#txt_dir = r'/home/zzw109/project/book/allbookstxt'
#xml_dir = r'/home/zzw109/project/book/xml'
#solr_xml_dir = base_dir+os.sep+'solr_xml'
#book = BookDoc(testfile, txt_dir, xml_dir)
#print book.getRefs()
##print book.getTitle()
##print book.getAuthors()
##book.getHierachy()
#while True:
#  continue
#f = sys.argv[1]
#lines = open(r'/home/zzw109/project/book'+os.sep+f).read().strip().split('\n')
#for line in lines:
#    if not os.path.exists(xml_dir+os.sep+line.split()[0][:-3]+'xml'):
#        continue
#    txt = line.split()[0][:-3]+'txt'
#    print txt
#    try:
#        book = BookDoc(txt, txt_dir, xml_dir)
#        book.getHierachy()
#        book.getTitle()
#        #book.getAuthors()
#        book.getISBN()
#    except IndexError,IOError:
#        print "Index error or IOErr"
#        continue
#    book.writeXML(solr_xml_dir)
