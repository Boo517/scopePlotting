# -*- coding: utf-8 -*-
"""
Created on Mon Jul 31 11:30:36 2023

@author: P3 Lab Office
"""

# %%
"""
IMPORTS
"""
import numpy as np
#import scipy as sp
import matplotlib.pyplot as plt
import tkinter as Tkinter, tkinter.filedialog as tkFileDialog

# %%
""" 
EXPERIMENTAL VALUES
"""
dB1 = 26        #attenuation in decibels for BRog1
dB2 = 26        #attenuation in decibels for BRog2
R1 = 816000000     #Rogowski coil coefficient for BRog1
R2 = 1000000000     #Rogowski coil coefficient for BRog2

# %%
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
folder = '/'.join(filepath.split('/')[:-1]) + '/'
data = np.genfromtxt(filepath, skip_header=2, delimiter=',',
                     usecols=range(1,10))

#this dictionary gives which column a certain data channel lies on in the
#data array 
#woulda used an enum if they existed in python
columns = {
    'trigger' : 0,      #[V]trigger signal
    'rog1_raw' : 1,     #[V]Bertha rogowski coil 1
    'rog2_raw' : 2,     #[V]Bertha rogowski coil 2
    'diode' : 3,        #[V]diode for laser timing
    'DSO21': 4,
    'DSO22' : 5,
    'DSO23' : 6,
    'DSO24' : 7,
    'time' : 8          #[ps]timestamp of sample
    }

# %%
"""
SEPARATE SCOPE DATA
"""
#unpack data into 2 arrays based on scope which recorded it
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

# %%
"""
PLOT RAW VOLTAGE DATA
"""
trigger = DSO1[:,0]
rog1_raw = DSO1[:,1]
rog2_raw = DSO1[:,2]
diode = DSO1[:,3]
time1 = DSO1[:,4]
time1 = time1*10**-12     #[ps]->[s]

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

#save figure as png
plt.savefig(folder+"raw_plots")

# %%
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
  
#a DC voltage offset in the raw rogowski data results in a linear current slope
#when current should actually be 0.
#By subtracting this offset from the voltages before integrating, 
#we get a signal which starts at 0 current before the shot, 
#then returns to 0 after settling following the shot
#(assuming the offset doesn't change over the course of the experiment)
#UPDATE 8-30-23: regarding this^, it seems that the DC offset does frequently 
#jump in a discrete step, sometimes long before and other times long after 
#peak current. To deal with this, the averaging used to find the offset 
#is calculated just before current starts. This hopefully means that 
#total current is accurate for the window of interest, from current start to
#around 5 us after peak. If the step occurs before averaging, it has no
#effect, and if it occurs after the window of interest, it just results in 
#a very apparent nonphysical linear current slope at a time past where we care

#take the average of the pre-current rogowski values 
#to find the DC offset and subtract it before integrating
#NOTE: not averaging for all pretrigger time anymore, because it was far enough
#from the actual current rise that changes in noise and dc offset resulted
#in an inaccurate calibration (see above text wall of DOOM)
rog1_peak_time = time1[rog1 == max(rog1)][0]
averaging_time = 4*10**-6       #[s]
prepeak_spacing = .8*10**-6     #[s]spacing from peak so averaging doesn't
                                #occur after current start. >expected risetime
avg_end = rog1_peak_time -  prepeak_spacing
avg_start = avg_end - averaging_time
precurrent = np.logical_and(time1>=avg_start, time1<=avg_end)   
#NOTE: right now, just taking .8 us before max rog1 voltage as time to stop
#averaging for finding DC offset, with fixed 2 us of averaging time
#for future reference: could be better to adjust averaging time based on 
#period of noise and use a more robust method than a fixed offset for finding 
#current start time

dc1 = np.mean(rog1[precurrent])     #DC offset is average voltage pre-current
dc2 = np.mean(rog2[precurrent])
rog1 -= dc1     #subtract the DC offsets
rog2 -= dc2

#integrate Rogowski voltages to get currents
int_mask = time1>avg_start  #integrate only after when DC offset calibrated
i1 = cumtrapz(time1[int_mask], rog1[int_mask]*R1)
i2 = cumtrapz(time1[int_mask], rog2[int_mask]*R2)
#pad with zeros to reach length of other arrays for export
num_zeros = len(time1) - len(i1)
i1 = np.pad(i1, (num_zeros,0))
i2 = np.pad(i2, (num_zeros,0))
i_total = i1-i2     #i2 is flipped (negative voltage for positive current)

#test my code by comparing it to scipy
#UPDATE 8-28-23, resulted in same array, so my function is good
# i1_test = sp.integrate.cumtrapz(rog1*R1, time1, initial=0)
# i2_test = sp.integrate.cumtrapz(rog2*R2, time1, initial=0)
# print(np.array_equal(i1, i1_test))
# print(np.array_equal(i2, i2_test))

# %%
"""
PEAK CURRENT AND RISE TIME
"""
peak_current = max(i_total)
peak_time = time1[i_total==peak_current][0]
peak_mask = np.logical_and(time1>=0, time1<=peak_time)

#get start time by extrapolating from linear region (current rise like sin^2)
#mask for indices in linear region where we will do regression
linear_mask = np.logical_and(i_total[peak_mask]<=0.8*peak_current,   
                              i_total[peak_mask]>=0.2*peak_current)  
#NOTE: without restricting linear_mask to peak_mask (0-peak current),
#linear_mask will include the current ramp down after peak, which we don't want  
time1_linear = time1[peak_mask][linear_mask]
i_linear = i_total[peak_mask][linear_mask]

#y = mx + c = [x, 1][m, c].T = A*[m, c]
#numpy least squares function gives m, c given A, y
A = np.vstack((time1_linear, np.ones(len(time1_linear)))).T     
m, c = np.linalg.lstsq(A, i_linear, rcond=None)[0]

#y = mx + c = m(x + c/m), so -c/m is zero-crossing
start_time = -c/m
risetime = peak_time - start_time

#Output peak current, current start time and risetime to screen
print("Peak Current: {:.4f} kA at t = {:.4f} microseconds after trigger"
      .format(peak_current/10**3, peak_time*10**6))
print("Current Start: t = {:.4f} microseconds after trigger"
      .format(start_time*10**6))
print("Rise time: {:.4f} nanoseconds".format(risetime*10**9))


# %%
"""
PLOTTING CURRENT
"""
#plot current through both Rogowskis
fig, (ax3,ax4)= plt.subplots(2,1)
ax3.plot(time1, i1, label="Rogowski 1")
ax3.plot(time1, i2, label="Rogowski 2")

ax3.set_xlabel("Time after Trigger [s]")
ax3.set_ylabel("Current [A]")
ax3.legend()

ax4.plot(time1, i_total, label="Total Current")
#plot fit line over current plot
extrapolate_mask = np.logical_and(time1[peak_mask]>=start_time, 
                                  i_total[peak_mask]<=0.8*peak_current)
time1_fit = time1[peak_mask][extrapolate_mask]
ax4.plot(time1_fit, m*time1_fit + c, '--', label="Linear Fit")
ax4.plot(start_time, 0, 'x', label="Current Start")
ax4.plot(peak_time, peak_current, 'x', label="Peak Current")

plot_xlim = peak_time + 5*10**-6    #plot from trigger to 5 us after peak
plot_ylim = peak_current    #plot from 0 to peak current
ax4.set_xlim([0, plot_xlim])
ax4.set_ylim([-.1*plot_ylim, plot_ylim*1.1])    #give 10% of peak as padding
ax4.set_xlabel("Time after Trigger [s]")
ax4.set_ylabel("Current [A]")
ax4.legend()

#save figure as png
plt.savefig(folder+"currrent_plots")

# %%
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
    'current' : 0   #[A]total current from integrated Rogowskis 1 and 2
    'trigger' : 1,  #[V]trigger signal
    'rog1_raw' : 2, #[V]rogowski coil 1
    'rog2_raw' : 3, #[V]rogowski coil 2
    'diode' : 4,    #[V]diode for laser timing
    'time1' : 5,    #[ps]timestamp of samples for DSO1
    'DSO21': 6,
    'DSO22' : 7,
    'DSO23' : 8,
    'DSO24' : 9,
    'time2' : 10    #[ps]timestamp of samples for DSO2
    }
"""

