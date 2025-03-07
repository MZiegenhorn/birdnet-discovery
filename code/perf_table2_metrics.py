#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
assess performance of of base birdnet and arcticsoundsnet; all data in Table 2 and S3 Table come from this script

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
birdnetFold = Path("~/base_bnet_labels") 
#specCodes- if using base_bnet_run data, need to adjust scientific names to 4-letter codes. Use specCodes.csv for this. If using asnet results, set to empty
#specCodes = []
specCodes =Path('~specCodes.csv')  
filelength = 300 #file length of input sound files, in seconds
confth = 0 #best confidence threshold to use can be determined from running assessPerf_forAUC.py and then tab1_metrics.py scripts


#########  function- ####################
#find in-window detections. This is unnecessary when looking at the file level, but also useful if you want to look at finer-scale results. 
def inwindets(data,datastarts,datastops,winstart,winstop):
    #get manual detections in the window
    cond1 = (datastarts >= winstart)&(datastarts < winstop)#is start in window
    cond2 = (datastops > winstart)&(datastops <= winstop)#is end in window
    cond3 = (datastops <= winstop)&(datastarts >= winstart)#the full detection is in the window 
    inwinman = data[cond1 | cond2 | cond3]
    
    return inwinman

####################



#####  combine labels from manual annotation and birdnet/arcticsoundsnet results ##################

## open absfile csv, query file names, look for matching files in lab_list and figure out what's within each time chunk, add that to dataframe

#load manual csv
mandata = pd.read_csv(absfile)
lab_list = list(mandata['file_name'].drop_duplicates())
netlist = list(birdnetFold.glob('*results.csv'))

        
#setup start and end time- this could be modified to be more sophisticated if you're interested in looking at detections/annotations at a finer-scale than the full file length. 
starts = [0]
stops = [filelength]
 
#empty arrays for data frame creation
filename = []; startsall = []; stopsall = []; manSp = []; netSp = []; netdatafull = []; confall = []   

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
                windetsfinal = inwinnet[inwinnet['Confidence']>=confth]
                
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


#empty arrays for data frame creation
filename = []; startsall = []; stopsall = []; manSp = []; netSp = []; netdatafull = []; confall = []

#run through each label file    
for filen in lab_list:
    filet = [filen.split('.')[0] in i.name for i in netlist]
    filetemp = list(compress(netlist,filet))
    
    #if there's not a corresponding net file, skip evaluation
    if not filetemp:
        print('No corresponding net file found for file '+filen)
        
    else:

        #truncate manual data 
        useman = mandata[mandata['file_name']==filen]
        
        #run through starts
        for ic in range(0,len(starts)):
            
            inwinman = inwindets(useman, useman["start_time"],
                                 useman["end_time"],starts[ic],stops[ic])
            
            if not inwinman.empty:
            
                #combine if needed 
                speclistman = list(inwinman['annotAll'].drop_duplicates())
            #could change the above and NOT drop the duplicates down the line, if want to actually keep them to use as proxy for counts... 
                specstrman = ' , '.join(speclistman)
            else:
                specstrman = "nan"
            
            
            ####### now do the same for network data

            file = filetemp[0]
            netdata = pd.read_csv(file)
            
            inwinnet = inwindets(netdata, netdata["Start (s)"],
                                 netdata["End (s)"],starts[ic],stops[ic])
            
            if not inwinnet.empty:
                #compile everything here and add to manual dataset
                #prune anything below confidence threshold
                windetsfinal = inwinnet[inwinnet['Confidence']>=confth]
                
                if not windetsfinal.empty:  
                    #replace names for fc and pesa female
                    windetsfinal.loc[windetsfinal['Common name']=='fc',['Common name']]= 'RTLO'
                    windetsfinal.loc[windetsfinal['Common name']=='f',['Common name']]= 'PESA'
                    #join them
                    specall = list(windetsfinal['Common name'].drop_duplicates())
                    
                    if 'fc' in specall:
                        specall[specall=='fc'] = 'RTLO'
                        
                    speclist = []
                    conflist = []
                    for iS in specall:
                        speclist.append(iS)
                        conflist.append(str(np.max(windetsfinal.loc[windetsfinal['Common name']==iS,'Confidence'])))
                    
                    #deal with species code, if coming from base_bnet_labels
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
                    conf = ','.join(conflist)
                else:
                    specstr = 'nan'
                    conf = 'nan'
            else:
                specstr = 'nan'
                conf = 'nan'

                 
        #fill rows accordingly
        filename.append(filen)   
        startsall.append(starts[ic])
        stopsall.append(stops[ic])
        manSp.append(specstrman)
        netSp.append(specstr)
        confall.append(conf)
        
        #save netdatafull- this is used to get the total number of detections for Table 1. Set confth to 0 to get the full number, and then to the optimum value to get the adjusted number.
        if not netdata[netdata['Confidence']>=confth].empty :
            netdatafull.append(len(netdata[netdata['Confidence']>=confth]))

#create output data frame
allData = pd.DataFrame({'filename':filename,'start':startsall,'stop':stopsall,
                        'manSp':manSp,'netSp':netSp,'conf':confall})
    
##print number of network (birdnet or arcticsoudnsnet) detections
print('Total number of network detections: '+str(sum(netdatafull)))


#################### performance loop #######################################

#get specs to run through
specsman = list(allData['netSp'].drop_duplicates().dropna()) 

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


tp = []; tn = []; fp = []; fn = []; spec = []; acc = []; pre = []; rec = []; nMan = []; rocsave = []

for specuse in finalspecs:
    
    #get relevant indices
    speclower = specuse.lower()
    posMan = pd.Series([speclower in i.lower() for i in allData['manSp']])
    posNet = pd.Series([speclower in i.lower() for i in allData['netSp']])
    negMan = pd.Series([speclower not in i.lower() for i in allData['manSp']])
    negNet = pd.Series([speclower not in i.lower() for i in allData['netSp']])
    
    #calculate true positive, i.e., trueSp and net Sp is specA 
    tptemp = len(allData[posMan & posNet])
    tp.append(tptemp)
    
    #calculate true negative,i.e. trueSp and netSp are NOT specA
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
    #save number of manual detections of that species
    nMan.append(len(allData[posMan]))
    
    #### get metrics to add
    acc.append(round((tptemp + tntemp)/(tptemp + tntemp + fptemp + fntemp),5)*100)
 
    
    if (tptemp+fptemp == 0):
        pre.append(np.nan)
    else:
        pre.append(round(tptemp/(tptemp + fptemp),5)*100)
        
    if (tptemp + fntemp == 0):
        rec.append(np.nan)
    else:
        rec.append(round(tptemp/(tptemp + fntemp),5)*100)
    
#combine into dataframe
test = [tp[i] + fp[i] for i in range(0,len(fp))]


#allPerf can be examined to get all data from Table 2
#the exception to this is species with no network detections- in that case, precision = NA, recall = 0, and accuracy can be computed using nfiles (total number of manually annotated files, 524) via 
#accuracy = (nfiles - nMan) / nfiles

allPerf = pd.DataFrame({'Species':spec,'Accuracy':acc,'Precision':pre,'Recall':rec,
                        'TPos':tp,'TNeg':tn,'FPos':fp,'FNeg':fn,'nMan':nMan,'nNet':test})


#save outputs to birdnetfold
#setup output name
outdetsfile = birdnetFold/(birdnetFold.name.split('/')[-1]+'_'+str(filelength)+'_performance_data.csv')
allData.to_csv(outdetsfile,index=False)

#metrics
outdetsfile = birdnetFold/(birdnetFold.name.split('/')[-1]+'_'+str(filelength)+'_performance_metrics.csv')
allPerf.to_csv(outdetsfile,index=False)

 
  





