# birdnet-discovery
This repository contains all code related to the pipeline for signal discovery/training data creation outlined in Ziegenhorn et al. (2025) 


# Introduction

The following fully describes the pipeline for training data creation developed in Ziegenhorn et al. (2025) as well as all code and data provided in the birdnet-discovery repository. 

The purpose of this pipeline is to derive high-quality, comprehensive training data from an unlabelled dataset of raw audio files for downstream classification tasks using embeddings from a BirdNET-based classifier. In Ziegenhorn et al. (2025), this process is used to create a training dataset from a large-scale monitoring effort in northern Alaska encompassing 8+ TB of acoustic data from approximately 150 recording locations. 

The core of the birdnet-discovery pipeline uses the HDBSCAN clustering method (see CITE for details) to cluster embeddings in 2D space and then saves those results for manual review. This non-deterministic method of signal discovery means that target classes DO NOT need to be known prior to pipeline utilization. We developed this method with the knowledge that those involved in acoustic monitoring regimes may not often have a target species but rather be interested in targeting ALL acoustically active species in the study area, without prior knowledge of what those species might be. Conversely, monitoring efforts may be focused on target species for which limited (or no) training data is currently available (e.g., Arctic breeding shorebirds). Our method of employing clustering for signal discovery and training data development is broadly applicable to these downstream goals, as well as potentially others.

While the code developed for this pipeline is optimized for use with BirdNET, the overall scheme could be adapted to work with embeddings from other models (e.g., Perch). Likewise, the output of this pipeline (the final training data) is optimized to train a custom classifier with BirdNET as a base but could be transferred to any desired framework. Code and data used to do this in Ziegenhorn et al. 2025 to produce and evaluate ArcticSoundsNET are included in this repository and detailed at the end of this README. For details on the equipment used, and relevant settings, for the example audio recording files provided in this repository, and all methods employed here, please see Ziegenhorn et al. (2025). 

Any questions or concerns can be directed to Morgan Ziegenhorn at maziegenhorn36@gmail.com or directly via the GitHub page associated with this repository: https://github.com/MZiegenhorn/birdnet-discovery. All python scripts provided in the birdnet-discovery repository were written and run using Spyder IDE (v5.5.1). 

Throughout this README…

Paths to data files provided in this repository are written in italics when referenced. 

Paths to code provided in this repository are underlined when referenced. 


# Getting started with BirdNET

This pipeline was developed for use with BirdNET-Analyzer’s command line interface code. The most up-to-date version of BirdNET-Analyzer can be found at GitHub at: https://github.com/kahst/BirdNET-Analyzer?tab=readme-ov-file#training. Full documentation on how to download, install, and use BirdNET-Analyzer in command line (regardless of operating system) can be accessed from that page. Please refer to their comprehensive guide for all steps related to model training (train.py) and classification (analyze.py and embeddings.py) referenced in this document. 

While this guide is for use with command line BirdNET-Analyzer in mind, it may be possible to run BirdNET-related steps in other versions such as the GUI. However, this has not been tested. 

Once you have BirdNET installed, we recommend running the most up-to-date model on at least a subset of your data and examining the labels provided by analyze.py in your preferred software (e.g. Audacity, Raven Lite, Raven Pro, Kaleidoscope Pro). Understanding your data and the performance of your chosen model (e.g., base BirdNET, or potentially another model from which you have embeddings) may significantly inform how you use this pipeline.
![image](https://github.com/user-attachments/assets/1fbbe4f0-0d7f-42c9-b300-fc9b875d38b1)
