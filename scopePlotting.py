# -*- coding: utf-8 -*-
"""
Created on Mon Jul 31 11:30:36 2023

@author: P3 Lab Office
"""
#-----------------------------------------------------------------------------#
"""
IMPORTS
"""
import numpy as np
import matplotlib.pyplot as plt
import tkinter as Tkinter, tkinter.filedialog as tkFileDialog
#-----------------------------------------------------------------------------#
""" 
EXPERIMENTAL VALUES
"""
dB1 = 19.82         #attenuation in decibels for BRog1
dB2 = 19.49         #attenuation in decibels for BRog2
BR1 = 765500000     #Rogowski coil coefficient for BRog1
BR2 = 820000000     #Rogowski coil coefficient for BRog2
#-----------------------------------------------------------------------------#
"""
FILE IMPORT
"""
def getfile():
    root = Tkinter.Tk()
    root.after(100, root.focus_force)
    root.after(200,root.withdraw)    
    file_path = tkFileDialog.askopenfilename(parent=root,title='Pick a file')    
    return file_path 

#take only 9 data columns (of 10 total) from selected file, 
#ignoring the 'sample' column
data = np.genfromtxt(getfile(), skip_header=2, delimiter=',',
                     usecols=range(1,10))

#this dictionary gives which column a certain data channel lies on in the
#data array 
#woulda used an enum if they existed in python
columns = {
    'trigger' : 0,  #[V]trigger signal
    'rog1_raw' : 1,     #[V]Bertha rogowski coil 1
    'rog2_raw' : 2,     #[V]Bertha rogowski coil 2
    'diode' : 3,    #[V]diode for laser timing
    'DSO21': 4,
    'DSO22' : 5,
    'DSO23' : 6,
    'DSO24' : 7,
    'time' : 8      #[ps]timestamp of sample
    }

#-----------------------------------------------------------------------------#
"""
SEPARATE SCOPE DATA
"""
#unpack data into arrays based on which scope it's from
#in order to avoid the timing mismatch problem (2 separate time columns)
#doing this instead of interpolation to avoid creating new datapoints
DSO1 = data[:, 
            [*range(columns['trigger'], columns['diode']+1)]+[columns['time']]]
DSO2 = data[:, 
            [*range(columns['DSO21'], columns['time']+1)]]
#take only rows where signals aren't nan, using first data column to check
DSO1 = DSO1[~np.isnan(DSO1[:,0]), :]
DSO2 = DSO2[~np.isnan(DSO2[:,0]), :]
#NOTE: the slice creates a view of og data array (like a ref)

"""
PLOT
"""
#plot raw voltage data
trigger = DSO1[:,0]
rog1_raw = DSO1[:,1]
rog2_raw = DSO1[:,2]
diode = DSO1[:,3]
bertha_time = DSO1[:,4]*10**-6     #[ps]->[us]

fig, (ax1,ax2) = plt.subplots(2,1)
ax1.plot(bertha_time, trigger, label="Trigger")
ax1.plot(bertha_time, diode, label="Diode")
ax1.set_xlabel("Time after Trigger [us]")
ax1.set_ylabel("Voltage [V]")
ax1.legend()

ax2.plot(bertha_time, rog1_raw, label="Rogowski 1")
ax2.plot(bertha_time, rog2_raw, label="Rogowski 2")
ax2.set_xlabel("Time after Trigger [us]")
ax2.set_ylabel("Voltage [V]")
ax2.legend()
plt.show()

"""
ROGOWSKI ANALYSIS
"""
#get actual rogowski voltages, accounting for attenuation
rog1 = rog1_raw*10**(dB1/20)
rog2 = rog2_raw*10**(dB1/20)
#integrate Rogowski voltages to get currents

#Output peak current, current start time and risetime to screen

"""
DATA EXPORT
"""
#export data for plots to text file for Origin import
export_array = np.concatenate((DSO1, DSO2), 1) # concatenate horizontally

