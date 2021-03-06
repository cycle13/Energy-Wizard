#!/usr/bin/env python
"""
Copyright Netherlands eScience Center

Function        : Regression of climatological variable on OMET (SODA3) with whitening
Author          : Yang Liu
Date            : 2017.11.10
Last Update     : 2018.05.23
Description     : The code aims to explore the association between climatological
                  variables with oceanic meridional energy transport (OMET).
                  The statistical method employed here is linear regression. A
                  number of fields (SST, SLP, Sea ice, geopotential, etc.),
                  corresponding to the pre-existing natural modes of variability,
                  will be projected on meridional energy transport. This will enhance
                  our understanding of climate change. Notice that the time series
                  of input data will be whitened (the seasonal cycles are removed).
                  The fields come from ERA-Interim surface level data, from 1980-2014.

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
datapath_OMET = '/home/yang/workbench/Core_Database_AMET_OMET_reanalysis/SODA3/postprocessing'
# target climatological variables
datapath_y = "/home/yang/workbench/Core_Database_AMET_OMET_reanalysis/ERAI/regression"
# specify output path for figures
output_path = '/home/yang/NLeSC/Computation_Modeling/BlueAction/OMET/SODA3'
# the threshold ( index of latitude) of the OMET
# There is a cut to JRA, too
# index of latitude for insteret
# 20N
lat_SODA3_20 = 569
# after a cut to 20-90 N
lat_SODA3_20_cut = 0

# 30N
lat_SODA3_30 = 613
# after a cut to 20-90 N
lat_SODA3_30_cut = 44

# 40N
lat_SODA3_40 = 662
# after a cut to 20-90 N
lat_SODA3_40_cut = 93

# 50N
lat_SODA3_50 = 719
# after a cut to 20-90 N
lat_SODA3_50_cut = 150

# 60N
lat_SODA3_60 = 789
# after a cut to 20-90 N
lat_SODA3_60_cut = 220

# 70N
lat_SODA3_70 = 880
# after a cut to 20-90 N
lat_SODA3_70_cut = 311

# 80N
lat_SODA3_80 = 974
# after a cut to 20-90 N
lat_SODA3_80_cut = 405

# make a dictionary for instereted sections (for process automation)
lat_interest = {}
lat_interest_list = [20,30,40,50,60,70,80]
# after cut
lat_interest['SODA3'] = [lat_SODA3_20_cut,lat_SODA3_30_cut,lat_SODA3_40_cut,lat_SODA3_50_cut,lat_SODA3_60_cut,lat_SODA3_70_cut,lat_SODA3_80_cut]
# the range ( index of latitude) of the projection field
lat_y = 94 # 60 N - 90 N
####################################################################################
print '*******************************************************************'
print '*********************** extract variables *************************'
print '*******************************************************************'
# # MOM5_z50 grid info
# ji_5 = 1440
# jj_5 = 1070
# level_5 = 50
# zonal integral
dataset_OMET = Dataset(datapath_OMET + os.sep + 'OMET_SODA3_model_5daily_1980_2015_E_zonal_int.nc')
dataset_y = Dataset(datapath_y + os.sep + 'surface_ERAI_monthly_regress_1979_2016.nc')
for k in dataset_OMET.variables:
    print dataset_OMET.variables['%s' % (k)]

for l in dataset_y.variables:
    print dataset_y.variables['%s' % (l)]

# extract Oceanic meridional energy transport
# dimension (year,month,latitude)
OMET = dataset_OMET.variables['E'][:,:,569:]/1000 # from Tera Watt to Peta Watt # start from 1980
lat_OMET = dataset_OMET.variables['latitude_aux'][569:]
year = dataset_OMET.variables['year'][:]
# extract variables from 20N to 90 N
# sea level pressure
SLP = dataset_y.variables['msl'][12:444,0:lat_y+1,:] # from 1980 - 2015
# sea surface temperature
SST = dataset_y.variables['sst'][12:444,0:lat_y+1,:]
mask_SST = np.ma.getmaskarray(SST[0,:,:])
# sea ice cover
ci = dataset_y.variables['ci'][12:444,0:lat_y+1,:]
mask_ci = np.ma.getmaskarray(ci[0,:,:])
# longitude
lon = dataset_y.variables['longitude'][:]
# latitude
lat = dataset_y.variables['latitude'][0:lat_y+1]
# time (number of months)
time = dataset_y.variables['time'][12:444]

print 'The type of SLP is', type(SLP)
print 'The type of SST is', type(SST)
print 'The type of ci is', type(ci)

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
    SLP_seasonal_mean[i,:,:] = np.mean(SLP[i::12,:,:],axis=0)
    # remove seasonal mean
    SLP_white[i::12,:,:] = SLP[i::12,:,:] - SLP_seasonal_mean[i,:,:]

# remove climatology for Sea Surface Temperature
SST_seasonal_mean = np.zeros((12,lat_y+1,len(lon))) # from 20N - 90N
SST_white = np.zeros(SST.shape,dtype=float)
for i in month_ind:
    # calculate the monthly mean (seasonal cycling)
    SST_seasonal_mean[i,:,:] = np.mean(SST[i::12,:,:],axis=0)
    # remove seasonal mean
    SST_white[i::12,:,:] = SST[i::12,:,:] - SST_seasonal_mean[i,:,:]

# remove climatology for Sea Ice Concentration
ci_seasonal_mean = np.zeros((12,lat_y+1,len(lon))) # from 20N - 90N
ci_white = np.zeros(ci.shape)
for i in month_ind:
    # calculate the monthly mean (seasonal cycling)
    ci_seasonal_mean[i,:,:] = np.mean(ci[i::12,:,:],axis=0)
    # remove seasonal mean
    ci_white[i::12,:,:] = ci[i::12,:,:] - ci_seasonal_mean[i,:,:]

# remove the seasonal cycling of OMET at 60N
# dimension of OMET[year,month]
OMET_seansonal_cycle = np.mean(OMET,axis=0)
OMET_white = np.zeros(OMET.shape,dtype=float)
for i in month_ind:
    OMET_white[:,i,:] = OMET[:,i,:] - OMET_seansonal_cycle[i,:]

print '*******************************************************************'
print '*********************** prepare variables *************************'
print '*******************************************************************'
# take the time series of E
OMET_series = OMET.reshape(len(year)*len(month_ind),len(lat_OMET))
# take the time series of whitened OMET
OMET_white_series = OMET_white.reshape(len(year)*len(month_ind),len(lat_OMET))
print '*******************************************************************'
print '***************************  Detrend  *****************************'
print '*******************************************************************'
####################################################
######      detrend - polynomial fitting      ######
####################################################
poly_fit = np.zeros(ci_white.shape,dtype=float)
for i in np.arange(len(lat)):
    for j in np.arange(len(lon)):
        polynomial = np.polyfit(np.arange(len(time)), ci_white[:,i,j], 5)
        poly = np.poly1d(polynomial)
        poly_fit[:,i,j] = poly(np.arange(len(time)))

ci_white_detrend = np.zeros(ci_white.shape,dtype=float)
ci_white_detrend = ci_white - poly_fit

# detrend OMET
poly_fit_OMET = np.zeros(OMET_white_series.shape,dtype=float)
for i in np.arange(len(lat_OMET)):
        polynomial_OMET = np.polyfit(np.arange(len(year)*len(month_ind)), OMET_white_series[:,i], 5)
        poly_OMET = np.poly1d(polynomial_OMET)
        poly_fit_OMET[:,i] = poly_OMET(np.arange(len(year)*len(month_ind)))

OMET_white_detrend_series = np.zeros(ci_white.shape,dtype=float)
OMET_white_detrend_series = OMET_white_series - poly_fit_OMET
print '*******************************************************************'
print '********************** Running mean/sum ***************************'
print '*******************************************************************'
# running mean is calculated on time series
# define the running window for the running mean
#window = 12 # in month
window = 60 # in month
# calculate the running mean and sum of OMET
OMET_running_mean = np.zeros((len(year)*len(month_ind)-window+1,len(lat_OMET)),dtype=float)
#OMET_running_sum = np.zeros(len(OMET_series)-window+1)
for i in np.arange((len(year)*len(month_ind)-window+1)):
    OMET_running_mean[i,:] = np.mean(OMET_series[i:i+window,:],0)

# calculate the running mean and sum of OMET after removing the seasonal cycling
OMET_white_running_mean = np.zeros((len(year)*len(month_ind)-window+1,len(lat_OMET)),dtype=float)
#OMET_running_sum = np.zeros(len(OMET_series)-window+1)
for i in np.arange((len(year)*len(month_ind)-window+1)):
    OMET_white_running_mean[i] = np.mean(OMET_white_series[i:i+window,:],0)

OMET_white_detrend_running_mean = np.zeros((len(year)*len(month_ind)-window+1,len(lat_OMET)),dtype=float)
#OMET_running_sum = np.zeros(len(OMET_series)-window+1)
for i in np.arange((len(year)*len(month_ind)-window+1)):
    OMET_white_detrend_running_mean[i] = np.mean(OMET_white_detrend_series[i:i+window,:],0)

SLP_white_running_mean = np.zeros((len(year)*len(month_ind)-window+1,len(lat),len(lon)),dtype=float)
for i in np.arange(len(year)*len(month_ind)-window+1):
    SLP_white_running_mean[i,:,:] = np.mean(SLP_white[i:i+window,:,:],0)

SST_white_running_mean = np.zeros((len(year)*len(month_ind)-window+1,len(lat),len(lon)),dtype=float)
for i in np.arange(len(year)*len(month_ind)-window+1):
    SST_white_running_mean[i,:,:] = np.mean(SST_white[i:i+window,:,:],0)

ci_white_running_mean = np.zeros((len(year)*len(month_ind)-window+1,len(lat),len(lon)),dtype=float)
for i in np.arange(len(year)*len(month_ind)-window+1):
    ci_white_running_mean[i,:,:] = np.mean(ci_white[i:i+window,:,:],0)

ci_white_detrend_running_mean = np.zeros((len(year)*len(month_ind)-window+1,len(lat),len(lon)),dtype=float)
for i in np.arange(len(year)*len(month_ind)-window+1):
    ci_white_detrend_running_mean[i,:,:] = np.mean(ci_white_detrend[i:i+window,:,:],0)

print '*******************************************************************'
print '*************************** time series ***************************'
print '*******************************************************************'
# index and namelist of years for time series and running mean time series
index = np.arange(1,433,1)
index_year = np.arange(1980,2016,1)
#
# index_running_mean = np.arange(1,265-window+1,1)
# index_year_running_mean = np.arange(1980+window/12,2015,1)
#
# # plot the OMET after removing seasonal cycle
# fig1 = plt.figure()
# plt.plot(index,OMET_white_series,'b-',label='SODA3')
# plt.title('Oceanic Meridional Energy Transport Anomaly at 60N (1980-2014)')
# #plt.legend()
# fig1.set_size_inches(12, 5)
# plt.xlabel("Time")
# plt.xticks(np.linspace(0, 264, 23), index_year)
# plt.xticks(rotation=60)
# plt.ylabel("Meridional Energy Transport (PW)")
# plt.show()
# fig1.savefig(output_path + os.sep + 'regression' + os.sep + 'OMET_anomaly_60N_time_series_1980_2014.jpg', dpi = 500)
#
# # plot the running mean of OMET after removing seasonal cycle
# fig0 = plt.figure()
# plt.plot(index_running_mean,OMET_white_running_mean,'b-',label='SODA3')
# plt.title('Running Mean of OMET Anomalies at 60N with a window of %d months (1980-2014)' % (window))
# #plt.legend()
# fig0.set_size_inches(12, 5)
# plt.xlabel("Time")
# plt.xticks(np.linspace(0, 265-window, 23-window/12), index_year_running_mean)
# plt.xticks(rotation=60)
# plt.ylabel("Meridional Energy Transport (PW)")
# plt.show()
# fig0.savefig(output_path + os.sep + 'regression' + os.sep +'OMET_anomaly_60N_running_mean_window_%d_only.jpg' % (window), dpi = 500)
#
# # plot the OMET with running mean
# fig2 = plt.figure()
# plt.plot(index,OMET_series,'b--',label='time series')
# plt.plot(index[window-1:],OMET_running_mean,'r-',linewidth=2.0,label='running mean')
# plt.title('Running Mean of OMET at 60N with a window of %d months (1980-2014)' % (window))
# #plt.legend()
# fig2.set_size_inches(12, 5)
# plt.xlabel("Time")
# plt.xticks(np.linspace(0, 264, 23), index_year)
# plt.xticks(rotation=60)
# plt.ylabel("Meridional Energy Transport (PW)")
# plt.show()
# fig2.savefig(output_path + os.sep + 'regression' + os.sep +'OMET_60N_running_mean_window_%d_comp.jpg' % (window), dpi = 500)
#
# # plot the OMET after removing the seasonal cycling with running mean
# fig3 = plt.figure()
# plt.plot(index,OMET_white_series,'b--',label='time series')
# plt.plot(index[window-1:],OMET_white_running_mean,'r-',linewidth=2.0,label='running mean')
# plt.title('Running Mean of OMET Anomalies at 60N with a window of %d months (1980-2014)' % (window))
# #plt.legend()
# fig3.set_size_inches(12, 5)
# plt.xlabel("Time")
# plt.xticks(np.linspace(0, 264, 23), index_year)
# plt.xticks(rotation=60)
# plt.ylabel("Meridional Energy Transport (PW)")
# plt.show()
# fig3.savefig(output_path + os.sep + 'regression' + os.sep + 'OMET_anomaly_60N_running_mean_window_%d_comp.jpg' % (window), dpi = 500)
#
# print '*******************************************************************'
# print '********************* Fourier transform ***************************'
# print '*******************************************************************'
# # Fast Fourier Transform of OMET
# FFT_OMET = np.fft.fft(OMET_series)
# freq_FFT_OMET = np.fft.fftfreq(len(FFT_OMET),d=1)
# mag_FFT_OMET = abs(FFT_OMET)
# # Plot OMET in Frequency domain
# fig4 = plt.figure()
# plt.plot(freq_FFT_OMET[0:200],mag_FFT_OMET[0:200],'b-',label='SODA3')
# plt.title('Fourier Transform of OMET at 60N (1980-2014)')
# #plt.legend()
# fig4.set_size_inches(12, 5)
# plt.xlabel("Times per month")
# #plt.xticks(np.linspace(0, 456, 39), index_year)
# #plt.xticks(rotation=60)
# plt.ylabel("Power spectrum density (PW^2/month)")
# plt.show()
# fig4.savefig(output_path + os.sep + 'regression' + os.sep + 'OMET_60N_FFT_1980_2014.jpg', dpi = 500)
#
# # Fast Fourier Transform of OMET anomalies
# FFT_OMET_white = np.fft.fft(OMET_white_series)
# freq_FFT_OMET_white = np.fft.fftfreq(len(FFT_OMET_white),d=1)
# mag_FFT_OMET_white = abs(FFT_OMET_white)
# # Plot the anomaly of OMET in Frequency domain
# fig5 = plt.figure()
# plt.plot(freq_FFT_OMET_white[0:200],mag_FFT_OMET_white[0:200],'b-',label='SODA3')
# plt.title('Fourier Transform of OMET Anomaly at 60N (1980-2014)')
# #plt.legend()
# fig5.set_size_inches(12, 5)
# plt.xlabel("Times per month")
# #plt.xticks(np.linspace(0, 456, 39), index_year)
# #plt.xticks(rotation=60)
# plt.ylabel("Power spectrum density (PW^2/month)")
# plt.show()
# fig5.savefig(output_path + os.sep + 'regression' + os.sep + 'OMET_anomaly_60N_FFT_1980_2014.jpg', dpi = 500)
#
# # Plot the running mean of OMET anomaly in Frequency domain
# FFT_OMET_white_running_mean = np.fft.fft(OMET_white_running_mean)
# freq_FFT_OMET_white_running_mean = np.fft.fftfreq(len(FFT_OMET_white_running_mean),d=1)
# mag_FFT_OMET_white_running_mean = abs(FFT_OMET_white_running_mean)
# # Plot the running mean of OMET in Frequency domain
# fig6 = plt.figure()
# plt.plot(freq_FFT_OMET_white_running_mean[0:60],mag_FFT_OMET_white_running_mean[0:60],'b-',label='SODA3')
# plt.title('Fourier Transform of Running Mean (%d) of OMET Anomalies at 60N (1980-2014)' % (window))
# #plt.legend()
# fig6.set_size_inches(12, 5)
# plt.xlabel("Times per month")
# #plt.xticks(np.linspace(0, 456, 39), index_year)
# #plt.xticks(rotation=60)
# plt.ylabel("Power spectrum density (PW^2/month)")
# plt.show()
# fig6.savefig(output_path + os.sep + 'regression' + os.sep + 'OMET_anomaly_60N_FFT_running_mean_%d_1980_2014.jpg' % (window), dpi = 500)

# testing figure for detrending OMET with time series excluding seasonal cycling
# detrend - polynomial fitting
fig00 = plt.figure()
plt.axhline(y=0, color='k',ls='-')
plt.plot(index,OMET_white_series[:,lat_interest['SODA3'][4]],'b--',linewidth = 0.5,label='Anomalies')
plt.plot(index,poly_fit_OMET[:,lat_interest['SODA3'][4]],'r-',linewidth = 2,label='Polynomial')
plt.plot(index,OMET_white_detrend_series[:,lat_interest['SODA3'][4]],'g-',linewidth = 1,label='Detrend')
plt.title('OMET Anomalies at 60N and the detrend OMET anomalies (1979-2016)')
plt.legend()
fig00.set_size_inches(12, 5)
plt.xlabel("Time")
plt.xticks(np.linspace(0, 432, 37), index_year)
plt.xticks(rotation=60)
plt.ylabel("OMET PW")
plt.show()
fig00.savefig(output_path + os.sep + 'regression' + os.sep + 'Detrend_poly_OMET_white.jpg', dpi = 300)

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
plt.title('Trend of Sea Level Pressure Anomalies (1980-2014)',fontsize = 9, y=1.05)
plt.show()
fig7.savefig(output_path + os.sep + 'regression' + os.sep + "Trend_ERAI_SLP.jpeg",dpi=400)

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
plt.title('Trend of Sea Surface Temperature Anomalies (1980-2014)',fontsize = 9, y=1.05)
plt.show()
fig8.savefig(output_path + os.sep + 'regression' + os.sep + "Trend_ERAI_SST.jpeg",dpi=400)

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
plt.title('Trend of the Sea Ice Concentration Anomalies (1980-2014)',fontsize = 9, y=1.05)
plt.show()
fig9.savefig(output_path + os.sep + 'regression' + os.sep + "Trend_ERAI_Ice.jpeg",dpi=400)

print '*******************************************************************'
print '************************** regression *****************************'
print '*******************************************************************'
# calculate the standard deviation of OMET anomaly
OMET_white_std = np.std(OMET_white_series)
print 'The standard deviation of OMET anomaly is (in peta Watt):'
print OMET_white_std
# all the regression are taken on anomalies of variables
# this is because the seasonal cycles are always too strong

# create an array to store the correlation coefficient
slope = np.zeros((lat_y+1,len(lon)),dtype = float)
r_value = np.zeros((lat_y+1,len(lon)),dtype = float)
p_value = np.zeros((lat_y+1,len(lon)),dtype = float)
#######################################################################################################
# Since running mean will make the points more correlated with each other
# Apparently the T-test based on running mean time series will overestime the level of significance
# However, it is difficult to determine the degress of freedom as the points are actually correlated
# with space and time domain. As a compromise, we use the T-test results from the regression of SIC on
# original time series.
#######################################################################################################
p_value_original = np.zeros((lat_y+1,len(lon)),dtype = float)

for c in np.arange(len(lat_interest_list)):
    # linear regress SLP on OMET (anomalies)
    # plot correlation coefficient
    for i in np.arange(lat_y+1):
        for j in np.arange(len(lon)):
            # return value: slope, intercept, r_value, p_value, stderr
            slope[i,j],_,r_value[i,j],p_value[i,j],_ = stats.linregress(OMET_white_series[:,lat_interest['SODA3'][c]],SLP_white[:,i,j])
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
    cs = m.contourf(XX,YY,r_value,color,cmap='coolwarm',extend='both')
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
    plt.title('Regression of SLP Anomaly on OMET Anomaly across %dN' % (lat_interest_list[c]),fontsize = 9, y=1.05)
    plt.show()
    fig10.savefig(output_path + os.sep + 'regression' + os.sep + 'SLP' + os.sep + "Regression_OMET_SLP_ERAI_white_%dN_correlation_coef.jpeg" % (lat_interest_list[c]),dpi=400)

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
    cs = m.contourf(XX,YY,slope/1000,color,cmap='coolwarm',extend='both') # unit from Pa to kPa
    # add color bar
    cbar = m.colorbar(cs,location="bottom",size='4%',pad="8%",format='%.1f')
    cbar.ax.tick_params(labelsize=8)
    cbar.set_label('Regression Coefficient kPa/PW',fontsize = 8)
    i, j = np.where(p_value<=0.05)
    # get the coordinate on the map (lon,lat) and plot scatter dots
    m.scatter(XX[i,j],YY[i,j],2.2,marker='.',color='g',alpha=0.6, edgecolor='none') # alpha bleding factor with map
    plt.title('Regression of SLP Anomaly on OMET Anomaly across %dN' % (lat_interest_list[c]),fontsize = 9, y=1.05)
    plt.show()
    fig11.savefig(output_path + os.sep + 'regression' + os.sep + 'SLP' + os.sep + "Regression_OMET_SLP_ERAI_white_%dN_regression_coef.jpeg" % (lat_interest_list[c]),dpi=400)

    # linear regress SST on OMET (anomalies)
    # plot correlation coefficient
    for i in np.arange(lat_y+1):
        for j in np.arange(len(lon)):
            # return value: slope, intercept, r_value, p_value, stderr
            slope[i,j],_,r_value[i,j],p_value[i,j],_ = stats.linregress(OMET_white_series[:,lat_interest['SODA3'][c]],SST_white[:,i,j])
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
    cs = m.contourf(XX,YY,np.ma.masked_where(mask_SST,r_value),color,cmap='coolwarm',extend='both') # SST_white
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
    plt.title('Regression of SST Anomaly on OMET Anomaly across %dN' % (lat_interest_list[c]),fontsize = 9, y=1.05)
    plt.show()
    fig12.savefig(output_path + os.sep + 'regression' + os.sep + 'SST' + os.sep + "Regression_OMET_SST_ERAI_white_%dN_correlation_coef.jpeg" % (lat_interest_list[c]),dpi=400)

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
    cs = m.contourf(XX,YY,slope,color,cmap='coolwarm',extend='both')
    # add color bar
    cbar = m.colorbar(cs,location="bottom",size='4%',pad="8%",format='%.1f')
    cbar.ax.tick_params(labelsize=8)
    cbar.set_label('Regression Coefficient Celsius/PW',fontsize = 8)
    p_value[mask_SST==1] = 1.0
    i, j = np.where(p_value<=0.05)
    # get the coordinate on the map (lon,lat) and plot scatter dots
    m.scatter(XX[i,j],YY[i,j],2.2,marker='.',color='g',alpha=0.6, edgecolor='none') # alpha bleding factor with map
    plt.title('Regression of SST Anomaly on OMET Anomaly across %dN' % (lat_interest_list[c]),fontsize = 9, y=1.05)
    plt.show()
    fig13.savefig(output_path + os.sep + 'regression' + os.sep + 'SST' + os.sep + "Regression_OMET_SST_ERAI_white_%dN_regression_coef.jpeg" % (lat_interest_list[c]),dpi=400)

    # linear regress Sea Ice Concentration on OMET (anomalies)
    # plot correlation coefficient
    for i in np.arange(lat_y+1):
        for j in np.arange(len(lon)):
            # return value: slope, intercept, r_value, p_value, stderr
            slope[i,j],_,r_value[i,j],p_value[i,j],_ = stats.linregress(OMET_white_series[:,lat_interest['SODA3'][c]],ci_white[12:,i,j])
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
    color = np.linspace(-0.40,0.40,17)
    # !!!!!take care about the coordinate of contourf(Longitude, Latitude, data(Lat,Lon))
    cs = m.contourf(XX,YY,np.ma.masked_where(mask_ci,r_value),color,cmap='coolwarm') # ci_white
    # add color bar
    cbar = m.colorbar(cs,location="bottom",size='4%',pad="8%",format='%.2f',extend='both')
    cbar.ax.tick_params(labelsize=8)
    cbar.set_label('Correlation Coefficient',fontsize = 8)
    # locate the indices of p_value matrix where p<0.05 (99.5% confident)
    p_value[mask_ci==1] = 1.0
    i, j = np.where(p_value<=0.05)
    # get the coordinate on the map (lon,lat) and plot scatter dots
    m.scatter(XX[i,j],YY[i,j],2.2,marker='.',color='g',alpha=0.6, edgecolor='none') # alpha bleding factor with map
    plt.title('Regression of SIC Anomaly on OMET Anomaly across %dN' % (lat_interest_list[c]),fontsize = 9, y=1.05)
    plt.show()
    fig14.savefig(output_path + os.sep +'regression' + os.sep + 'SIC' + os.sep + 'LongTermTrend' + os.sep + "Regression_OMET_Ice_ERAI_white_%dN_correlation_coef.jpeg" % (lat_interest_list[c]),dpi=400)

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
    color = np.linspace(-1.0,1.0,41)
    # !!!!!take care about the coordinate of contourf(Longitude, Latitude, data(Lat,Lon))
    cs = m.contourf(XX,YY,np.ma.masked_where(mask_ci,slope),color,cmap='coolwarm',extend='both')
    # add color bar
    cbar = m.colorbar(cs,location="bottom",size='4%',pad="8%",format='%.2f',ticks=[-1.0,-0.5,0,0.5,1.0])
    cbar.ax.tick_params(labelsize=8)
    #cbar.set_ticks(np.arange(0,6))
    cbar_labels = ['-100%','-50%','0%','50%','100%']
    cbar.ax.set_xticklabels(cbar_labels)
    cbar.set_label('Regression Coefficient Percentage/PW',fontsize = 8)
    p_value[mask_ci==1] = 1.0
    i, j = np.where(p_value<=0.05)
    # get the coordinate on the map (lon,lat) and plot scatter dots
    m.scatter(XX[i,j],YY[i,j],2.2,marker='.',color='g',alpha=0.6, edgecolor='none') # alpha bleding factor with map
    plt.title('Regression of SIC Anomaly on OMET Anomaly across %dN' % (lat_interest_list[c]),fontsize = 9, y=1.05)
    plt.show()
    fig15.savefig(output_path + os.sep + 'regression' + os.sep + 'SIC' + os.sep + 'LongTermTrend' + os.sep + "Regression_OMET_Ice_ERAI_white_%dN_regression_coef.jpeg" % (lat_interest_list[c]),dpi=400)

    for i in np.arange(lat_y+1):
        for j in np.arange(len(lon)):
            # return value: slope, intercept, r_value, p_value, stderr
            slope[i,j],_,r_value[i,j],p_value_original[i,j],_ = stats.linregress(OMET_white_detrend_series[:,lat_interest['SODA3'][c]],ci_white_detrend[:,i,j])
            #slope[i,j],_,r_value[i,j],p_value_original[i,j],_ = stats.linregress(OMET_white_series[107:,lat_interest['SODA3'][c]],ci_white_detrend[:,i,j])
    p_value_original[mask_ci==True] = 1.0
    # plot regression coefficient
    fig16 = plt.figure()
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
    color = np.linspace(-1.0,1.0,41)
    # !!!!!take care about the coordinate of contourf(Longitude, Latitude, data(Lat,Lon))
    cs = m.contourf(XX,YY,np.ma.masked_where(mask_ci,slope),color,cmap='coolwarm',extend='both')
    # add color bar
    cbar = m.colorbar(cs,location="bottom",size='4%',pad="8%",format='%.2f',ticks=[-1.0,-0.5,0,0.5,1.0])
    cbar.ax.tick_params(labelsize=8)
    #cbar.set_ticks(np.arange(0,6))
    cbar_labels = ['-100%','-50%','0%','50%','100%']
    cbar.ax.set_xticklabels(cbar_labels)
    cbar.set_label('Regression Coefficient Percentage/PW',fontsize = 8)
    p_value[mask_ci==1] = 1.0
    i, j = np.where(p_value_original<=0.05)
    # get the coordinate on the map (lon,lat) and plot scatter dots
    m.scatter(XX[i,j],YY[i,j],2.2,marker='.',color='g',alpha=0.6, edgecolor='none') # alpha bleding factor with map
    plt.title('Regression of Detrend SIC Anomaly on OMET Anomaly across %dN' % (lat_interest_list[c]),fontsize = 9, y=1.05)
    plt.show()
    fig16.savefig(output_path + os.sep + 'regression' + os.sep + 'SIC' + os.sep + 'Detrend' + os.sep + "Regression_OMET_Ice_ERAI_white_%dN_regression_coef.jpeg" % (lat_interest_list[c]),dpi=400)

    for i in np.arange(lat_y+1):
        for j in np.arange(len(lon)):
            # return value: slope, intercept, r_value, p_value, stderr
            slope[i,j],_,r_value[i,j],p_value[i,j],_ = stats.linregress(OMET_white_detrend_running_mean[:,lat_interest['SODA3'][c]],ci_white_detrend_running_mean[:,i,j])
            #slope[i,j],_,r_value[i,j],p_value[i,j],_ = stats.linregress(OMET_white_running_mean[107:,lat_interest['SODA3'][c]],ci_white_detrend_running_mean[:,i,j])
    # plot regression coefficient
    fig17 = plt.figure()
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
    color = np.linspace(-1.0,1.0,41)
    # !!!!!take care about the coordinate of contourf(Longitude, Latitude, data(Lat,Lon))
    cs = m.contourf(XX,YY,np.ma.masked_where(mask_ci,slope),color,cmap='coolwarm',extend='both')
    # add color bar
    cbar = m.colorbar(cs,location="bottom",size='4%',pad="8%",format='%.2f',ticks=[-1.0,-0.5,0,0.5,1.0])
    cbar.ax.tick_params(labelsize=8)
    #cbar.set_ticks(np.arange(0,6))
    cbar_labels = ['-100%','-50%','0%','50%','100%']
    cbar.ax.set_xticklabels(cbar_labels)
    cbar.set_label('Regression Coefficient Percentage/PW',fontsize = 8)
    i, j = np.where(p_value_original<=0.05)
    # get the coordinate on the map (lon,lat) and plot scatter dots
    m.scatter(XX[i,j],YY[i,j],2.2,marker='.',color='g',alpha=0.6, edgecolor='none') # alpha bleding factor with map
    plt.title('Regression of Detrend SIC Anomaly on OMET Anomaly across %dN with a running mean of %d months' % (lat_interest_list[c],window),fontsize = 9, y=1.05)
    plt.show()
    fig17.savefig(output_path + os.sep + 'regression' + os.sep + 'SIC' + os.sep + 'Interannual' + os.sep + "Regression_OMET_Ice_ERAI_white_%dN_running_mean_%dm_regression_coef.jpeg" % (lat_interest_list[c],window),dpi=400)
    #fig17.savefig(output_path + os.sep + 'regression' + os.sep + 'SIC' + os.sep + 'Annual' + os.sep + "Regression_OMET_Ice_ERAI_white_%dN_running_mean_%dm_regression_coef.jpeg" % (lat_interest_list[c],window),dpi=400)
print ("--- %s minutes ---" % ((tttt.time() - start_time)/60))
