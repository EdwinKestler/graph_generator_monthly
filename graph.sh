#!/bin/bash

directory="/home/charmeleon/Documents/INSIVUMEH/git/graph_generator_monthly"
fecha=$date

#cd $directory && python $directory/downloadwithlink.py && python $directory/dataset.py && python $directory/dataset2.py &&
cd $directory && git add . && 
git commit -m "upgrade" && git push origin main

