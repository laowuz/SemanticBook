#!  /usr/bin/python
import subprocess
import os

def scp_from_brick3(input_file, output_dir):
  filenames = open(input_file).read().split()
  pre_dir = r'/opt/data/repositories/rep1/10/1/1'
  for filename in filenames:
    xml = pre_dir+os.sep+filename.split('.')[3]+os.sep+filename.split('.')[4]+os.sep+filename[0:-3]+'xml'
    scp = r'scp zzw109@brick3.ist.psu.edu:'+xml+' '+output_dir
    os.system(scp)
file = r'../info/allbook154to193.txt'
dir = r'../xml/'
scp_from_brick3(file,dir)

