#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Code for creating plots that are part of figure 3

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
import numpy as np
from scipy.stats import pearsonr


####settings

#load ROC file 
ROCroot = Path("~/asnet_final_labels")
confth = 0.83 #optimum confidence level for network 
#where to save output 
outpath = ROCroot #just keep it the same path

################
    
#grab the ROC file
csvlist = list(ROCroot.glob('*ROC_data.csv'))
ROCdata = pd.read_csv(csvlist[0])


#rmv species list
rmvspec=['unk','Rain','Human','insect','motor','CACK','LTDU','BARG','PAJA','ARTE','YBLO','WCSP','WISN','POJA','ATSP','BRAN','EYWA','SNBU','ARFO','LESA','SMLO','RTLO','WESA'] #species not included in evaluation
#remove species
rmvpattern = '|'.join(rmvspec)
prunedata = ROCdata[~ROCdata['spec'].str.contains(rmvpattern)]

#get confidence
cols = prunedata.columns
conf = [i[0] for i in cols.str.split('_')[1:]]
allconf = list(set(conf))


#prune data for each species to get average pre and average rec at confidence closest to confth
precdata = []; recdata = []
for spec in prunedata['spec']:
    usedata = prunedata[prunedata['spec']==spec]

    #prune confidence to just closest one
    confnum = [float(i.split('f')[1]) for i in allconf]
    
    #get average precision and recall at conf closest to confth
    confnum = np.array(confnum)[np.argsort(confnum)]
    confuse = next(x[0] for x in enumerate(confnum) if float(x[1])>=confth)
    colrec = 'conf'+str(confnum[confuse])+'_tp'
    colpre = 'conf'+str(confnum[confuse])+'_pre'
    
    precdata.append(usedata[colpre].values[0])
    recdata.append(usedata[colrec].values[0])

precdata = np.array(precdata)
recdata = np.array(recdata)


f=0.5
fscore5 = (f**2 + 1) * (precdata * recdata / (f**2 * precdata + recdata))


#add in number of examples from in same order as prune data- these values can be verified in S2 Table 
nexamp = [366,333,458,73,
          473,255,462,513,
          340,229,277,529,
          429,707,853,667]


#correlations
print(pearsonr(nexamp,precdata))
print(pearsonr(nexamp,recdata))
print(pearsonr(nexamp,fscore5))


#create plots
#precision
plt.plot(nexamp,precdata,'.')
plt.xlabel('Number of training examples')
plt.ylabel('Precision')
for i, txt in enumerate(prunedata['spec']):
    plt.annotate(txt, (nexamp[i], precdata[i]))
plt.show()

#recall
plt.plot(nexamp,recdata,'.')
plt.xlabel('Number of training examples')
plt.ylabel('Recall')
for i, txt in enumerate(prunedata['spec']):
    plt.annotate(txt, (nexamp[i], recdata[i]))
plt.show()


#fscore
plt.plot(nexamp,fscore5,'.')
plt.xlabel('Number of training examples')
plt.ylabel('F0.5-Score')
for i, txt in enumerate(prunedata['spec']):
    plt.annotate(txt, (nexamp[i], fscore5[i]))
plt.show()

