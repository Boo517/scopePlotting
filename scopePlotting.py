# -*- coding: utf-8 -*-
"""
Created on Mon Jul 31 11:30:36 2023

@author: P3 Lab Office
"""

import numpy as np
import tkinter as tk
from tkinter import filedialog

"""
FILE IMPORT
"""
#this dictionary gives which column a certain data channel lies on
#woulda used an enum if they existed in python
columns = {
    'sample' : 0,   #a string, either "DSO1" or "DSO2" and its sample #
    'trigger' : 1,  #[V]trigger signal
    'rog1' : 2,     #[V]rogowski coil 1
    'rog2' : 3,     #[V]rogowski coil 2
    'diode' : 4,    #[V]diode for laser timing
    'time' : 9      #[ps] timestamp of sample
    }

#TODO: file select
root = tk.Tk()
root.withdraw()
file_path = filedialog.askopenfilename()
#take only data columns pertaining to Bertha
data1 = np.genfromtxt('test.txt', skip_header=2, delimiter=',',
                     usecols=(columns['trigger'], columns['rog1'], 
                              columns['rog2'], columns['diode'], 
                              columns['time']))
#remove DSO2 rows, where all Bertha signals are nan, avoiding interpolation
data1 = np.delete(data1, np.isnan(data1[:,0]), 0)
