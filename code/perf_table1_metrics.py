#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Code to evaluate AUC for ROC and PR curves, determine optimum confidence score across classes, and calculate average precision and recall 

@author: maziegenhorn
"""

#reset environment
from IPython import get_ipython;   
get_ipython().magic('reset -sf')
get_ipython().magic('clear')


#required packages
from pathlib import Path
import pandas as pd
from matplotlib import pyplot as plt
from sklearn import metrics
import numpy as np



#### settings ##########################

#load ROC file
ROCfiles = Path("~/base_bnet_labels")
confth = 0.25 #confidence level for avg prec and recall- you can set this at 0 on the first run and then run it again once you've inspected the f-score results with the optimum value to extract average precision and recall

#where to save output 
outpath = ROCfiles #just keep it the same path

################
 
    
#grab the ROC file 
csvlist = list(ROCfiles.glob('*ROC_data.csv'))
ROCdata = pd.read_csv(csvlist[0])


#rmv species list
rmvspec=['unk','Rain','Human','insect','motor','CACK','LTDU','BARG','PAJA','ARTE','YBLO','WCSP','WISN','POJA','ATSP','BRAN','EYWA','SNBU','ARFO','LESA','SMLO','WESA']#remove if CONTAINS these, includes all species in less than 10 files
rmvpattern = '|'.join(rmvspec)
prunedata = ROCdata[~ROCdata['spec'].str.contains(rmvpattern)]


fp = ['fp' in i for i in ROCdata.columns]
tp = ['tp' in i for i in ROCdata.columns]
pre = ['pre' in i for i in ROCdata.columns]


#for each species, add to plot
aucall=[]; praucall=[]
for spec in prunedata['spec']:

    prunefp = ROCdata.loc[ROCdata['spec']==spec,fp]
    prunetp = ROCdata.loc[ROCdata['spec']==spec,tp]
    prunepre = ROCdata.loc[ROCdata['spec']==spec,pre]
    
    #prune if precision contains nans
    na_free = prunepre.dropna(axis=1)
    if np.size(na_free) < 2:
        print('no useable values for class '+spec)
    else:
        coluse = [i.split('_')[0] for i in na_free.columns]
        prunepre = na_free
        prunetp = prunetp.loc[:,[i+'_tp' for i in coluse]]
        prunefp = prunefp.loc[:,[i+'_fp' for i in coluse]]
        
        
        #display auc
        #resort if needed
        pridx = np.fliplr(np.argsort(prunefp))
        fpsort = prunefp.values.flatten()[pridx]
        tpsort = prunetp.values.flatten()[pridx]
        #add 0 and 1 to properly bound values for ROC AUC assessment
        tplist = list(tpsort.flatten())
        tplist.append(0)
        fplist = list(fpsort.flatten())
        fplist.append(0)
        tplist.insert(0,1)
        fplist.insert(0,1)
        
        auc = metrics.auc(fplist,tplist)
        #print('AUC for class '+spec+' = '+str(auc))
        #save AUC
        aucall.append(auc)
        
        #save AUC PR
        tpidx = np.fliplr(np.argsort(prunetp))
        tpsort = prunetp.values.flatten()[tpidx]
        presort = prunepre.values.flatten()[tpidx]
        #add 0 and 1 to properly bound values for PR AUC assessment
        tplist2 = list(tpsort.flatten())
        #tplist2.append(0)
        #tplist2.insert(0,1)
        prelist = list(presort.flatten())
        #prelist.append(1)
        #prelist.insert(0,0)
        
        prauc = metrics.auc(tplist2,prelist)
        
        
        praucall.append(prauc)
        
        #plot AUC ROC- this isn't included in the manuscript, but you may want to examine it 
        ax1 = plt.plot() 
        plt.plot(fplist,tplist,'o-')
        
plt.ylim([0 ,1])
plt.xlabel('False positive')
plt.ylabel('True positive')
plt.title(csvlist[0].name)
plt.show()

print(csvlist[0].name)
print('final AUC: ',np.nanmean(aucall))
print('final PR AUC: ',np.nanmean(praucall))

#compute avg pre and rec, use that to get f-rate at each conf and plot
#this plot can be inspected visually to get the optimum confidence threshold at a variety of f-scores
fs = [1,0.5,0.25,0.1]
#get columns
cols = prunedata.columns
conf = [i[0] for i in cols.str.split('_')[1:]]
allconf = list(set(conf))

for f in fs:
    fsave = []; confnum = []
    for confv in allconf:
        #find correct column for recall, precision
        colrec = confv+'_tp'
        recidx = [colrec in i for i in prunedata.columns]
        colpre = confv+'_pre'
        preidx = [colpre in i for i in prunedata.columns]
        avgpre = np.nanmean(prunedata[colpre]); avgrec = np.nanmean(prunedata[colrec])
        fscore = (f**2 + 1) * (avgpre * avgrec / (f**2 * avgpre + avgrec))
        fsave.append(fscore)
        confnum.append(float(confv.split('f')[1]))
        
    #plot
    ax2 = plt.plot() 
    plt.plot(confnum,fsave,'.',label=str(f))
plt.xlabel('Confidence threshold')
plt.ylabel('F-score')
plt.legend(loc='upper left')
plt.show()

#for asnet results, optimum confidence threshold is 0.83 for F-score 0.5


#get average precision and recall at conf closest to 0.83

confnum = np.array(confnum)[np.argsort(confnum)]
confuse = next(x[0] for x in enumerate(confnum) if float(x[1])>=confth)
colrec = 'conf'+str(confnum[confuse])+'_tp'
colpre = 'conf'+str(confnum[confuse])+'_pre'
recidx = [colrec in i for i in prunedata.columns]
preidx = [colpre in i for i in prunedata.columns]
avgpre = np.nanmean(prunedata[colpre]); avgrec = np.nanmean(prunedata[colrec])

print('Average precision at conf '+str(confth)+': '+str(avgpre))
print('Average recall at conf '+str(confth)+': '+str(avgrec))
