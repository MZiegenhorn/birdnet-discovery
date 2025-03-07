#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

@author: maziegenhorn

written to create short deployment folders to use for sbnet detector step
running on whole deployments just takes too long
then can cluster these and use them for full dataset

"""

#reset environment
from IPython import get_ipython;   
get_ipython().magic('reset -sf')
get_ipython().magic('clear')

#required packages
from pathlib import Path
import os
import pandas as pd
from itertools import compress
import shutil


####settings

#will run on this folder and subfolders
wavfolder = Path("/TLSA_acoustic_monitoring_2023/audiomoth_files/AL54") #NOT PROVIDED
#where to save output 
outpath = Path("~/shortDeps/wavs/TLSA_2023_AL54")

#date range
starthr = 14
endhr = 17 #this will end at 18
################

############ functions ###############

##### grabbed this from stack exchange, patch to fix speed of shutil (WAY faster now!)
def _copyfileobj_patched(fsrc, fdst, length=16*1024*1024):
    """Patches shutil method to hugely improve copy speed"""
    while 1:
        buf = fsrc.read(length)
        if not buf:
            break
        fdst.write(buf)
shutil.copyfileobj = _copyfileobj_patched

def copy_wavfiles(usedir,starthr,endhr,outfold):
    
    #do everything else
    if not(os.path.exists(outfold)):
        os.makedirs(outfold)
                
    #get all wav files 
    wavfiles = list(usedir.glob("*.[Ww][Aa][Vv]"))
            
    #get names
    filenames = [i.name.split('.')[0] for i in wavfiles]
    filestart = pd.to_datetime(filenames,format='%Y%m%d_%H%M%S')
    #resort wavfiles and filestart so indices work here
    filestart, wavfiles = (list(t) for t in zip(*sorted(zip(filestart, wavfiles))))
    keephrs = [(i.hour>=starthr) & (i.hour < endhr) for i in filestart]
    keepfiles = list(compress(wavfiles,keephrs))
   

    #save wavfile to new folder
    outfilelist = list(outfold.glob('*.[Ww][Aa][Vv]'))
            
    for file in keepfiles:
        outfile = outfold/file.name
    #skip it if already copied
        if outfile in outfilelist:
            print('Already exists! Skipping file '+file.name)
        else:
            shutil.copyfile(file,outfile)
            print('Copied file '+file.name)


#########################################



#get all folders and subfolders
subfolds = os.listdir(wavfolder)

keepidx = ['.' not in i for i in subfolds]; usefolds = list(compress(subfolds,keepidx))

#for each folder
if usefolds:
    subfoldflag = True
else:
    subfoldflag = False
    
if subfoldflag:

    for dep in usefolds:
        depfolder = wavfolder/dep
        outfolder = outpath/dep
    
    #if additionally nested, go in one more level
        sub2 = os.listdir(wavfolder/dep)
        testfold = depfolder/sub2[1] #chose a random index for this, might to be the best way
    
        if os.path.isdir(testfold):
            for sub in sub2:
                #get our full folder name
                subuse = depfolder/sub
                #add a level to outfolder
                outfold2 = outfolder/sub
                
                #get files to keep
                copy_wavfiles(subuse,starthr,endhr,outfold2)
                
                print('Done with folder '+sub)

        else:
        
            #define keepfiles
            copy_wavfiles(depfolder,starthr,endhr,outfolder)
            
            print('Done with folder '+dep)   
else:
        
    outfolder = outpath
            
    #define keepfiles
    copy_wavfiles(wavfolder,starthr,endhr,outfolder)











