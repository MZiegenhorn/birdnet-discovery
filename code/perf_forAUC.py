#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Code to get performance across the full range of confidence thresholds, in order to do AUC assessments for PR and ROC curves (done in tab1_metrics.py)

@author: maziegenhorn


"""


#reset environment
from IPython import get_ipython;   
get_ipython().magic('reset -sf')
get_ipython().magic('clear')

#required packages
from pathlib import Path
import pandas as pd
import numpy as np
import re
from itertools import compress


########### SETTINGS ####################

#load in csv of manual annotations
absfile = "~allManuals_combined.csv"
#folder for birdnet predictions
birdnetFold = Path("~base_bnet_labels") 
#specCodes- if using base_bnet_run data, need to adjust scientific names to 4-letter codes. Use specCodes.csv for this. If using asnet results, set to empty
specCodes = []
specCodes =Path('~specCodes.csv')  
filelength = 300 #file length of input sound files, in seconds
conf = np.linspace(0,1,20) #anything below this threshold will be pruned 

##############################


#########  function- find in-window detections. This is unnecessary when looking at the file level, but also useful if you want to look at finer-scale results. 
def inwindets(data,datastarts,datastops,winstart,winstop):
    #get manual detections in the window
    cond1 = (datastarts >= winstart)&(datastarts < winstop)#is start in window
    cond2 = (datastops > winstart)&(datastops <= winstop)#is end in window
    cond3 = (datastops <= winstop)&(datastarts >= winstart)#the full detection is in the window 
    inwinman = data[cond1 | cond2 | cond3]
    
    return inwinman

####################

#round confidence values to try
conf = conf.round(2) 

## open absfile csv, query file names, look for matching files in lab_list and figure out what's within each time chunk, add that to dataframe

#load manual csv
mandata = pd.read_csv(absfile)
lab_list = list(mandata['file_name'].drop_duplicates())
netlist = list(birdnetFold.glob('*results.csv'))

        
#setup start and end time- this could be modified to be more sophisticated if you're interested in looking at detections/annotations at a finer-scale than the full file length. 
starts = [0]
stops = [filelength]


for itrc in conf:
    #empty arrays for data frame creation
    filename = []; startsall = []; stopsall = []; manSp = []; netSp = []; confall = []
    
    #run through each label file    
    for filen in lab_list:
        filet = [filen.split('.')[0] in i.name for i in netlist]
        filetemp = list(compress(netlist,filet))
        
        ####### now do the same for network data
        if not filetemp:
            #if this file isn't in the network results, skip it, and print a warning- this means there is data in your manual set that hasn't yet been evaluated by birdnet
            print('WARNING! No corresponding file found for net file: '+filen)
            
        else:
            file = filetemp[0]
            netdata = pd.read_csv(file)
            
            #truncate manual data to this file only 
            useman = mandata[mandata['file_name']==filen]
        
            #run through starts
            for ic in range(0,len(starts)):
                
                #get in-window detections for manuals
                inwinman = inwindets(useman, useman["start_time"],
                                     useman["end_time"],starts[ic],stops[ic])
                
                if not inwinman.empty:
                    #combine if needed 
                    speclistman = list(inwinman['annotAll'].drop_duplicates())
                    specstrman = ' , '.join(speclistman)
                else:
                    #if no annotations, add a nan
                    specstrman = "nan"
                
                
                ####### now do the same for birdnet data
                inwinnet = inwindets(netdata, netdata["Start (s)"],
                                     netdata["End (s)"],starts[ic],stops[ic])
                
                if not inwinnet.empty:
                    #compile everything here and add to manual dataset
                    
                    #prune detections below this iteration's threshold
                    windetsfinal = inwinnet[inwinnet['Confidence']>=itrc]
                    
                    if not windetsfinal.empty:  
                        #replace names for fc and pesa female
                        windetsfinal.loc[windetsfinal['Common name']=='fc',['Common name']]= 'RTLO'
                        windetsfinal.loc[windetsfinal['Common name']=='f',['Common name']]= 'PESA'
                        #join them
                        speclist = list(windetsfinal['Common name'].drop_duplicates())
   
                        #if dealing with base birdnet results, adjust species codes 
                        if specCodes:
                            spdata = pd.read_csv(specCodes)
                            #for each row, find the correct species code
                            specsci = list(windetsfinal['Scientific name'].drop_duplicates())
                            speclist2 = []
                            for spec in specsci:
                                spcode = spdata[spdata['scientific_name']==spec]
                                if spcode.empty:
                                    print('species '+spec+' not in spcodes!')
                                    speclist2.append(spec)
                                else:
                                    speclist2.append(spcode['tag'].iloc[0])
                            speclist = speclist2                  
                        
                        specstr = ' , '.join(speclist)
                    else:
                        specstr = 'nan'
                else:
                    specstr = 'nan'
                     
                
                #fill rows accordingly
                filename.append(filen) 
                startsall.append(starts[ic])
                stopsall.append(stops[ic])
                manSp.append(specstrman)
                netSp.append(specstr)

    
    #create output data frame
    allDataFull = pd.DataFrame({'filename':filename,'start':startsall,'stop':stopsall,
                            'manSp':manSp,'netSp':netSp})
    
    #remove anything where net and manual both had no detection, those shouldn't be included in ROC curve
    allData = allDataFull[(allDataFull['manSp']!='nan' )| (allDataFull['netSp']!='nan')].reset_index(drop=True)
    

#################### evaluate performance #######################################
    
    #get specs to run through- only do it on first, so keeps them the same
    if itrc == 0:
        specsman = list(allData['netSp'].drop_duplicates()) 
    
    flatspec = []
    for itr in specsman:
        s = [i.strip() for i in itr.split(",")]
        for itr2 in s:
            s2 = itr2.strip("/'") 
            #use re to get rid of any pesky non-alphabet strings
            regex = re.compile('[^a-zA-Z]')
            #First parameter is the replacement, second parameter is your input string
            sfinal = regex.sub('', s2)
            
            flatspec.append(sfinal)
    
    #get unique species and move through
    finalspecs = list(set({v.casefold(): v for v in flatspec}.values()))
    
    tp = []; tn = []; fp = []; fn = []; spec = []; acc = []; pre = []; rec = []; fprate = []
    
    for specuse in finalspecs:
        
        if 'nan' not in specuse:
        
            print('Running for spec '+specuse+' and conf '+str(itrc))
            
            #get indices for positive and negative detections from manual and network (birdnet) data
            speclower = specuse.lower()
            posMan = pd.Series([speclower in i.lower() for i in allData['manSp']])
            posNet = pd.Series([speclower in i.lower() for i in allData['netSp']])
            negMan = pd.Series([speclower not in i.lower() for i in allData['manSp']])
            negNet = pd.Series([speclower not in i.lower() for i in allData['netSp']])
            
            #true positives, i.e., trueSp and netSp are both species A
            tptemp = len(allData[posMan & posNet])
            tp.append(tptemp)
            
            #calculate true negative,i.e. trueSp and netSp are NOT species A
            tntemp = len(allData[negMan & negNet])
            tn.append(tntemp)
            
            #calculate false positive, i.e., trueSp = NOT species A, netSp = species A 
            fptemp = len(allData[negMan & posNet])
            fp.append(fptemp)
            
            #calculate false negative, i.e., trueSp = species A, netSp = NOT species A 
            fntemp = len(allData[posMan & negNet])
            fn.append(fntemp)
            
            #save species
            spec.extend([specuse])
            
            #### get metrics to add
            acc.append(round((tptemp + tntemp)/(tptemp + tntemp + fptemp + fntemp),5))

            if (tptemp+fptemp == 0):
                pre.append(np.nan)
            else:
                pre.append(round(tptemp/(tptemp + fptemp),5))
                
            if (tptemp + fntemp == 0):
                rec.append(np.nan)
            else:
                rec.append(round(tptemp/(tptemp + fntemp),5))
                
            if (fptemp + tntemp == 0):
                fprate.append(np.nan)
            else:
                fprate.append(round(fptemp/(fptemp+tntemp),5))
                

    #store values to use for roc

    #initialize data frame if first loop
    if 'ROCdata' not in locals():
        ROCdata = pd.DataFrame({'spec':spec})
    
    #recall = tp rate    
    newtp = 'conf'+str(itrc)+'_tp'
    newfp = 'conf'+str(itrc)+'_fp'
    newpr = 'conf'+str(itrc)+'_pre'
    ROCdata[newtp] = rec
    ROCdata[newfp] = fprate
    ROCdata[newpr] = pre

#save the data so we can use it in tab1_metrics
outdetsfile = birdnetFold/(birdnetFold.name.split('/')[-1]+'_ROC_data.csv')
ROCdata.to_csv(outdetsfile,index=False) 
    
