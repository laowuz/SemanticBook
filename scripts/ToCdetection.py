#! /usr/bin/python

import re
import os
from datetime import datetime,timedelta

ToC_txt_dir = r'./allbookstxt'
ToC_dir = r'./toc'
log_file = r'./log.txt'
range1 = range(1,194)
range2 = range(1,10000)
begin_patterns = ['CONTENTS','Contents','TABLE OF CONTENTS','Table of contents']
#specail_patterns = ['Check List','Text Subjects','Contents of ...']

def exists_larger_number(lines,max_num):
    for line in lines:
        if len(line) == 0:
            continue
        if line[-1] in [str(k) for k in range(10)]:
            num = int(re.split('\D+',line)[-1])
            if num >= max_num and num-max_num<1000:
                return True
    return False
def exists_larger_number2(lines,max_num):
    for line in lines:
        if len(line) == 0:
            continue
        if line[0] in [str(k) for k in range(10)]:
            num = int(re.split('\D+',line)[0])
            if num >= max_num:
                return True
    return False

def have_similar_format(lines,line):
    s1 = re.split('\D+',line)
    for l in lines:
        if len(line) == 0:
            continue
        s2 = re.split('\D+',l)
        if s1[-1].isdigit() == s2[-1].isdigit() and s1[0].isdigit() == s2[0].isdigit():
            return True
    return False
    
        

def ToC_detection(f):
    #print f
    lines = open(f).read().replace('\x0c','\n').split('\n')
    first_lines = lines[0:len(lines)/5]
    begin_line = 0
    end_line = len(first_lines)
    max_num_lines = 1200
    for i in range(0,end_line):
        for pattern in begin_patterns:
            if first_lines[i].endswith(pattern) or first_lines[i].startswith(pattern):
                begin_line = i
                break
        if begin_line > 0:
            break
    if begin_line == 0:
        open(log_file,'a').write(f+'\n')
        return None
    end_line = min(len(lines),begin_line+max_num_lines)
    #print 'begin_line:',begin_line,'end_line',end_line
    max_num_start = 0
    max_num_end = 0
    flag = 0
    num_next = 0
    num_start = 0
    i = begin_line
    while i < end_line:
        if len(lines[i])==0:
            i = i + 1
            continue
        if len(lines[i+1])==0:
            lines[i+1] = " "
        if lines[i][0].isdigit():
            if int(lines[i][0]) < max_num_start:
                if exists_larger_number(lines[i+1:i+6],max_num_end) is True:
                    i = i + 1
                    continue
                elif len(lines[i])>1 and lines[i][1].isdigit():
                    num_start = int(re.split('\D+',lines[i])[0])
                    if num_start >= max_num_start:
                        max_num_start = num_start
                        i = i + 1
                        continue
                end_line = i
                flag = 1
                break
            max_num_start = int(lines[i][0])
            if lines[i][-1] in [str(k) for k in range(10)]:
                num_next = int(re.split('\D+',lines[i])[-1])
                if num_next > max_num_end:
                    max_num_end = num_next
            i = i + 1
            continue
        elif lines[i][-1] in [str(k) for k in range(10)]:
            if len(re.findall('\d+ - \d+',lines[i]))>0:
                i = i + 1
                continue
            num_next = int(re.split('\D+',lines[i])[-1])
            #print num_next,max_num_end
            if num_next < max_num_end:
                if exists_larger_number(lines[i+1:i+6],max_num_end) is True:
                    i = i + 1
                    continue
                end_line = i
                flag = 1
                break
            elif num_next > 1800:
                i = i + 1
                continue
            elif have_similar_format(lines[max(begin_line,i-5):i],lines[i]) or num_next-max_num_end<10:
                max_num_end = num_next
            i = i + 1
            continue
        elif lines[i+1][0].isdigit() and int(lines[i+1][0]) >= max_num_start:
            i = i + 1
            continue
        elif i < begin_line+10:
            i = i+ 1
            continue
        else:
            if i == begin_line+10 and max_num_start == 0 and max_num_end == 0:
                #print 'ToC is None'
                return None
            if exists_larger_number(lines[i+1:i+6],max_num_end) or exists_larger_number2(lines[i+1:i+6],max_num_start):
                i = i + 1
                #print 'exists_larger_number',lines[i+1:i+6],max_num_end
                continue
            end_line = i
            break
    while len(lines[end_line])==0:
        end_line = end_line -1
    if flag:
            end_line = end_line -1
    if len(lines[end_line])>0:
        while lines[end_line].isdigit() or (lines[end_line][0].isdigit() is False and lines[end_line][-1].isdigit() is False):
            #print lines[end_line]
            end_line = end_line -1
            while len(lines[end_line])==0:
                end_line = end_line -1
    toc = lines[begin_line:end_line+1]
    toc.append("--------------------------this is the end of ToC-----------------------")
   # toc.extend(lines[end_line+1:end_line+8])
    return toc,begin_line,end_line

def testToCDetection(xml_dir):
    head = r'<PAGECOLUMN>\n<REGION.*?>\n<PARAGRAPH>\n<LINE>\n<WORD .*?>'
    C,C1,C2,C3,C4,C5=0,0,0,0,0,0
    for xml in os.listdir(xml_dir):
        text = open(xml_dir+os.sep+xml).read()
        pgs = re.findall(r'<OBJECT.*?>.*?</OBJECT>',text,re.S)
        first_pgs = '\n'.join(pgs[:min(50,len(pgs))])
        if re.search(head+r'CONTENTS\.?</WORD>\n</LINE>',first_pgs,re.I) is not None:
            C += 1
            continue
        if re.search(head+r'CHECK</WORD>\n<WORD .*?>LIST</WORD>\n</LINE>',first_pgs,re.I) is not None:
            C1 += 1
            continue
        if re.search(head+r'TABLE</WORD>\n<WORD .*?>OF</WORD>\n<WORD .*?>CONTENTS\.?</WORD>\n</LINE>',first_pgs,re.I):
            C2 +=1
            continue
        if re.search(head+r'CONTENTS</WORD>',first_pgs,re.I):
            C3 += 1
            continue
        if re.search(head+r'Text</WORD>\n<WORD .*?>Subjects</WORD>\n</LINE>',first_pgs,re.I) is not None:
            C4 += 1
            continue
        if re.search(head+r'INDEX\.?</WORD>\n</LINE>',first_pgs,re.I):
            C5 += 1
            continue
        print xml
    print C,C1,C2,C3,C4,C5

def genDic():
    txt = r'/home/zzw109/project/book/structureextraction/groundtruth100/100_books.txt'
    dir = r''
    bookid_dic = {}
    for line in open(txt):
        id,fname = line.split()
        book_name = fname[fname.rfind(r'/')+1:-4]
        bookid_dic[book_name]=id
    return bookid_dic
def genGT():
    xml = open(r'/home/zzw109/project/book/structureextraction/groundtruth100/free_groundtruth_100.xml').read()
    books = re.findall(r'<book>\n<bookid>(.*?)</bookid>\n(.*?)</book>',xml,re.S)
    dic = {}
    for book in books:
        dic[book[0]] = book[1]
    return dic

def ToCDetectionICDAR13(djvuXML):
    xml = open(djvuXML).read()
    pgs = re.findall(r'<OBJECT.*?>.*?</OBJECT>',xml,re.S)
    start_pg = -1
    v_lines = []

    #ToC start detection
    for i in range(len(pgs)):
        for p in toc_begin_patterns:
            if re.search(head+p,pgs[i],re.I) is not None:
                start_pg = i
                break
        if start_pg > -1:
            break
    if start_pg == -1:
        print 'no toc detected...'
        return

    #ToC end detection
    pre_page_no,page_no = -1,-1
    C_without_page_no = 0
    end_page = start_pg
    for i in range(start_pg,len(pgs)):
        #paras = re.findall(r'<PARAGRAPH>.*?</PARAGRAPH>',pgs[i],re.S)
        #for para in paras:
        lines = re.findall(r'<LINE>.*?</LINE>',pgs[i],re.S)
        for k in range(len(lines)):
            coords = re.findall(r'<WORD coords="(.*?)">.*?</WORD>',lines[k],re.S)
            words = re.findall(r'<WORD .*?>(.*?)</WORD>',lines[k],re.S)
            sr = re.search(r'\d+$',''.join(words))
            if sr is not None:
                page_no = int(sr.group())
            x_start = int(coords[0].split(',')[0])
            y_start = min([int(coord.split(',')[3]) for coord in coords])
            x_end = int(coords[-1].split(',')[2])
            y_end = max([int(coord.split(',')[1]) for coord in coords])
            #size = y_end - y_start
            v_lines.append((words,x_start,y_start,x_end,y_end,page_no))
            #print words
            if (pre_page_no+2)*100>page_no > pre_page_no:
                pre_page_no = page_no
                C_without_page_no = 0
            else:
                C_without_page_no += 1
                if C_without_page_no == 1:
                    end_page = i
                    if k == 0:
                        end_page = i-1
            if C_without_page_no >= 15:
                break
        if C_without_page_no >= 15:
            break
    for j in range(15):
        v_lines.pop()
    print v_lines
    print start_pg,end_page

    #ToC parsing

    #ToC linking
    bookid_dic = genDic()
    toc_dic = genGT()
    bookid = bookid_dic[djvuXML[djvuXML.rfind(r'/')+1:-9]]
    toc_GT = toc_dic[bookid]
    return

if __name__ == "__main__":
    head = r'<PAGECOLUMN>\n<REGION.*?>\n<PARAGRAPH>\n<LINE>\n<WORD .*?>'
    toc_begin_patterns = [r'CONTENTS\.?</WORD>\n</LINE>',
            r'CHECK</WORD>\n<WORD .*?>LIST</WORD>\n</LINE>',
            r'TABLE</WORD>\n<WORD .*?>OF</WORD>\n<WORD .*?>CONTENTS\.?</WORD>\n</LINE>',
            r'CONTENTS</WORD>',
            r'Text</WORD>\n<WORD .*?>Subjects</WORD>\n</LINE>',
            r'INDEX\.?</WORD>\n</LINE>']
    xml_dir = r'/home/zzw109/project/book/structureextraction/groundtruth100/xmls'
    #testToCDetection(xml_dir)
    t1 = datetime.now()
    ToCDetectionICDAR13(xml_dir+os.sep+r'addisonsl00couruoft_djvu.xml')
    #toc = ToC_detection(r'/home/zzw109/project/book/goodbooks/books/Pattern Recognition and Machine Learning.txt')
    #print toc
    t2 = datetime.now() - t1
    print t2.seconds
if 0:
	C,C1 = 0,0            
	for f in os.listdir(ToC_txt_dir):
	    C = C+1
	    f0 = ToC_txt_dir+os.sep+f
	    f1 = ToC_dir+os.sep+f
	    if os.path.exists(f0) is False:
	        continue
	    try:
	      toc = ToC_detection(f0)
	      #print toc
	      if toc is not None:
	        C1 = C1 + 1
	        open(f1,'w').write('\n'.join(toc))
	        print C1,C
	    except IndexError:
	      print "Index error"
	      continue

if 0:
    for r1 in range1[0:2]:
        for r2 in range2:
            f = ToC_txt_dir+os.sep+'10.1.1.'+str(r1)+'.'+str(r2)+'.txt'
            f1 = ToC_dir + os.sep+'10.1.1.'+str(r1)+'.'+str(r2)+'.txt'
            print f
            if os.path.exists(f) is False:
                #print 'file not exists\n'
                continue
            toc = ToC_detection(f)
            if toc is not None:
                open(f1,'w').write('\n'.join(toc))
