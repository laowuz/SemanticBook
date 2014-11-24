#! /usr/bin/python

import os,subprocess

from pdfminer.pdfparser import PDFParser, PDFDocument, PDFSyntaxError, PDFEncryptionError
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.layout import LAParams
from pdfminer.converter import PDFPageAggregator
from pdfminer.psparser import PSSyntaxError,PSEOF

def get_number_of_pages(pdf):
    fp = open(pdf,'rb')
    parser = PDFParser(fp)
    doc = PDFDocument()
    parser.set_document(doc)
    doc.set_parser(parser)
    doc.initialize('')
    if not doc.is_extractable:
        print 'not extractable'
        return -1
       # raise PDFTextExtractionNotAllowed
   # mgr = PDFResourceManager()
   # device = PDFDevice(mgr)
   # interpreter = PDFPageInterpreter(mgr, device)
    c = 0
    for page in doc.get_pages():
        # interpreter.process_page(page)
        c = c+1
    return c

ids = open(r'/home/zzw109/project/book/booksmorethan40pages.txt').read().strip().split()
out = open(r'/home/zzw109/project/book/booksandnumofpages.txt','w')
pdf_dir = r'/home/zzw109/project/book/pdfs'
c = 0
for id in ids:
    c = c+1
    pdf = pdf_dir+os.sep+id
    try:
        num = get_number_of_pages(pdf)
        out.write(id+'\t'+str(num)+'\n')
        print id,num,c
    except (RuntimeError,PDFSyntaxError,TypeError,PSSyntaxError,PDFEncryptionError,ValueError,KeyError,PSEOF):
        continue



if 0:
    f = open(r'/home/zzw109/project/book/books40pages140-157.txt','w')
    pdf_dir = r'/home/zzw109/project/book/repository'
    for dir in range(140,157):
        for pdf in os.listdir(pdf_dir+os.sep+str(dir)):
            print pdf
            if not pdf.endswith('.pdf'):
                continue
            try:
                if get_number_of_pages(pdf_dir+os.sep+str(dir)+os.sep+pdf) >= 40:
                    f.write(pdf+'\n')
            except (RuntimeError,PDFSyntaxError,TypeError,PSSyntaxError,PDFEncryptionError,ValueError,KeyError,PSEOF):
                continue
       
#pdf = r'/home/zzw109/project/book/goodbooks/10.1.1.115.2797.pdf'
#print(get_number_of_pages(pdf))

#outlines = doc.get_outlines()
#fh = open('toc.txt','w')
#for line in outlines:
#    print line
#    fh.write(str(line)+'\n')

if 0:
    for f in os.listdir(r'/home/zzw109/project/book/intech'):
        if f.endswith('.zip'):
            print f
    subprocess.call('unzip',f)
if 0:
	pre_url = r'http://books.google.com/ebooks?id='
	ids = open(r'/home/zzw109/project/book/googleid.txt').read().split()
	urls = [pre_url+bookid for bookid in ids]
	open(r'/home/zzw109/project/book/freebooksulrs.txt','w').write('\n'.join(urls))
