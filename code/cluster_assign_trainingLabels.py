#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This code takes wavfiles, cluster times, and an associated csv that says which clusters you'd like to pull'. Output is training examples for your classifier, sorted according to the labels in the csv file

@author: maziegenhorn


"""

#reset environment
from IPython import get_ipython;   
get_ipython().magic('reset -sf')
get_ipython().magic('clear')

#required packages
from pathlib import Path
import pandas as pd
from itertools import compress
import os
import math as mt
import scipy.io.wavfile 
import numpy as np
import librosa


######################3 settings #######################

#load in csv of assignments, and set output path 
homeroot = Path("~")
selroot = homeroot/"shortDeps/asnet_binary_output/clusters"
outfolder = homeroot/"shortDeps/new_trainingData"
clus_sheet = homeroot/"cluster_typeAssign.csv"
fsuse = 16000 #sampling rate of audio data, in Hz

################


#read in cluster assignment sheet
assigndata = pd.read_csv(clus_sheet)

#run through each row of data and use relevant info 
for i in range(0,len(assigndata)):
    assignrow = assigndata.iloc[i]
    iclus = assignrow["Cluster #"]
    dep = assignrow["Folder"]
    assign = assignrow["Label"]
    
    #grab selection files
    selfolder = selroot/dep
    sel_list = list(selfolder.glob("*.txt"))

    #check for output folder 
    outpath = outfolder/str(assign)
    
    if not(os.path.exists(outpath)):
        os.makedirs(outpath)
    
    #pull the correct selection file
    selstr = 'Cluster'+str(iclus)+'_'
    seluse = [selstr in sel_list[i].name for i in range(0,len(sel_list))]
    selfile = list(compress(sel_list,seluse))
    
    seltab = pd.read_table(selfile[0])
    
    #for each entry, pull the right wav, and grab the right time from it
    count = 1
    
    for ie in range(0,len(seltab)):
        entry = seltab.iloc[ie]
        
        #open sound file, and pull the right times!
        s,fs = librosa.load(entry['Wavfile'],sr=fsuse)
        #get time and convert to x position
        startsec = entry['Start time']
        endsec = startsec + 3 #birdnet labels are 3 seconds long
        startX = startsec * fs; endX = endsec * fs
       
        #grab selection from wav file
        wavtrunc = s[mt.floor(startX):round(endX)]
     
         #save using original name, annotation, and count
        savname = dep+'_'+entry['Wavfile'].split('/')[-1].replace('.WAV','_')+str(iclus)+'_'+str(count)+'.wav'
        outfile = outpath/savname
         #convert to 16 bit so raven will read it correctly
        wav16 = wavtrunc.astype(np.float32)
        scipy.io.wavfile.write(outfile,fs,wav16)

        count = count + 1
        
    print('Done with clus '+str(iclus))






