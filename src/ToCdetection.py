#! /usr/bin/python

import re
import os

ToC_txt_dir = r'./allbookstxt'
ToC_dir = r'./toc'
log_file = r'./log.txt'
range1 = range(1,194)
range2 = range(1,10000)
begin_patterns = ['CONTENTS','Contents','TABLE OF CONTENTS','Table of contents']

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


if __name__ == "__main__":
    toc = ToC_detection(r'/home/zzw109/project/book/goodbooks/books/Pattern Recognition and Machine Learning.txt')
    print toc
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
    
        



