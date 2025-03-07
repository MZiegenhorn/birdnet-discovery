#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This code runs HDBSCAN clustering for a folder (or folder of subfolders) of birdnet embeddings, and outputs spectrogram images of what is stored in each cluster, as well as txt files for each cluster of the times associated with the images. These txt files can be used to extract wav snippets corresponding to all audio in a given cluster. 

@author: maziegenhorn


"""


#reset environment
from IPython import get_ipython;   
get_ipython().magic('reset -sf')
get_ipython().magic('clear')


#required packages
import scipy.signal
from pathlib import Path
import os
from scipy.spatial import distance
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import math as mt
import librosa
from itertools import compress
import hdbscan
import scipy.sparse.linalg



####  settings  ################

# file paths
#path to embeddings
embroot = Path("~/shortDeps/bbnet_output")
#path to labels- if no labels, ALL embeddings will be clustered. This may be quite slow. 
#code is set up for labels to be stored in same folder/subfodler structure as embeddings
labelroot = embroot 
#path to raw wav files (used to create spectrograms)- should have same folder/subfolder structure as embroot
wavroot = Path("~/shortDeps/wavs")
fsuse = 16000 #sampling frequency of your audio files, in Hz
#where to save output 
outroot = embroot/'clusters' 

# settings for label pruning- only in effect if label files are found 
labmethod = 'label' #options are 'label' for basing on a target label, otherwise 'confidence' for pruning low-confidence embeddings
targ = 'bird' #birdnet label for target class. Will be ignored if label files are not present.
conf = 0.9 #only keep embeddings above this label confidence level. Used with labmethod 'confidence'. NOT TESTED.

# settings for spectrogram-MODIFY WITH CAUTION
nfft = 512 
hop_length = int(nfft*.5) # number of samples to hop over before next nfft

# settings for clustering
minsize = 5 #minimum number of embeddings in a cluster to keep that cluster. 
clusterMethod = 'leaf' #see HDBSCAN clustering for setting this parameter. Leaf clustering will preserve small clusters, which may help identify less common signal types in the data, but results in a larger number of clusters to review. 


################ functions #######################3

def get_distmat(features):
    
    nimage = len(features)
    distance_matrix = np.zeros((nimage, nimage))

    for i in range(nimage):
        feati = features[i].T
        for k in range(i):
            featk = features[k].T
            # measure Jensen–Shannon distance between each feature vector
            # and add to the distance matrix
            distance_matrix[i,k] = distance.jensenshannon(feati,featk)

    # symmetrize the matrix as distance matrix is symmetric
    distmatrix = np.maximum(distance_matrix, distance_matrix.transpose())
    return distmatrix



################### main code ##############################

#get list of deployments in folder
foldlist = os.listdir(embroot) #assume same structure for embfolder,labfolder, and wavfolder

for dep in foldlist:
    #verify embeddings present
    embfolder = embroot/dep
    emblist = list(embfolder.glob('*embeddings.txt'))
    
    if not emblist:
        print('no embeddings found in folder! Skipping '+dep)
    else:
        
        
        ########### combine embeddings across all files in folder ###############
        
        #if embeddings present, continue
        outpath = outroot/dep
        wavfolder = wavroot/dep 
        
        #get label list and wav list
        lablist = list(embfolder.glob('*results.csv'))
        wavlist = list(wavfolder.glob('*.[Ww][Aa][Vv]'))
        
        #if root destination exists, print a warning that clusters will be overwritten
        if os.path.exists(outpath):
            print('Already clusters present for '+dep+'. Overwriting... ')
        
        
        #for each embedding, extract the vectors and add them 
        starts = []; stops =[]; plotspecs = []; wvname = []
        if 'embed' in globals():
            del embed
        
        for embfile in emblist:
            embs = pd.read_table(embfile,names=["start","stop","embedding"])
                
            embtemp = embs["embedding"]; startsall = embs["start"]; endsall = embs["stop"]
            
            #check if there's any wav corresponding, otherwise skip file
            embshort = embfile.name.split('.birdnet')[0]
            wavmatch = [embshort in i.name for i in wavlist]
            wavuse = list(compress(wavlist,wavmatch))
                
            if not wavuse:
                print('No matching wav file found for embedding '+embfile.name)
            else:
            
                #if label list is not empty, look for match and use it to prune embeddings
                if not lablist:
                    if embfile == emblist[0]:
                        #only print on first iteration
                        print('WARNING: No labels provided! All embeddings will be clustered- this may be very slow.')
                    useidx = np.linspace(0,len(startsall)-1,len(startsall))
                    
                else:
                   
                    labmatch = [embshort in i.name for i in lablist]
                    #grab correct label file
                    labuse = list(compress(lablist,labmatch))
                    
                    if labuse:
                        predtab = pd.read_csv(labuse[0])
                        #get useidx
                        times = list(embs["start"])
                        labtimes = predtab["Start (s)"]
                        
                        if labmethod == 'label':
                            #extract target signals
                            keepidx = [targ in i for i in predtab["Common name"]]
                        elif labmethod == 'confidence':
                            #extract high-confidence signals
                            keepidx = [i >= conf for i in predtab["Confidence"]]
                            
                        keeptimes = list(compress(labtimes,keepidx))
                        useidx = [times.index(il) for il in keeptimes]
    
                if not useidx:
                    print('No usable signals in file '+embfile.name)
                    
                else:
                    embkeep = embtemp[useidx]
                    emb2 = np.array([i.split(',') for i in embkeep])
                    #convert to float
                    embsall = np.asfarray(emb2)
        
                    #add embeddings to list, unless it's empty
                    if not 'embed' in globals():
                        embed = embsall
                    else:
                        embed = np.concatenate((embed,embsall),axis=0)
                    
                        
                    #load wav file and compute spectrograms
                    s,fs = librosa.load(wavuse[0],sr=fsuse)
            
 
                    for s1 in startsall[useidx]:
                        #truncate to correct point
                        sind = s1*fs; eind = (s1+3)*fs
                        wavtr = s[mt.floor(sind):mt.ceil(eind)]
    
                        #compute spectrogram
                        win = np.hanning(nfft)
                        sFFT = scipy.signal.ShortTimeFFT(win, hop=hop_length,fs=fs,mfft=nfft)
                        spectemp = abs(sFFT.stft(wavtr))
                        speclog = np.log(spectemp + 1e-9)
                        specnorm = (speclog - speclog.min())/(speclog.max()-speclog.min())
                        specnorm = np.flip(specnorm,axis=0)
                
                        #add to growing list
                        plotspecs.append(specnorm)
                        wvname.append(wavuse[0])
                
    
                    starts.extend(startsall[useidx])
                    stops.extend(endsall[useidx])
                    
                    print('Done with file '+embfile.name)

        
        ############## clustering ######################

        #get distance matrix for the vectors
        embmat = get_distmat(embed)
        # you can plot the embeddings themselves if you uncomment the line below, if you're curious what they look like in 2D space
        #plt.scatter(embmat[0],embmat[1])
        
        #HDBSCAN clustering-this may be slow to run if you have a lot of data points 
        labs = hdbscan.HDBSCAN(min_cluster_size=minsize,
                             cluster_selection_method=clusterMethod).fit_predict(embmat) 
        
        nclus = len(pd.unique(labs))
        clus = pd.unique(labs)
        print('Num of clusters ',str(nclus))
        
        #create root destination
        os.makedirs(outpath)
        
        #save images for each cluster
        for icl in range(nclus):
        
            clususe= list(compress(plotspecs,labs==clus[icl]))
            timesuse = list(compress(starts,labs==clus[icl]))
            wvuse = list(compress(wvname,labs==clus[icl]))
            
            #truncate cluster -1 if it's too big. This cluster stores embeddings that didn't cluster, and so it can end up quite large. If it gets too big, the invidual images are impossible to see. That's why this is here. 
            nimg = len(clususe)
            if (clus[icl] == -1) & (nimg > 500):
                print('Too many images in clus -1. Truncating from '+str(nimg))
                clususe = clususe[0:500]
                nimg = len(clususe)
                
                
            #determine nimages for plotting 
            ncol = int(np.ceil(np.sqrt(nimg)))
            nrow = int(np.ceil(nimg/ncol))
            
            #plotting
            fig = plt.figure(figsize=(24, 24))
            plt.title('Cluster '+str(clus[icl]))
            k = 0
            
            for ini in range(nimg):
                # display original image
                fig.add_subplot(nrow,ncol,ini+1)
                plt.imshow(clususe[ini])
                plt.axis("off")
                
            #save image of this cluster
            imname = 'Cluster'+str(clus[icl])+'.png'
            outfile = outpath/imname
            plt.savefig(outfile)
            plt.close()
        
            #save times (in seconds) for each cluster, with label, in its own text file 
            clustab = pd.DataFrame({'Wavfile':wvuse,
                                    'Start time':timesuse,
                                    'Cluster':str(clus[icl])})
            
            #setup output name
            outname = dep+'_Cluster'+str(clus[icl])+'_times.txt'
            outdetsfile = outpath/outname
            clustab.to_csv(outdetsfile,sep='\t',index=False)
        
        
    print('Done with folder '+dep)

    
