#! /usr/bin/python

import os
from subprocess import call

errs=['10.1.1.133.8170.pdf','10.1.1.178.9385.pdf','10.1.1.176.6996.pdf','10.1.1.190.5454.pdf','10.1.1.183.1275.pdf','10.1.1.110.1124.pdf','10.1.1.97.1530.pdf','10.1.1.148.8602.pdf','10.1.1.169.4779.pdf','10.1.1.139.681.pdf','10.1.1.138.2400.pdf','10.1.1.175.8439.pdf','10.1.1.175.772.pdf','10.1.1.188.8310.pdf','10.1.1.187.3373.pdf','10.1.1.186.8382.pdf','10.1.1.184.2778.pdf','10.1.1.182.4561.pdf','10.1.1.182.9814.pdf','10.1.1.179.2375.pdf','10.1.1.179.459.pdf','10.1.1.179.2392.pdf','10.1.1.96.5922.pdf','10.1.1.92.7704.pdf','10.1.1.149.639.pdf','10.1.1.169.6788.pdf','10.1.1.165.4563.pdf','10.1.1.163.2745.pdf','10.1.1.157.4734.pdf']
file = r'../101to..txt'
pdfs = [it.split()[0] for it in open(file).read().strip().split('\n')]
for pdf in pdfs:
    print pdf
    if os.path.exists(r'../pictures/'+pdf[:-4]+'.png'):
        continue
    if pdf in errs:
        continue
    call(['convert',r'../pdfs/'+pdf+'[0]',r'../pictures/'+pdf[:-4]+'.png'])
