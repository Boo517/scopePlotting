# -*- coding: utf-8 -*-
"""
Created on Mon Jul 31 11:30:36 2023

@author: P3 Lab Office
"""

import numpy as np

"""
FILE IMPORT
"""
def getfile():
    import tkinter as Tkinter, tkinter.filedialog as tkFileDialog
    root = Tkinter.Tk()
    root.after(100, root.focus_force)
    root.after(200,root.withdraw)    
    file_path = tkFileDialog.askopenfilename(parent=root,title='Pick a file')    
    return file_path 

#this dictionary gives which column a certain data channel lies on in the
#data array 
#woulda used an enum if they existed in python
columns = {
    'trigger' : 0,  #[V]trigger signal
    'rog1' : 1,     #[V]rogowski coil 1
    'rog2' : 2,     #[V]rogowski coil 2
    'diode' : 3,    #[V]diode for laser timing
    'DSO21': 4,
    'DSO22' : 5,
    'DSO23' : 6,
    'DSO24' : 7,
    'time' : 8      #[ps]timestamp of sample
    }

#take only 9 data columns (of 10 total) from selected file 
data = np.genfromtxt(getfile(), skip_header=2, delimiter=',',
                     usecols=range(1,10))
# take data pertaining to Bertha
bertha_data = data[:, (columns['trigger'], columns['rog1'], columns['rog2'], 
                       columns['diode'], columns['time'])]
#remove DSO2 rows, where all Bertha signals are nan, avoiding interpolation
bertha_data = np.delete(bertha_data, np.isnan(bertha_data[:,0]), 0)
#NOTE: the slice is mutable, but delete() creates a copy
