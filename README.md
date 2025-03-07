# birdnet-discovery
This repository contains all code related to the pipeline for signal discovery/training data creation outlined in Ziegenhorn et al. (2025):

Ziegenhorn, Morgan A. and Lanctot, Richard B. and Brown, Stephen C. and Brengle, Miles and Schulte, Shiloh and Saalfeld, Sarah T. and Latty, Christopher J. and Smith, Paul A. and Lecomte, Nicolas, Arcticsoundsnet: Birdnet Embeddings Facilitate Improved Bioacoustic Classification of Arctic Species. Available at SSRN: https://ssrn.com/abstract=5135160 or http://dx.doi.org/10.2139/ssrn.5135160

**PLEASE NOTE** Large files associated with this repository cannot be appropriately stored on GitHub, and are instead available on Dryad at: 



Any questions or concerns can be directed to Morgan Ziegenhorn at maziegenhorn36@gmail.com or directly via the GitHub page associated with this repository: https://github.com/MZiegenhorn/birdnet-discovery. All python scripts provided in the birdnet-discovery repository were written and run using Spyder IDE (v5.5.1). 


# Introduction

The following fully describes the pipeline for training data creation developed in Ziegenhorn et al. (2025) as well as all code and data provided in the birdnet-discovery repository. 

The purpose of this pipeline is to derive high-quality, comprehensive training data from an unlabelled dataset of raw audio files for downstream classification tasks using embeddings from a BirdNET-based classifier. In Ziegenhorn et al. (2025), this process is used to create a training dataset from a large-scale monitoring effort in northern Alaska encompassing 8+ TB of acoustic data from approximately 150 recording locations. 

The core of the birdnet-discovery pipeline uses the HDBSCAN clustering method (see CITE for details) to cluster embeddings in 2D space and then saves those results for manual review. This non-deterministic method of signal discovery means that target classes DO NOT need to be known prior to pipeline utilization. We developed this method with the knowledge that those involved in acoustic monitoring regimes may not often have a target species but rather be interested in targeting ALL acoustically active species in the study area, without prior knowledge of what those species might be. Conversely, monitoring efforts may be focused on target species for which limited (or no) training data is currently available (e.g., Arctic breeding shorebirds). Our method of employing clustering for signal discovery and training data development is broadly applicable to these downstream goals, as well as potentially others.

While the code developed for this pipeline is optimized for use with BirdNET, the overall scheme could be adapted to work with embeddings from other models (e.g., Perch). Likewise, the output of this pipeline (the final training data) is optimized to train a custom classifier with BirdNET as a base but could be transferred to any desired framework. Code and data used to do this in Ziegenhorn et al. (2025) to produce and evaluate ArcticSoundsNET are included in this repository and detailed at the end of this README. For details on the equipment used, and relevant settings, for the example audio recording files provided in this repository, and all methods employed here, please see Ziegenhorn et al. (2025). 

Throughout this README…

Paths to data files provided in this repository are *written in italics when referenced*. 

Paths to code provided in this repository **are bold when referenced**. 


# Getting started with BirdNET

This pipeline was developed for use with BirdNET-Analyzer’s command line interface code. The most up-to-date version of BirdNET-Analyzer can be found on GitHub at: https://github.com/kahst/BirdNET-Analyzer?tab=readme-ov-file#training. Full documentation on how to download, install, and use BirdNET-Analyzer in command line (regardless of operating system) can be accessed from that page. Please refer to their comprehensive guide for all steps related to model training (train.py) and classification (analyze.py and embeddings.py) referenced in this document. 

While this guide is for use with command line BirdNET-Analyzer in mind, it may be possible to run BirdNET-related steps in other versions such as the GUI. However, this has not been tested. 

Once you have BirdNET-Analyzer installed, we recommend running the most up-to-date model on at least a subset of your data and examining the labels provided by analyze.py in your preferred software (e.g. Audacity, Raven Lite, Raven Pro, Kaleidoscope Pro). Understanding your data and the performance of your chosen model (e.g., base BirdNET, or potentially another model from which you have embeddings) may significantly inform how you use this pipeline.


# Working with embeddings

If you are unfamiliar with the magic of embeddings, here is a brief definition: in machine learning, embeddings are a low-dimensional representation of your data learned by a given model. In 2D space, the distance between embeddings from each data segment your model classifies (e.g., 3-second segments for BirdNET, 5-second segments for Perch) should be shorter for similar segments (e.g., two songs from a singing bird) and larger for dissimilar segments (e.g., a barking dog and a singing bird). To get embeddings from BirdNET, you will run embeddings.py rather than analyze.py on your acoustic data files (see BirdNET-Analyzer documentation for details on running both embeddings.py and analyze.py in command line, including relevant settings).  



# Clustering embeddings

As mentioned, this pipeline hinges on the use of the HDBSCAN clustering algorithm to distill embeddings from your full dataset into clusters of self-similar audio signals, some of which may be of interest/target species. This process is advantageous because it is non-deterministic; the number of desired clusters is not set ahead of time, and nothing need be known about the target signals when getting started. 

Once you have model embeddings from your raw audio data, these can be clustered using **~/code/cluster_run_HDBSCAN.py**. This script requires as input:

1)	Path to your embeddings files
2)	Path to your audio files (.WAV or .wav, though modification for other audio input types should be relatively simple!)

and will output:

1)	Spectrogram images of data put into each cluster
2)  Text files that list the audio file, start time, and cluster label for all data segments in a given cluster, which can be used to extract audio segments for manual review and/or training data development (see below)

## Some notes on **cluster_run_HDBSCAN.py**…

This script was optimized to create clusters from an input folder of short (300 second) audio files, such that clusters are created at the level of the folder instead of for each individual audio file. Running at the individual file level would make the initial clustering process much faster but would result in a very large number of clusters that need to then be manually reviewed. 

The downside of this process is that clustering on many files at once is computationally costly and may overly tax the memory of your computing system. In Ziegenhorn et al. (2025), this cost was minimized in the following ways:

1)	File subsetting: As our dataset was well over 8 TB, clustering across embeddings from every file in the full dataset was not feasible. We subsetted files across all plots with acoustic ARUs to only include data from morning hours (6-9 AM local time), as this active period covered vocal activity of all target species (Arctic birds). We verified this by examining a small subset of data from other time periods from files from many plots and found that there were no signal types that were common outside of this high-activity period that were common during other times of day (e.g., no nocturnal-only callers). An example of this short dataset from one of our Arctic plots, and the code used to produce it, is included in this repository (*~/shortDeps/TLSA_2023_AL54*, **~/code/cluster_pruneFiles_to_shortDeps.py**). 

Other methods of subsetting may include randomly choosing files from throughout the day or not including data from every study plot/acoustic instrument. Determining how to subset your data, if subsetting is necessary, will be dependent on your study system and survey regime. 

2)	Pre-labeling data: Another potential avenue for minimizing clustering and review time is providing BirdNET labels along with embeddings to **clusters_run_HDBSCAN.py**. This allows pruning of unwanted labels (e.g., restricting embeddings to data segments where a bird was present) or pruning based on low-confidence detection (e.g., restricting embeddings to data segments with a BirdNET confidence score of > 0.9). 

This process requires a separate run of analyze.py through the BirdNET-Analyzer library, which will output both labels and label confidence scores for your raw data files. These labels can then be provided as input to **cluster_run_HDBSCAN.py** to prune out non-useful embeddings before clustering occurs. 

A caveat of this process is that this type of pruning only works well if the base BirdNET algorithm can successfully detect your target signals. In the case of Ziegenhorn et al. (2025), this was not true, and it was necessary to build an intermediary model (binary BirdNET, or asnet_binary) using a small, weakly labelled training data (‘bird’, ‘rain’, and ‘background’) to obtain labels for use with **clusters_run_HDBSCAN.py**. This model (*~/models/asnet_binary.tflite*) and its associated training data (*~/asnet_binary_training_data*) are provided for reference and reproducibility. For details on how to train a similar model and training settings, see Ziegenhorn et al. (2025) and the BirdNET documentation page. While this step may take extra time on the front-end, it may drastically reduce the time spent on manual review of clusters later on. 

Embeddings and labels for our data using the asnet_binary model were then extracted by running BirdNET-Analyzer embeddings.py and analyze.py in command line with a custom classifier option. 

An example of the output of this process (using asnet_binary as the classification model) for data from a single instrument, TLSA_2023_AL54, can be found in this repository at *~/shortDeps/asnet_binary_output/TLSA_2023_AL54*. An example of the output of **cluster_run_HDBSCAN.py** can be found in this repository at *~/shortDeps/asnet_binary_output/clusters*.

# Cluster review and training data distillation

Output clusters from cluster_run_HDBSCAN.py can be reviewed using Preview (macOS) or any other image-viewing software. We provide example clusters from one Arctic study plot, TLSA_2023_AL54. During visual review, we kept a spreadsheet of cluster labels to determine which clusters to keep, discard, or review additionally using Raven Lite or similar. We include a template, *~cluster_typeAssign.csv*, that can be used for your own review. This spreadsheet includes the following columns: 

1)	**Folder**: The name of the folder in which a given set of cluster image/text files are saved 
2)	**Cluster**: The number of the cluster you are referencing (included in the file name for each cluster image file, and as a title on the image itself)
3)	**Label**: The label you want to assign images to this cluster to in your training data  

This template spreadsheet is set up for use with the cluster assignment script (**~/code/cluster_assign_trainingLabels.py**). This script uses clustering output in conjunction with the spreadsheet to truncate raw files into audio clips that are sorted according to the labels provided and stored in the specified output folder. An example of the output from this script is provided at *~/shortDeps/asnet_binary_output/new_trainingData*. 

**note**: while our cluster_typeAssign.csv template file only includes data from a single folder, you may run through as many as you wish and input a single csv into the cluster assignment script. The correct clips from audio files will be chosen accordingly. 

In our work, we assigned clips that merited further review to the ‘review’ category. These can be reviewed using Raven Lite software (or the software of your choice) to determine their final label. This is advantageous especially when target signals may not be recognizable on sight from spectrogram images. When starting out, most clusters (that are not messy, faint, overly noisy, or of non-target signals) may be assigned to the ‘review’ class. As you progress through your cluster review, and begin defining and re-defining types, you will likely recognize some types by sight and no longer need to specifically review those files. Once final labels are decided, the CSV file can be modified and cluster_assign_trainingLabels.py may be run again to re-categorize clusters accordingly. See the following example:

If study species in your system are not well-known to you upon starting out, you might begin with something like this:

 ![image](https://github.com/user-attachments/assets/865b3cab-173f-4e96-9227-792a0068f98c)

Here, we have one cluster that we know is Lapland longspur (‘LALO’), several others that we’d like to review (‘review’), and four clusters that we can distinguish but do not know the identity of (‘type1’, ‘type2’). As we progress through manual review of clusters in this folder and others, we can re-contextualize these clusters and assign more of them to particular species or species’ groups:

![image](https://github.com/user-attachments/assets/8aaee15a-9173-47d4-823e-c29128b2d272)

In this case, we learned upon further data exploration that type1 was a call from the willow ptarmigan (WIPT), type2 a call from the american golden-plover (AMGP), and clusters 0 and 16 have been defined to additional species (red-throated loon and parasitic jaeger). Cluster 20 was removed after review as it was determined it was a poorer example of a class for which we already had robust training data (black-bellied plover). 

The data segments distilled and labelled from this process can then be used for training a classification model that is optimized for your dataset. In Ziegenhorn et al. (2025), this process was used to create the training data for ArcticSoundsNET, which was built as a custom classifier using BirdNET as a base model (same general process as for developing asnet_binary described above). However, the training data produced by this pipeline is broadly usable for transfer learning using other base models, and, by conserving raw audio for training, is agnostic of model architecture (i.e., your model architecture using your developed training dataset does not need to be a convolutional neural network like BirdNET or utilize spectrogram images as the primary means of classification). 

We hope birdnet-discovery will greatly improve your ability to develop training data for your acoustic dataset! Please get in touch with questions, comments, and suggestions. The final section of this document details code and data related to performance of ArcticSoundsNET and Ziegenhorn et al. (2025) that is not elsewhere highlighted in the README. 

 
# Additional data and code:

Repository paths and descriptions of all other code and data related to the process of training and evaluating the final ArcticSoundsNET model described in Ziegenhorn et al. (2025):

*~/asnet_final_training_data*: Full training data for final ArcticSoundsNET model 

*~/models/asnet_final.tflite*: Final ArcticSoundsNET tflite model (this folder also includes label and params files)

*~/ground_truth/wavs*: Full audio files for ground truth dataset

*~/ground_truth/manuals_all_labels_clean.csv*: Compiled CSV of manual annotations from all expert reviewers across the full ground truth dataset

*~/ground_truth/allManuals_combined.csv*: Final manual annotation sheet used in performance evaluations

**~/code/perf_combineManuals.py**: code used to convert manuals_all_labels_clean.csv to allManuals_combined.csv

*~/species_list_forBirdNET.txt*: Custom species list provided to base BirdNET when comparing performance on ground truth data to that of ArcticSoundsNET

*~/specCodes.csv*: Evaluation codes for use with performance scripts

*~/base_bnet_labels*: Base BirdNET labels for all ground truth files

*/asnet_final_labels*: ArcticSoundsNET labels for all ground truth files

**~/code/perf_forAUC.py**: Performance code used to accumulate results used by perf_table1_metrics.py

**~/code/perf_table1_metrics.py**: Performance code used to produce data in Ziegenhorn et al. (2025) Table 1 

**~/code/perf_table2_metrics.py**: Performance code used to produce all data in Ziegenhorn et al. (2025) Table 2 (and total number of model detections in Table 1)

**~/code/perf_fig3.py**: Code to produce Ziegenhorn et al. (2025) Figure 3

