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
dB1 = 26        #attenuation in decibels for BRog1
dB2 = 26        #attenuation in decibels for BRog2
R1 = 816000000     #Rogowski coil coefficient for BRog1
R2 = 1000000000     #Rogowski coil coefficient for BRog2
#-----------------------------------------------------------------------------#
"""
FILE IMPORT
"""
#this function opens a file select dialog through Tkinter and returns 
#the path to the selected file
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
#and reassigning the names doesn't change this I think? (garbage collector?)
#TODO: see if this is true, and free up that space (the NaN rows) if it is

"""
PLOT
"""
#plot raw voltage data
trigger = DSO1[:,0]
rog1_raw = DSO1[:,1]
rog2_raw = DSO1[:,2]
diode = DSO1[:,3]
time1 = DSO1[:,4]*10**-12     #[ps]->[s]

fig, (ax1,ax2) = plt.subplots(2,1)
ax1.plot(time1, trigger, label="Trigger")
ax1.plot(time1, diode, label="Diode")
ax1.set_xlabel("Time after Trigger [s]")
ax1.set_ylabel("Voltage [V]")
ax1.legend()

ax2.plot(time1, rog1_raw, label="Rogowski 1")
ax2.plot(time1, rog2_raw, label="Rogowski 2")
ax2.set_xlabel("Time after Trigger [s]")
ax2.set_ylabel("Voltage [V]")
ax2.legend()
plt.show()

"""
ROGOWSKI ANALYSIS
"""
#this function returns a vector containing the 
#cumulative trapezoidal integration of y(t) over the time vector t
def cumtrapz(t, y):
    dt = np.diff(t)     #timesteps
    return np.cumsum(dt*(y[0:-1]+y[1:])/2)

#get actual rogowski voltages, accounting for attenuation
#using the formula 'attenuation[dB] = 20*log(V_in/V_out)'
rog1 = rog1_raw*10**(dB1/20)
rog2 = rog2_raw*10**(dB2/20)

#before and long after the trigger, when current should be 0, 
#there is a very linear slope on the integrated rogowski curves. 
#This is probably due to a DC voltage offset and so by subtracting this offset 
#from the voltages before integrating, we get a signal which 
#starts at 0 current until the trigger, 
#then returns to 0 after settling following the shot

#take the average of the pre-trigger rogowski values
#to find the DC offset and subtract it before integrating
pretrigger = time1<0    #trigger is t=0, so pre-trig is everything < 0
dc1 = np.mean(rog1[pretrigger])     #DC offset is average voltage pre-trigger
dc2 = np.mean(rog2[pretrigger])
rog1 -= dc1     #subtract the DC offset
rog2 -= dc2


#integrate Rogowski voltages to get currents
i1 = cumtrapz(time1, rog1*R1)
i2 = cumtrapz(time1, rog2*R2)

#plot current curves
fig, (ax3,ax4)= plt.subplots(2,1)
ax3.plot(time1[1:], i1, time1[1:], i2)
i_total = i1-i2     #i2 is flipped (negative voltage for positive current)
ax4.plot(time1[1:], i_total)

#Output peak current, current start time and risetime to screen

"""
DATA EXPORT
"""
#export data for plots to text file for Origin import
export_array = np.concatenate((DSO1, DSO2), 1) # concatenate horizontally

