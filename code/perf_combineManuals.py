#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

@author: maziegenhorn

This script converts the csv of all manual annotations into a final csv, separated into time chunks defined by the detwindow parameter, of the list of species manually annotated in that certain detwindow

"""


#reset environment
from IPython import get_ipython;   
get_ipython().magic('reset -sf')
get_ipython().magic('clear')


#required packages
from pathlib import Path
import pandas as pd
import numpy as np
from itertools import compress



########### SETTINGS ####################

#load in csv of labels from all manual reviewers
absfile = "~/manuals_all_labels_clean.csv"
#output folder
outfold = Path("~")

detwindow = 0.5 # set the detection window in seconds
filelength = 300 #file length of input sound files, in seconds
####################



############ functions ##################

#this function compiles detections from each individual reviewer
def revcode_sort(data,revdata,strkey):
    sasidx = [strkey in i for i in revdata]
    revsas = list(compress(revdata,sasidx))
    
    if revsas:
        antemp = list(data[sasidx])
    else:
        antemp = ['nan']
        
    #convert to string so don't end up with lists of lists
    anstr = ','.join(antemp)
    
    return anstr
#########################3



############ give a label to each detection window for each manual reviewer who reviewed that file  who had that file ###########

#load in starting csv
manualdata = pd.read_csv(absfile)

##get the full list of files reviewed by manual reviewers
#separate file names from reviewer codes
filen = [i.split('.')[0] for i in manualdata['file_name']] 
filelist = list(set(filen))


#setup starts and stops based on file length and detwindow
#data window size
nchunks = filelength/detwindow 
starts = np.linspace(0,filelength-detwindow,int(nchunks))
stops = starts + detwindow
    

filename = []; start_time = []; end_time = []; annotSAS = []; annotARA = []; annotJP = []; annotMZ=[]; annotMB=[]; annotAll = []

#run through each file 
for usefile in filelist:
    
    #truncate to annotations only from that file 
    keepidx = [usefile in i for i in filen]
    usedata = manualdata[keepidx]
    
    
    #for each time chunk
    for ic in range(0,len(starts)):
        #define annotations that are in the detection window
        cond1 = (usedata["start_time"]<stops[ic])&(usedata["start_time"]>=starts[ic])#is start in window
        cond2 = (usedata["end_time"]<=stops[ic])&(usedata["end_time"]>starts[ic])#is end in window
        cond3 = (usedata["start_time"]<=starts[ic])&(usedata["end_time"]>=stops[ic])#does detection span whole window
        absdets = usedata[cond1 | cond2 | cond3] 
        
        #if annotations are found
        if not absdets.empty:
            #add starts, end, filename to growing list
            start_time.append(starts[ic])
            end_time.append(stops[ic])
            #get correct filename
            filetemp = absdets['file_name'].iloc[0]
            filename.append(filetemp.split('.')[0]+'.wav')
            
            #query revcodes- who's annotation was it?
            revcodes = [i.split('.')[1] for i in absdets['file_name']]
            annots = absdets['common_name']
            
            an1temp = revcode_sort(annots,revcodes,'SAS')
            an2temp = revcode_sort(annots,revcodes,'JP')
            an3temp = revcode_sort(annots,revcodes,'MZ')
            an4temp = revcode_sort(annots,revcodes,'MB')
            
            #combine all and delete duplicates
            allann = an1temp+','+an2temp+','+an3temp+','+an4temp
            allist = allann.split(',')
            finallist = list(set(allist))
            
            #append individual annotation lists    
            annotSAS.append(an1temp)
            annotJP.append(an2temp)
            annotMZ.append(an3temp)
            annotMB.append(an4temp)
            #append overall annotation list
            annotAll.append(finallist)
        

    print('Done with file ',usefile)


#output data frame
alldata = pd.DataFrame({"file_name":filename,"start_time":start_time,           "end_time":end_time,"annotSAS":annotSAS,"annotJP":annotJP,"annotMZ":annotMZ,"annotMB":annotMB,"annotAll":annotAll})


#save output data frame
#setup output name
outdetsfile = outfold/'allManuals_combined.csv'
alldata.to_csv(outdetsfile,index=False)



 
  





