
import os,sys
import subprocess

file = sys.argv[1]
print file
py = r'/home/zzw109/project/pdfminer/tools/pdf2txt.py'
pdf_dir = r'/home/zzw109/project/book/pdfs'
html_dir = r'/home/zzw109/project/book/html'
lines = open(file).read().strip().split('\n')
for line in lines:
    pdf = line.split()[0]
    print pdf
    book = pdf_dir+os.sep+pdf
    html = html_dir+os.sep+pdf+'.html'
    subprocess.call([py,'-o',html,book])
    print html
