#!/usr/bin/env python
"""
Copyright Netherlands eScience Center

Function        : Regression of climatological variable on OMET (GLORYS2V3) with whitening
Author          : Yang Liu
Date            : 2017.11.10
Last Update     : 2017.11.10
Description     : The code aims to explore the association between climatological
                  variables with oceanic meridional energy transport (OMET).
                  The statistical method employed here is linear regression. A
                  number of fields (SST, SLP, Sea ice, geopotential, etc.),
                  corresponding to the pre-existing natural modes of variability,
                  will be projected on meridional energy transport. This will enhance
                  our understanding of climate change. Notice that the time series
                  of input data will be whitened (the seasonal cycles are removed).
                  The fields come from ERA-Interim surface level data, from 1993-2014.

Return Value    : Map of correlation
Dependencies    : os, time, numpy, scipy, netCDF4, matplotlib, basemap
variables       : Sea Surface Temperature                       SST
                  Sea Level Pressure                            SLP
                  Sea Ice Concentration                         ci
                  Oceanic meridional energy transport           OMET
Caveat!!        : The input data of OMET is from 30 deg north to 90 deg north (Northern Hemisphere).
"""

import numpy as np
import scipy as sp
from scipy import stats
import time as tttt
from netCDF4 import Dataset,num2date
import os
import seaborn as sns
import platform
import logging
#import matplotlib
# Generate images without having a window appear
#matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap, cm

# print the system structure and the path of the kernal
print platform.architecture()
print os.path

# calculate the time for the code execution
start_time = tttt.time()
# switch on the seaborn effect
sns.set()

################################   Input zone  ######################################
# specify data path
# OMET
datapath_OMET = 'F:\DataBase\HPC_out\GLORYS2V3\postprocessing'
# target climatological variables
datapath_y = "F:\DataBase\ERA_Interim\Monthly"
# specify output path for figures
output_path = 'C:\Yang\PhD\Computation and Modeling\Blue Action\OMET\GLORYS2V3'
# the threshold ( index of latitude) of the OMET
lat_OMET = 788 # at 60 N
# the range ( index of latitude) of the projection field
lat_y = 94 # upto 20 N
####################################################################################
print '*******************************************************************'
print '*********************** extract variables *************************'
print '*******************************************************************'
# ORCA025_z75 grid infor (Madec and Imbard 1996)
ji = 1440
jj = 1021
level = 75
# zonal integral
dataset_OMET = Dataset(datapath_OMET + os.sep + 'GLORYS2V3_model_monthly_orca025_E_zonal_int.nc')
dataset_y = Dataset(datapath_y + os.sep + 'surface_monthly_regress_variables_197901-201612.nc')
for k in dataset_OMET.variables:
    print dataset_OMET.variables['%s' % (k)]

for l in dataset_y.variables:
    print dataset_y.variables['%s' % (l)]

# extract Oceanic meridional energy transport
# dimension (year,month,latitude)
OMET = dataset_OMET.variables['E'][:,:,lat_OMET]/1000 # from Tera Watt to Peta Watt # start from 1993
# extract variables from 20N to 90 N
# sea level pressure
SLP = dataset_y.variables['msl'][168:432,0:lat_y+1,:] # from 1993 - 2014
# sea surface temperature
SST = dataset_y.variables['sst'][168:432,0:lat_y+1,:]
mask_SST = np.ma.getmaskarray(SST[0,:,:])
# sea ice cover
ci = dataset_y.variables['ci'][168:432,0:lat_y+1,:]
mask_ci = np.ma.getmaskarray(ci[0,:,:])
# longitude
lon = dataset_y.variables['longitude'][:]
# latitude
lat = dataset_y.variables['latitude'][0:lat_y+1]
# time (number of months)
time = dataset_y.variables['time'][:]

print 'The type of SLP is', type(SLP)
print 'The type of SST is', type(SST)
print 'The type of ci is', type(ci)

print '*******************************************************************'
print '*********************** prepare variables *************************'
print '*******************************************************************'
# take the time series of E
OMET_series = OMET.reshape(264)

print '*******************************************************************'
print '*************************** whitening *****************************'
print '*******************************************************************'
# remove the seasonal cycling of target climatology for regression
# These climitology data comes from ERA-Interim surface level
month_ind = np.arange(12)
# remove climatology for Sea Level Pressure
SLP_seasonal_mean = np.zeros((12,lat_y+1,len(lon))) # from 20N - 90N
SLP_white = np.zeros(SLP.shape,dtype=float)
for i in month_ind:
    # calculate the monthly mean (seasonal cycling)
    SLP_seasonal_mean[i,:,:] = np.mean(SLP[i:-1:12,:,:],axis=0)
    # remove seasonal mean
    SLP_white[i:-1:12,:,:] = SLP[i:-1:12,:,:] - SLP_seasonal_mean[i,:,:]

# remove climatology for Sea Surface Temperature
SST_seasonal_mean = np.zeros((12,lat_y+1,len(lon))) # from 20N - 90N
SST_white = np.zeros(SST.shape,dtype=float)
for i in month_ind:
    # calculate the monthly mean (seasonal cycling)
    SST_seasonal_mean[i,:,:] = np.mean(SST[i:-1:12,:,:],axis=0)
    # remove seasonal mean
    SST_white[i:-1:12,:,:] = SST[i:-1:12,:,:] - SST_seasonal_mean[i,:,:]

# remove climatology for Sea Ice Concentration
ci_seasonal_mean = np.zeros((12,lat_y+1,len(lon))) # from 20N - 90N
ci_white = np.zeros(ci.shape)
for i in month_ind:
    # calculate the monthly mean (seasonal cycling)
    ci_seasonal_mean[i,:,:] = np.mean(ci[i:-1:12,:,:],axis=0)
    # remove seasonal mean
    ci_white[i:-1:12,:,:] = ci[i:-1:12,:,:] - ci_seasonal_mean[i,:,:]

# remove the seasonal cycling of OMET at 60N
# dimension of OMET[year,month]
OMET_seansonal_cycle = np.mean(OMET,axis=0)
OMET_white = np.zeros(OMET.shape,dtype=float)
for i in month_ind:
    OMET_white[:,i] = OMET[:,i] - OMET_seansonal_cycle[i]

# take the time series of whitened OMET
OMET_white_series = OMET_white.reshape(264)

print '*******************************************************************'
print '********************** Running mean/sum ***************************'
print '*******************************************************************'
# running mean is calculated on time series
# define the running window for the running mean
window = 60 # in month
# calculate the running mean and sum of OMET
OMET_running_mean = np.zeros(len(OMET_series)-window+1)
#OMET_running_sum = np.zeros(len(OMET_series)-window+1)
for i in np.arange(len(OMET_series)-window+1):
    OMET_running_mean[i] = np.mean(OMET_series[i:i+window])
    #OMET_running_sum[i] = np.sum(OMET_series[i:i+window])

# calculate the running mean and sum of OMET after removing the seasonal cycling
OMET_white_running_mean = np.zeros(len(OMET_white_series)-window+1)
#OMET_running_sum = np.zeros(len(OMET_series)-window+1)
for i in np.arange(len(OMET_white_series)-window+1):
    OMET_white_running_mean[i] = np.mean(OMET_white_series[i:i+window])
    #OMET_white_running_sum[i] = np.sum(OMET_white_series[i:i+window])

print '*******************************************************************'
print '*************************** time series ***************************'
print '*******************************************************************'
# index and namelist of years for time series and running mean time series
index = np.arange(1,265,1)
index_year = np.arange(1993,2015,1)

index_running_mean = np.arange(1,265-window+1,1)
index_year_running_mean = np.arange(1993+window/12,2015,1)

# plot the OMET after removing seasonal cycle
fig1 = plt.figure()
plt.plot(index,OMET_white_series,'b-',label='GLORYS2V3')
plt.title('Oceanic Meridional Energy Transport Anomaly at 60N (1993-2014)')
#plt.legend()
fig1.set_size_inches(12, 5)
plt.xlabel("Time")
plt.xticks(np.linspace(0, 264, 23), index_year)
plt.xticks(rotation=60)
plt.ylabel("Meridional Energy Transport (PW)")
plt.show()
fig1.savefig(output_path + os.sep + 'regression' + os.sep + 'OMET_anomaly_60N_time_series_1993_2014.jpg', dpi = 500)

# plot the running mean of OMET after removing seasonal cycle
fig0 = plt.figure()
plt.plot(index_running_mean,OMET_white_running_mean,'b-',label='GLORYS2V3')
plt.title('Running Mean of OMET Anomalies at 60N with a window of %d months (1993-2014)' % (window))
#plt.legend()
fig0.set_size_inches(12, 5)
plt.xlabel("Time")
plt.xticks(np.linspace(0, 265-window, 23-window/12), index_year_running_mean)
plt.xticks(rotation=60)
plt.ylabel("Meridional Energy Transport (PW)")
plt.show()
fig0.savefig(output_path + os.sep + 'regression' + os.sep +'OMET_anomaly_60N_running_mean_window_%d_only.jpg' % (window), dpi = 500)

# plot the OMET with running mean
fig2 = plt.figure()
plt.plot(index,OMET_series,'b--',label='time series')
plt.plot(index[window-1:],OMET_running_mean,'r-',linewidth=2.0,label='running mean')
plt.title('Running Mean of OMET at 60N with a window of %d months (1993-2014)' % (window))
#plt.legend()
fig2.set_size_inches(12, 5)
plt.xlabel("Time")
plt.xticks(np.linspace(0, 264, 23), index_year)
plt.xticks(rotation=60)
plt.ylabel("Meridional Energy Transport (PW)")
plt.show()
fig2.savefig(output_path + os.sep + 'regression' + os.sep +'OMET_60N_running_mean_window_%d_comp.jpg' % (window), dpi = 500)

# plot the OMET after removing the seasonal cycling with running mean
fig3 = plt.figure()
plt.plot(index,OMET_white_series,'b--',label='time series')
plt.plot(index[window-1:],OMET_white_running_mean,'r-',linewidth=2.0,label='running mean')
plt.title('Running Mean of OMET Anomalies at 60N with a window of %d months (1993-2014)' % (window))
#plt.legend()
fig3.set_size_inches(12, 5)
plt.xlabel("Time")
plt.xticks(np.linspace(0, 264, 23), index_year)
plt.xticks(rotation=60)
plt.ylabel("Meridional Energy Transport (PW)")
plt.show()
fig3.savefig(output_path + os.sep + 'regression' + os.sep + 'OMET_anomaly_60N_running_mean_window_%d_comp.jpg' % (window), dpi = 500)

print '*******************************************************************'
print '********************* Fourier transform ***************************'
print '*******************************************************************'
# Fast Fourier Transform of OMET
FFT_OMET = np.fft.fft(OMET_series)
freq_FFT_OMET = np.fft.fftfreq(len(FFT_OMET),d=1)
mag_FFT_OMET = abs(FFT_OMET)
# Plot OMET in Frequency domain
fig4 = plt.figure()
plt.plot(freq_FFT_OMET[0:200],mag_FFT_OMET[0:200],'b-',label='GLORYS2V3')
plt.title('Fourier Transform of OMET at 60N (1993-2014)')
#plt.legend()
fig4.set_size_inches(12, 5)
plt.xlabel("Times per month")
#plt.xticks(np.linspace(0, 456, 39), index_year)
#plt.xticks(rotation=60)
plt.ylabel("Power spectrum density (PW^2/month)")
plt.show()
fig4.savefig(output_path + os.sep + 'regression' + os.sep + 'OMET_60N_FFT_1993_2014.jpg', dpi = 500)

# Fast Fourier Transform of OMET anomalies
FFT_OMET_white = np.fft.fft(OMET_white_series)
freq_FFT_OMET_white = np.fft.fftfreq(len(FFT_OMET_white),d=1)
mag_FFT_OMET_white = abs(FFT_OMET_white)
# Plot the anomaly of OMET in Frequency domain
fig5 = plt.figure()
plt.plot(freq_FFT_OMET_white[0:200],mag_FFT_OMET_white[0:200],'b-',label='GLORYS2V3')
plt.title('Fourier Transform of OMET Anomaly at 60N (1993-2014)')
#plt.legend()
fig5.set_size_inches(12, 5)
plt.xlabel("Times per month")
#plt.xticks(np.linspace(0, 456, 39), index_year)
#plt.xticks(rotation=60)
plt.ylabel("Power spectrum density (PW^2/month)")
plt.show()
fig5.savefig(output_path + os.sep + 'regression' + os.sep + 'OMET_anomaly_60N_FFT_1993_2014.jpg', dpi = 500)

# Plot the running mean of OMET anomaly in Frequency domain
FFT_OMET_white_running_mean = np.fft.fft(OMET_white_running_mean)
freq_FFT_OMET_white_running_mean = np.fft.fftfreq(len(FFT_OMET_white_running_mean),d=1)
mag_FFT_OMET_white_running_mean = abs(FFT_OMET_white_running_mean)
# Plot the running mean of OMET in Frequency domain
fig6 = plt.figure()
plt.plot(freq_FFT_OMET_white_running_mean[0:60],mag_FFT_OMET_white_running_mean[0:60],'b-',label='GLORYS2V3')
plt.title('Fourier Transform of Running Mean (%d) of OMET Anomalies at 60N (1993-2014)' % (window))
#plt.legend()
fig6.set_size_inches(12, 5)
plt.xlabel("Times per month")
#plt.xticks(np.linspace(0, 456, 39), index_year)
#plt.xticks(rotation=60)
plt.ylabel("Power spectrum density (PW^2/month)")
plt.show()
fig6.savefig(output_path + os.sep + 'regression' + os.sep + 'OMET_anomaly_60N_FFT_running_mean_%d_1993_2014.jpg' % (window), dpi = 500)

print '*******************************************************************'
print '**************************** trend ********************************'
print '*******************************************************************'
# the calculation of trend are based on target climatolory after removing seasonal cycles
# trend of SLP
# create an array to store the slope coefficient and residual
a = np.zeros((lat_y+1,len(lon)),dtype = float)
b = np.zeros((lat_y+1,len(lon)),dtype = float)
# the least square fit equation is y = ax + b
# np.lstsq solves the equation ax=b, a & b are the input
# thus the input file should be reformed for the function
# we can rewrite the line y = Ap, with A = [x,1] and p = [[a],[b]]
A = np.vstack([index,np.ones(len(index))]).T
# start the least square fitting
for i in np.arange(lat_y+1):
    for j in np.arange(len(lon)):
        # return value: coefficient matrix a and b, where a is the slope
        a[i,j], b[i,j] = np.linalg.lstsq(A,SLP_white[:,i,j])[0]
# visualization through basemap
fig7 = plt.figure()
# setup north polar stereographic basemap
# resolution c(crude) l(low) i(intermidiate) h(high) f(full)
# lon_0 is at 6 o'clock
m = Basemap(projection='npstere',boundinglat=60,round=True,lon_0=0,resolution='l')
# draw coastlines
m.drawcoastlines(linewidth=0.25)
# fill continents, set lake color same as ocean color.
# m.fillcontinents(color='coral',lake_color='aqua')
# draw parallels and meridians
m.drawparallels(np.arange(20,81,10),fontsize = 7,linewidth=0.75)
m.drawmeridians(np.arange(0,360,30),labels=[1,1,1,1],fontsize = 7,linewidth=0.75)
# x,y coordinate - lon, lat
xx, yy = np.meshgrid(lon,lat)
XX, YY = m(xx, yy)
# define color range for the contourf
color = np.linspace(-60,60,25) # for SLP
# !!!!!take care about the coordinate of contourf(Longitude, Latitude, data(Lat,Lon))
#cs = m.contour(XX,YY,a*12,color)
#plt.clabel(cs, fontsize=7, inline=1)
cs = m.contourf(XX,YY,a*12*10,color,cmap='coolwarm')
# add color bar
cbar = m.colorbar(cs,location="bottom",size='4%',pad="8%",format='%d')
cbar.ax.tick_params(labelsize=8)
#cbar.set_ticks(np.arange(-1,1.1,0.2))
#cbar.set_ticklabels(np.arange(-1,1.1,0.2))
cbar.set_label('Pa/Decade',fontsize = 8)
plt.title('Trend of Sea Level Pressure Anomalies (1993-2014)',fontsize = 9, y=1.05)
plt.show()
fig7.savefig(output_path + os.sep + 'regression' + os.sep + "Trend_ERAI_SLP.jpeg",dpi=500)

# trend of SST
# start the least square fitting
for i in np.arange(lat_y+1):
    for j in np.arange(len(lon)):
        # return value: coefficient matrix a and b, where a is the slope
        a[i,j], b[i,j] = np.linalg.lstsq(A,SST_white[:,i,j])[0]
# visualization through basemap
fig8 = plt.figure()
m = Basemap(projection='npstere',boundinglat=60,round=True,lon_0=0,resolution='l')
# draw coastlines
m.drawcoastlines(linewidth=0.25)
# fill continents, set lake color same as ocean color.
# m.fillcontinents(color='coral',lake_color='aqua')
# draw parallels and meridians
m.drawparallels(np.arange(20,81,10),fontsize = 7,linewidth=0.75)
m.drawmeridians(np.arange(0,360,30),labels=[1,1,1,1],fontsize = 7,linewidth=0.75)
# x,y coordinate - lon, lat
xx, yy = np.meshgrid(lon,lat)
XX, YY = m(xx, yy)
# define color range for the contourf
color = np.linspace(-1.0,1.0,21)
# !!!!!take care about the coordinate of contourf(Longitude, Latitude, data(Lat,Lon))
cs = m.contourf(XX,YY,np.ma.masked_where(mask_SST,a*12*10),color,cmap='coolwarm')
# add color bar
cbar = m.colorbar(cs,location="bottom",size='4%',pad="8%",format='%.1f')
cbar.ax.tick_params(labelsize=8)
cbar.set_label('Celsius/Decade',fontsize = 8)
plt.title('Trend of Sea Surface Temperature Anomalies (1993-2014)',fontsize = 9, y=1.05)
plt.show()
fig8.savefig(output_path + os.sep + 'regression' + os.sep + "Trend_ERAI_SST.jpeg",dpi=500)

# trend of Sea Ice concentration
# start the least square fitting
for i in np.arange(lat_y+1):
    for j in np.arange(len(lon)):
        # return value: coefficient matrix a and b, where a is the slope
        a[i,j], b[i,j] = np.linalg.lstsq(A,ci_white[:,i,j])[0]
# visualization through basemap
fig9 = plt.figure()
m = Basemap(projection='npstere',boundinglat=60,round=True,lon_0=0,resolution='l')
# draw coastlines
m.drawcoastlines(linewidth=0.25)
# fill continents, set lake color same as ocean color.
# m.fillcontinents(color='coral',lake_color='aqua')
# draw parallels and meridians
m.drawparallels(np.arange(20,81,10),fontsize = 7,linewidth=0.75)
m.drawmeridians(np.arange(0,360,30),labels=[1,1,1,1],fontsize = 7,linewidth=0.75)
# x,y coordinate - lon, lat
xx, yy = np.meshgrid(lon,lat)
XX, YY = m(xx, yy)
# define color range for the contourf
color = np.linspace(-0.18,0.18,19)
# !!!!!take care about the coordinate of contourf(Longitude, Latitude, data(Lat,Lon))
cs = m.contourf(XX,YY,np.ma.masked_where(mask_ci,a*12*10),color,cmap='coolwarm')
# add color bar
cbar = m.colorbar(cs,location="bottom",size='4%',pad="8%",format='%.3f')
cbar.ax.tick_params(labelsize=8)
cbar.set_ticks(np.arange(-0.18,0.20,0.06))
cbar_labels = ['-18%','-12%','-6%','0%','6%','12%','18%']
cbar.ax.set_xticklabels(cbar_labels)
cbar.set_label('Percentage/Decade',fontsize = 8)
plt.title('Trend of the Sea Ice Concentration Anomalies (1993-2014)',fontsize = 9, y=1.05)
plt.show()
fig9.savefig(output_path + os.sep + 'regression' + os.sep + "Trend_ERAI_Ice.jpeg",dpi=500)

print '*******************************************************************'
print '************************** regression *****************************'
print '*******************************************************************'
# calculate the standard deviation of OMET anomaly
OMET_white_std = np.std(OMET_white_series)
print 'The standard deviation of OMET anomaly is (in peta Watt):'
print OMET_white_std
# all the regression are taken on anomalies of variables
# this is because the seasonal cycles are always too strong

# variables to be projected (array size the same as)
#SLP_white_selected = SLP_white[:,0:lat_y+1,:]
#SST_white_selected = SST_white[:,0:lat_y+1,:]
#ci_white_selected = ci_white[:,0:lat_y+1,:]

# create an array to store the correlation coefficient
slope = np.zeros((lat_y+1,len(lon)),dtype = float)
r_value = np.zeros((lat_y+1,len(lon)),dtype = float)
p_value = np.zeros((lat_y+1,len(lon)),dtype = float)

# linear regress SLP on OMET (anomalies)
# plot correlation coefficient
for i in np.arange(lat_y+1):
    for j in np.arange(len(lon)):
        # return value: slope, intercept, r_value, p_value, stderr
        slope[i,j],_,r_value[i,j],p_value[i,j],_ = stats.linregress(OMET_white_series,SLP_white[:,i,j])
# visualization through basemap
fig10 = plt.figure()
# setup north polar stereographic basemap
# resolution c(crude) l(low) i(intermidiate) h(high) f(full)
# lon_0 is at 6 o'clock
m = Basemap(projection='npstere',boundinglat=60,round=True,lon_0=0,resolution='l')
# draw coastlines
m.drawcoastlines(linewidth=0.25)
# fill continents, set lake color same as ocean color.
# m.fillcontinents(color='coral',lake_color='aqua')
# draw parallels and meridians
m.drawparallels(np.arange(60,81,10),fontsize = 7,linewidth=0.75)
m.drawmeridians(np.arange(0,360,30),labels=[1,1,1,1],fontsize = 7,linewidth=0.75)
# x,y coordinate - lon, lat
xx, yy = np.meshgrid(lon,lat[0:lat_y+1])
XX, YY = m(xx, yy)
# define color range for the contourf
color = np.linspace(-0.25,0.25,11)
# !!!!!take care about the coordinate of contourf(Longitude, Latitude, data(Lat,Lon))
cs = m.contourf(XX,YY,r_value,color,cmap='coolwarm')
# add color bar
cbar = m.colorbar(cs,location="bottom",size='4%',pad="8%",format='%.2f')
cbar.ax.tick_params(labelsize=8)
cbar.set_label('Correlation Coefficient',fontsize = 8)
# fancy layout of maps
# label of contour lines on the map
#plt.clabel(cs,incline=True, format='%.1f', fontsize=12, colors='k')
# draw significance stippling on the map
# locate the indices of p_value matrix where error p<0.05 (99.5% confident)
i, j = np.where(p_value<=0.05)
# get the coordinate on the map (lon,lat) and plot scatter dots
m.scatter(XX[i,j],YY[i,j],2.2,marker='.',color='g',alpha=0.6, edgecolor='none') # alpha bleding factor with map
plt.title('Regression of SLP Anomaly on OMET Anomaly across 60 N',fontsize = 9, y=1.05)
plt.show()
fig10.savefig(output_path + os.sep + 'regression' + os.sep + "Regression_OMET_SLP_ERAI_white_correlation_coef.jpeg",dpi=500)

# plot regression coefficient
fig11 = plt.figure()
# setup north polar stereographic basemap
m = Basemap(projection='npstere',boundinglat=60,round=True,lon_0=0,resolution='l')
# draw coastlines
m.drawcoastlines(linewidth=0.25)
# draw parallels and meridians
m.drawparallels(np.arange(60,81,10),fontsize = 7,linewidth=0.75)
m.drawmeridians(np.arange(0,360,30),labels=[1,1,1,1],fontsize = 7,linewidth=0.75)
# x,y coordinate - lon, lat
xx, yy = np.meshgrid(lon,lat[0:lat_y+1])
XX, YY = m(xx, yy)
# define color range for the contourf
color = np.linspace(-2.2,2.2,23) # SLP_white
# !!!!!take care about the coordinate of contourf(Longitude, Latitude, data(Lat,Lon))
cs = m.contourf(XX,YY,slope/1000,color,cmap='coolwarm') # unit from Pa to kPa
# add color bar
cbar = m.colorbar(cs,location="bottom",size='4%',pad="8%",format='%.1f')
cbar.ax.tick_params(labelsize=8)
cbar.set_label('Regression Coefficient kPa/PW',fontsize = 8)
i, j = np.where(p_value<=0.05)
# get the coordinate on the map (lon,lat) and plot scatter dots
m.scatter(XX[i,j],YY[i,j],2.2,marker='.',color='g',alpha=0.6, edgecolor='none') # alpha bleding factor with map
plt.title('Regression of SLP Anomaly on OMET Anomaly across 60 N',fontsize = 9, y=1.05)
plt.show()
fig11.savefig(output_path + os.sep + 'regression' + os.sep + "Regression_OMET_SLP_ERAI_white_regression_coef.jpeg",dpi=500)

# linear regress SST on OMET (anomalies)
# plot correlation coefficient
for i in np.arange(lat_y+1):
    for j in np.arange(len(lon)):
        # return value: slope, intercept, r_value, p_value, stderr
        slope[i,j],_,r_value[i,j],p_value[i,j],_ = stats.linregress(OMET_white_series,SST_white[:,i,j])
# visualization through basemap
fig12 = plt.figure()
# setup north polar stereographic basemap
m = Basemap(projection='npstere',boundinglat=60,round=True,lon_0=0,resolution='l')
# draw coastlines
m.drawcoastlines(linewidth=0.25)
# draw parallels and meridians
m.drawparallels(np.arange(60,81,10),fontsize = 7,linewidth=0.75)
m.drawmeridians(np.arange(0,360,30),labels=[1,1,1,1],fontsize = 7,linewidth=0.75)
# x,y coordinate - lon, lat
xx, yy = np.meshgrid(lon,lat[0:lat_y+1])
XX, YY = m(xx, yy)
# define color range for the contourf
color = np.linspace(-0.3,0.3,21) # SST_white
# !!!!!take care about the coordinate of contourf(Longitude, Latitude, data(Lat,Lon))
cs = m.contourf(XX,YY,np.ma.masked_where(mask_SST,r_value),color,cmap='coolwarm') # SST_white
# add color bar
cbar = m.colorbar(cs,location="bottom",size='4%',pad="8%",format='%.2f')
cbar.ax.tick_params(labelsize=8)
#cbar.set_ticks(np.arange(-1,1.1,0.2))
#cbar.set_ticklabels(np.arange(-1,1.1,0.2))
cbar.set_label('Correlation Coefficient',fontsize = 8)
# locate the indices of p_value matrix where p<0.05 (99.5% confident)
p_value[mask_SST==1] = 1.0
i, j = np.where(p_value<=0.05)
# get the coordinate on the map (lon,lat) and plot scatter dots
m.scatter(XX[i,j],YY[i,j],2.2,marker='.',color='g',alpha=0.6, edgecolor='none') # alpha bleding factor with map
plt.title('Regression of SST Anomaly on OMET Anomaly across 60 N ',fontsize = 9, y=1.05)
plt.show()
fig12.savefig(output_path + os.sep + 'regression' + os.sep + "Regression_OMET_SST_ERAI_white_correlation_coef.jpeg",dpi=500)

# plot regression coefficient
fig13 = plt.figure()
# setup north polar stereographic basemap
m = Basemap(projection='npstere',boundinglat=60,round=True,lon_0=0,resolution='l')
# draw coastlines
m.drawcoastlines(linewidth=0.25)
# draw parallels and meridians
m.drawparallels(np.arange(60,81,10),fontsize = 7,linewidth=0.75)
m.drawmeridians(np.arange(0,360,30),labels=[1,1,1,1],fontsize = 7,linewidth=0.75)
# x,y coordinate - lon, lat
xx, yy = np.meshgrid(lon,lat[0:lat_y+1])
XX, YY = m(xx, yy)
# define color range for the contourf
color = np.linspace(-5.0,5.0,21)
# !!!!!take care about the coordinate of contourf(Longitude, Latitude, data(Lat,Lon))
cs = m.contourf(XX,YY,slope,color,cmap='coolwarm')
# add color bar
cbar = m.colorbar(cs,location="bottom",size='4%',pad="8%",format='%.1f')
cbar.ax.tick_params(labelsize=8)
cbar.set_label('Regression Coefficient Celsius/PW',fontsize = 8)
p_value[mask_SST==1] = 1.0
i, j = np.where(p_value<=0.05)
# get the coordinate on the map (lon,lat) and plot scatter dots
m.scatter(XX[i,j],YY[i,j],2.2,marker='.',color='g',alpha=0.6, edgecolor='none') # alpha bleding factor with map
plt.title('Regression of SST Anomaly on OMET Anomaly across 60 N',fontsize = 9, y=1.05)
plt.show()
fig13.savefig(output_path + os.sep + 'regression' + os.sep + "Regression_OMET_SST_ERAI_white_regression_coef.jpeg",dpi=500)

# linear regress Sea Ice Concentration on OMET (anomalies)
# plot correlation coefficient
for i in np.arange(lat_y+1):
    for j in np.arange(len(lon)):
        # return value: slope, intercept, r_value, p_value, stderr
        slope[i,j],_,r_value[i,j],p_value[i,j],_ = stats.linregress(OMET_white_series,ci_white[:,i,j])
# visualization through basemap
fig14 = plt.figure()
# setup north polar stereographic basemap
m = Basemap(projection='npstere',boundinglat=60,round=True,lon_0=0,resolution='l')
# draw coastlines
m.drawcoastlines(linewidth=0.25)
# draw parallels and meridians
m.drawparallels(np.arange(60,81,10),fontsize = 7,linewidth=0.75)
m.drawmeridians(np.arange(0,360,30),labels=[1,1,1,1],fontsize = 7,linewidth=0.75)
# x,y coordinate - lon, lat
xx, yy = np.meshgrid(lon,lat[0:lat_y+1])
XX, YY = m(xx, yy)
# define color range for the contourf
color = np.linspace(-0.30,0.30,13)
# !!!!!take care about the coordinate of contourf(Longitude, Latitude, data(Lat,Lon))
cs = m.contourf(XX,YY,np.ma.masked_where(mask_ci,r_value),color,cmap='coolwarm') # ci_white
# add color bar
cbar = m.colorbar(cs,location="bottom",size='4%',pad="8%",format='%.2f')
cbar.ax.tick_params(labelsize=8)
cbar.set_label('Correlation Coefficient',fontsize = 8)
# locate the indices of p_value matrix where p<0.05 (99.5% confident)
p_value[mask_ci==1] = 1.0
i, j = np.where(p_value<=0.05)
# get the coordinate on the map (lon,lat) and plot scatter dots
m.scatter(XX[i,j],YY[i,j],2.2,marker='.',color='g',alpha=0.6, edgecolor='none') # alpha bleding factor with map
plt.title('Regression of Sea Ice Concentration Anomaly on OMET Anomaly across 60 N',fontsize = 9, y=1.05)
plt.show()
fig14.savefig(output_path + os.sep + 'regression' + os.sep + "Regression_OMET_Ice_ERAI_white_correlation_coef.jpeg",dpi=500)

# plot regression coefficient
fig15 = plt.figure()
# setup north polar stereographic basemap
m = Basemap(projection='npstere',boundinglat=60,round=True,lon_0=0,resolution='l')
# draw coastlines
m.drawcoastlines(linewidth=0.25)
# draw parallels and meridians
m.drawparallels(np.arange(60,81,10),fontsize = 7,linewidth=0.75)
m.drawmeridians(np.arange(0,360,30),labels=[1,1,1,1],fontsize = 7,linewidth=0.75)
# x,y coordinate - lon, lat
xx, yy = np.meshgrid(lon,lat[0:lat_y+1])
XX, YY = m(xx, yy)
# define color range for the contourf
color = np.linspace(-0.75,0.75,31)
# !!!!!take care about the coordinate of contourf(Longitude, Latitude, data(Lat,Lon))
cs = m.contourf(XX,YY,slope,color,cmap='coolwarm')
# add color bar
cbar = m.colorbar(cs,location="bottom",size='4%',pad="8%",format='%.2f',ticks=[-0.65,-0.3,0,0.3,0.65])
cbar.ax.tick_params(labelsize=8)
#cbar.set_ticks(np.arange(0,6))
cbar_labels = ['-65%','-30%','0%','30%','65%']
cbar.ax.set_xticklabels(cbar_labels)
cbar.set_label('Regression Coefficient Percentage/PW',fontsize = 8)
p_value[mask_ci==1] = 1.0
i, j = np.where(p_value<=0.05)
# get the coordinate on the map (lon,lat) and plot scatter dots
m.scatter(XX[i,j],YY[i,j],2.2,marker='.',color='g',alpha=0.6, edgecolor='none') # alpha bleding factor with map
plt.title('Regression of Sea Ice Concentration Anomaly on OMET Anomaly across 60 N',fontsize = 9, y=1.05)
plt.show()
fig15.savefig(output_path + os.sep + 'regression' + os.sep + "Regression_OMET_Ice_ERAI_white_regression_coef.jpeg",dpi=500)

print ("--- %s minutes ---" % ((tttt.time() - start_time)/60))