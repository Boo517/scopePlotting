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
#import scipy as sp
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
    filepath = tkFileDialog.askopenfilename(parent=root,title='Pick a file')    
    return filepath 

#take only 9 data columns (of 10 total) from selected file, 
#ignoring the 'sample' column
filepath = getfile()
data = np.genfromtxt(filepath, skip_header=2, delimiter=',',
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
#and reassigning the names doesn't change this I think? (garbage collection?)
#meaning these arrays take up twice as much memory as they need to
#BUT that probably doesn't matter much

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
#this function returns a vector the same shape as y(t) containing the 
#cumulative trapezoidal integration of y(t) over the time vector t
#with initial value 0 
def cumtrapz(t, y):
    dt = np.diff(t)     #timesteps
    integration = np.cumsum(dt*(y[0:-1]+y[1:])/2)
    return np.concatenate(([0.0], integration))

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

#test my code by comparing it to scipy
#UPDATE 8-28-23, resulted in same array, so my function is good
# i1_test = sp.integrate.cumtrapz(rog1*R1, time1, initial=0)
# i2_test = sp.integrate.cumtrapz(rog2*R2, time1, initial=0)
# print(np.array_equal(i1, i1_test))
# print(np.array_equal(i2, i2_test))

#plot current curves for the first 5 microseconds
peak_mask = np.logical_and(time1>0, time1<5*10**-6)    #mask to get first 5 us
fig, (ax3,ax4)= plt.subplots(2,1)
ax3.plot(time1[peak_mask], i1[peak_mask], label="Rogowski 1")
ax3.plot(time1[peak_mask], i2[peak_mask], label="Rogowski 2")
ax3.set_xlabel("Time after Trigger [s]")
ax3.set_ylabel("Current [A]")
ax3.legend()


i_total = i1-i2     #i2 is flipped (negative voltage for positive current)
ax4.plot(time1[peak_mask], i_total[peak_mask], label="Total Current")
ax4.set_xlabel("Time after Trigger [s]")
ax4.set_ylabel("Current [A]")
ax4.legend()

#Output peak current, current start time and risetime to screen
peak_current = max(i_total)
peak_time = time1[i_total==peak_current][0]
#get start time by extrapolating from linear region (current rise like sin^2)
#start_time = 
risetime = peak_time

print("Peak Current: {:.4f} kA at t = {:.4f} microseconds after trigger"
      .format(peak_current/10**3, peak_time*10**6))
print("Rise time: {:.4f} nanoseconds".format(risetime*10**9))


"""
DATA EXPORT
"""
#export data for plots to text file for Origin import
export_array = np.concatenate((
    i_total[np.newaxis].T, DSO1, DSO2), 1) #horizontal cat
#NOTE: new data array has 11 columns from the original 9, as the time column
#has been split in 2 and a new column has been added for the total current
np.savetxt(filepath[:-4]+" formatted.csv", export_array)
#TODO: decide if this cumbersome 18-digit scientific notation is what we want
#and csv vs txt (currently using csv just for distinguishing from scope out)

"""
REFERENCE DICT FOR WRITTEN FILE FORMAT
columns = {
    'current' : 0   #[A]total current
    'trigger' : 1,  #[V]trigger signal
    'rog1_raw' : 2, #[V]rogowski coil 1
    'rog2_raw' : 3, #[V]rogowski coil 2
    'diode' : 4,    #[V]diode for laser timing
    'time1' : 5,    #[s]timestamp of samples for DSO1
    'DSO21': 6,
    'DSO22' : 7,
    'DSO23' : 8,
    'DSO24' : 9,
    'time2' : 10    #[s]timestamp of samples for DSO2
    }
"""

