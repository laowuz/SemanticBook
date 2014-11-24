#! /user/bin/python
import re

class ArnetAuthor():
    def __init__(id,name):
        self.id = id
        self.name = name
        self.interest = ''
        self.experience = ''
        self.paper_title = ''
        slef.homepage = ''
    def setInterest(interest):
        self.interest = interest
    def setExperience(exp):
        self.experience = exp
    def setPaper_Title(pt):
        self.paper_title = pt
    def setHomepage(hp):
        self.homepage = hp

class ArnetAuthors():
    def __init__(self,infile,outfile):
        self.text = open(infile).read()
        self.author_out = open(outfile,'w')

    def writeAuthors(self):
        find = re.findall('\(\d+,\'(.*?)\'',self.text)
        print len(find)
        self.author_out.write('\n'.join(find))
        self.author_out.close()



if __name__ == "__main__":
    aa = ArnetAuthors(r'/home/zzw109/laowuz/coevolution/arnet_authors.sql',r'/home/zzw109/laowuz/coevolution/arnet_authors.txt')
    aa.writeAuthors()

