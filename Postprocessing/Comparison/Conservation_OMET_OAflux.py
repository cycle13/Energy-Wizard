#!/usr/bin/env python
"""
Copyright Netherlands eScience Center
Function        : Conservation of Oceanic Meridional Energy Transport
Author          : Yang Liu
Date            : 2018.02.26
Last Update     : 2018.03.02
Description     : The code aims to inspect the conservation of the oceanic meridional
                  energy transport calculated from different oceanic reanalysis datasets.
                  This includes ORAS4 from ECMWF, GLORYS2V3 from Mercator Ocean, and SODA3
                  from University of Maryland & TAMU. For the surface flux, we take an
                  independent dataset OAflux from WHOI. This dataset contains time series
                  of ocean latent and sensible heat flux, which could be used to calculate
                  the net heat flux at the surface of the ocean with a combination of the
                  surface radiation product from ISCCP.

                  In this case, we will focus on the conservation of energy from 50N to 70N
                  in the Atlantic. The conservation of energy is acquired through:
                  **** Meridional Heat Transport + Ocean Surface Net Heat Flux = d(OHC)/dt ****
Return Value    : NetCFD4 data file
Dependencies    : os, time, numpy, netCDF4, sys, matplotlib
variables       : Meridional Energy Transport               E         [Tera-Watt]
                  Meridional Overturning Circulation        Psi       [Sv]
                  Ocean Surface Net Heat Flux               Qnet      [W/m2]

Caveat!!        : Dimension of OMET from each Reanalysis product
                  SODA 3 (MOM5 Grid)
                  Time: 1980 - 2015
                  Direction of Axis: from south to north, west to east
                  Model Level: MOM5 Arakawa-B grid
                  Dimension:
                  Latitude      1070
                  Longitude     1440
                  Depth         50

                  ORAS4 (ORCA1 Grid)
                  Time: 1979 - 2014
                  Direction of Axis: from south to north, west to east
                  Model Level: ORCA Arakawa-C grid
                  Dimension:
                  Latitude      362
                  Longitude     292
                  Depth         42

                  GLORYS2V3 (ORCA025 Grid)
                  Time: 1993 - 2014
                  Direction of Axis: from south to north, west to east
                  Model Level: ORCA Arakawa-C grid
                  Dimension:
                  Latitude      1021
                  Longitude     1440
                  Depth         75

                  OAflux (Geographic Grid)
                  Time: 1983.07 - 2009.12
                  Direction of Axis: from south to north, west to east
                  Latitude      180
                  Longitude     360

                  OAflux has a filled value of 3.2766E+04. We have to refill it with 0.

"""

import numpy as np
import seaborn as sns
import time as tttt
from netCDF4 import Dataset,num2date
import os
import platform
import sys
import numpy as np
import logging
import matplotlib
# generate images without having a window appear
#matplotlib.use('Agg')
import matplotlib.pyplot as plt

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
datapath_ORAS4_OMET= '/home/yang/workbench/Core_Database_AMET_OMET_reanalysis/ORAS4/postprocessing'
datapath_GLORYS2V3_OMET = '/home/yang/workbench/Core_Database_AMET_OMET_reanalysis/GLORYS2V3/postprocessing'
# OHC
datapath_ORAS4_OHC= '/home/yang/workbench/Core_Database_AMET_OMET_reanalysis/ORAS4/statistics'
datapath_GLORYS2V3_OHC = '/home/yang/workbench/Core_Database_AMET_OMET_reanalysis/GLORYS2V3/statistics'
# land sea mask
datapath_ORAS4_mask = '/home/yang/workbench/Core_Database_AMET_OMET_reanalysis/ORAS4'
datapath_GLORYS2V3_mask = '/home/yang/workbench/Core_Database_AMET_OMET_reanalysis/GLORYS2V3'
#datapath_SODA3_mask = '/home/yang/workbench/Core_Database_AMET_OMET_reanalysis/SODA3'
# ocean surface net heat flux
datapath_OAflux = '/home/yang/workbench/Core_Database_AMET_OMET_reanalysis/OAflux/postprocessing'
# specify output path for figures
output_path = '/home/yang/NLeSC/Computation_Modeling/BlueAction/OMET/Conservation'
# the threshold (index of latitude) of the OMET (globally)
# 50N
lat_GLORYS2V3_50 = 726
lat_ORAS4_50 = 218
lat_OAflux_50 = 140
# 60N
lat_GLORYS2V3_60 = 788
lat_ORAS4_60 = 233
lat_OAflux_60 = 150
# 70N
lat_GLORYS2V3_70 = 857
lat_ORAS4_70 = 250
lat_OAflux_70 = 160
####################################################################################
print '*******************************************************************'
print '*********************** extract variables *************************'
print '*******************************************************************'
# # ORCA1_z42 grid infor (Madec and Imbard 1996)
# ji_1 = 362
# jj_1 = 292
# level_1 = 42
#
# # ORCA025_z75 grid infor (Madec and Imbard 1996)
# ji_025 = 1440
# jj_025 = 1021
# level_025 = 75
#
# # MOM5_z50 grid info
# ji_5 = 1440
# jj_5 = 1070
# level_5 = 50
#
# # OAflux grid info
# ji_oa = 180
# jj_oa = 360

####################################################################################
####################                 OAflux (WHOI)               ###################
####################          time: 1983 July - 2009 Dec         ###################
#######     qnet: monthly mean net surface heat flux, positive downward     ########
####################                  unit: W/m2                 ###################
####################           spatial: lat 180 lon 360          ###################
####################################################################################
# get the key for the datasets
# OMET
dataset_GLORYS2V3_OMET = Dataset(datapath_GLORYS2V3_OMET + os.sep + 'GLORYS2V3_model_monthly_orca025_E_zonal_int.nc')
dataset_ORAS4_OMET = Dataset(datapath_ORAS4_OMET + os.sep + 'oras4_model_monthly_orca1_E_zonal_int.nc')
#dataset_SODA3_OMET = Dataset()
# OHC
dataset_GLORYS2V3_OHC = Dataset(datapath_GLORYS2V3_OHC + os.sep + 'GLORYS2V3_model_monthly_orca025_OHC_point.nc')
dataset_ORAS4_OHC = Dataset(datapath_ORAS4_OHC + os.sep + 'oras4_model_monthly_orca1_OHC_point.nc')
#dataset_SODA3_OHC = Dataset()
# global land sea mask
dataset_GLORYS2V3_mask_globe = Dataset(datapath_GLORYS2V3_mask + os.sep + 'G2V3_mesh_mask_myocean.nc')
dataset_ORAS4_mask_globe = Dataset(datapath_ORAS4_mask + os.sep + 'mesh_mask.nc')
#dataset_SODA3_mask = Dataset(datapath_SODA3_mask + os.sep + 'topog.nc')
# individual sea/ocean mask
dataset_GLORYS2V3_mask_ocean = Dataset(datapath_GLORYS2V3_mask + os.sep + 'new_maskglo.nc')
dataset_ORAS4_mask_ocean = Dataset(datapath_ORAS4_mask + os.sep + 'basinmask_050308_UKMO.nc')
# OAflux
dataset_OAflux = Dataset(datapath_OAflux + os.sep + 'OAflux_qnet_point.nc')

# extract variables
# OMET (peta watt)
OMET_ORAS4 = dataset_ORAS4_OMET.variables['E'][21:,:,:]/1000 # start from 1979
OMET_GLORYS2V3 = dataset_GLORYS2V3_OMET.variables['E'][:]/1000 # start from 1993
# OHC (peta joule)
OHC_point_ORAS4 = dataset_ORAS4_OHC.variables['OHC_glo_vert'][21:,:,:,:]/1000
OHC_ORAS4 = np.sum(OHC_point_ORAS4,3)
OHC_point_GLORYS2V3 = dataset_GLORYS2V3_OHC.variables['OHC_glo_vert'][:]/1000
OHC_GLORYS2V3 = np.sum(OHC_point_GLORYS2V3,3)
# Net Heat Flux (peta watt)
NHF_point_OAflux = dataset_OAflux.variables['qnet'][:]/1000
NHF_OAflux = np.sum(NHF_point_OAflux,3)
# year
year_ORAS4 = dataset_ORAS4_OMET.variables['year'][21:]         # from 1979 to 2014
year_GLORYS2V3 = dataset_GLORYS2V3_OMET.variables['year'][:]   # from 1993 to 2014
#year_SODA3
year_OAflux = dataset_OAflux.variables['year'][:]  # from 1983 to 2009
# nominal latitude
latitude_nom_ORAS4 = dataset_ORAS4_mask_globe.variables['gphiv'][0,:,96]
latitude_nom_GLORYS2V3 = dataset_GLORYS2V3_mask_globe.variables['gphiv'][0,:,1060]
#latitude_nom_SODA3 = dataset_SODA3_OMET.variables['y_T'][:]
# latitude
#latitude_ORAS4 = dataset_ORAS4_mask_globe.variables['nav_lat'][:]
#latitude_GLORYS2V3 = dataset_GLORYS2V3_mask_globe.variables['nav_lat'][:]
latitude_OAflux = dataset_OAflux.variables['latitude'][:]
# longitude
# tmask
vmask_ORAS4 = dataset_ORAS4_mask_globe.variables['vmask'][0,0,:,:]
vmask_GLORYS2V3 = dataset_GLORYS2V3_mask_globe.variables['vmask'][0,0,:,:]
#tmask_SODA3 = mesh_mask_SODA3.variables['wet'][:]
# sea/ocean mask
# Atlantic
tmaskatl_ORAS4 = dataset_ORAS4_mask_ocean.variables['tmaskatl'][:]
tmaskatl_GLORYS2V3 = dataset_GLORYS2V3_mask_ocean.variables['tmaskatl'][:,1:-1] # attention that the size is different!
print '*******************************************************************'
print '*************************** time series ***************************'
print '*******************************************************************'

# OMET
OMET_series_ORAS4 = OMET_ORAS4.reshape(len(year_ORAS4)*12,len(latitude_nom_ORAS4))
OMET_series_GLORYS2V3 = OMET_GLORYS2V3.reshape(len(year_GLORYS2V3)*12,len(latitude_nom_GLORYS2V3))
#OHC
OHC_series_ORAS4 = OHC_ORAS4.reshape(len(year_ORAS4)*12,len(latitude_nom_ORAS4))
OHC_series_GLORYS2V3 = OHC_GLORYS2V3.reshape(len(year_GLORYS2V3)*12,len(latitude_nom_GLORYS2V3))
# Net Heat Flux (peta watt)
# take care that the first 6 months have no values
NHF_series_OAflux = NHF_OAflux.reshape(len(year_OAflux)*12,len(latitude_OAflux))

# calculate the time derivative of Ocean Heat Content
# now the OHC/dt time series start from Feb of the starting year!!!
OHC_series_dt_ORAS4 = (OHC_series_ORAS4[1:,:] - OHC_series_ORAS4[:-1,:]) / (30*86400)
OHC_series_dt_GLORYS2V3 = (OHC_series_GLORYS2V3[1:,:] - OHC_series_GLORYS2V3[:-1,:]) / (30*86400)

print '*******************************************************************'
print '************************* regional result *************************'
print '*******************************************************************'
# from 50N to 70N
# OMET (energy flow in to the water parcel is positive)
OMET_series_ORAS4_regional = OMET_series_ORAS4[:,lat_ORAS4_50] - OMET_series_ORAS4[:,lat_ORAS4_70]
OMET_series_GLORYS2V3_regional = OMET_series_GLORYS2V3[:,lat_GLORYS2V3_50] - OMET_series_GLORYS2V3[:,lat_GLORYS2V3_70]
# OHC
OHC_series_ORAS4_regional = np.sum(OHC_series_dt_ORAS4[:,lat_ORAS4_50:lat_ORAS4_70],1)
OHC_series_GLORYS2V3_regional = np.sum(OHC_series_dt_GLORYS2V3[:,lat_GLORYS2V3_50:lat_GLORYS2V3_70],1)
#NHF
NHF_series_OAflux_regional = np.sum(NHF_series_OAflux[:,lat_OAflux_50:lat_OAflux_70],1)

# from 1983 to 2009
##################################################
# ORAS4
# 1979.02 - 2014.12 (431 months)
# index: 53 - 371
# GLORYS2V3
# 1993.01 - 2014.12
# index: 0 - 204
# OAflux
# 1983.07 - 2009.12 (318 months)
# index: 6 - 324

# index and namelist of years for time series
index = np.arange(0,324,1) # Starting from

# time series plot of energy convergence between 50N and 70N
fig1 = plt.figure()
plt.plot(index[6:],NHF_series_OAflux_regional[6:],color='royalblue',label='OAflux')
plt.plot(index[6:],OHC_series_ORAS4_regional[53:371],'c--',label='OHC_ORAS4')
plt.plot(index[121:],OHC_series_GLORYS2V3_regional[0:203],'m--',label='OHC_GLORYS2V3')
plt.plot(index[6:],OMET_series_ORAS4_regional[53:371],'c-',label='OMET_ORAS4')
plt.plot(index[121:],OMET_series_GLORYS2V3_regional[0:203],'m-',label='OMET_GLORYS2V3')
#plt.plot(index[],OMET_series_SODA3_regional[],'y-',label='OMET_SODA3')
plt.title('Heat Convergence between 50N and 70N')
plt.legend()
fig1.set_size_inches(12, 5)
plt.xlabel("Time")
plt.xticks(np.linspace(0, 324, 27), year_OAflux)
plt.xticks(rotation=60)
plt.ylabel("Energy Transport (PW)")
plt.show()
fig1.savefig(output_path + os.sep + 'Convergence_50N_70N_time_series_component.jpg', dpi = 500)

# time series plot of energy convergence residuals between 50N and 70N
# residual = d(OHC) / dt -NHF - OMET
fig2 = plt.figure()
plt.plot(index[6:],OHC_series_ORAS4_regional[53:371] - NHF_series_OAflux_regional[6:] - OMET_series_ORAS4_regional[53:371],'c--',label='ORAS4')
plt.plot(index[121:],OHC_series_GLORYS2V3_regional[0:203] - NHF_series_OAflux_regional[121:] - OMET_series_GLORYS2V3_regional[0:203],'m--',label='GLORYS2V3')
#plt.plot(index[],OMET_series_SODA3_regional[],'y-',label='OMET_SODA3')
plt.title('Heat Convergence Residual between 50N and 70N')
plt.legend()
fig2.set_size_inches(12, 5)
plt.xlabel("Time")
plt.xticks(np.linspace(0, 324, 27), year_OAflux)
plt.xticks(rotation=60)
plt.ylabel("Energy Transport (PW)")
plt.show()
fig2.savefig(output_path + os.sep + 'Convergence_50N_70N_time_series_residual.jpg', dpi = 500)

print ("--- %s minutes ---" % ((tttt.time() - start_time)/60))
