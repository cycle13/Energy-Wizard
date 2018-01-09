#!/usr/bin/env python
"""
Copyright Netherlands eScience Center

Function        : A statistical look into the temporal and spatial distribution of fields (ORAS4)
Author          : Yang Liu
Date            : 2018.1.4
Last Update     : 2018.1.9
Description     : The code aims to statistically take a close look into each fields.
                  This could help understand the difference between each datasets, which
                  will explain the deviation in meridional energy transport. Specifically,
                  the script deals with oceanic reanalysis dataset ORAS4 from ECMWF.
                  The complete computaiton is accomplished on model level (original ORCA1_z42 grid).
                  All the interpolations are made on the V grid, including scalars.
                  For the sake of accuracy, the zonal integrations are taken on
                  i-j coordinate, which follows i-coord.
                  The script also calculates the ocean heat content for certain layers.

Return Value    : NetCFD4 data file
Dependencies    : os, time, numpy, netCDF4, sys, matplotlib, logging
variables       : Potential Temperature                     Theta
                  Zonal Current Velocity                    u
                  Meridional Current Velocity               v
                  Zonal Grid Spacing Scale Factors          e1
                  Meridional Grid Spacing Scale Factors     e2
                  Land-Sea Mask                             mask

Caveat!!        : The full dataset is from 1958. However, a quality report from
                  Magdalena from ECMWF indicates the quality of data for the first
                  two decades are very poor. Hence we use the data from 1979. which
                  is the start of satellite era.
"""
import numpy as np
#import seaborn as sns
#import scipy as sp
import time as tttt
from netCDF4 import Dataset,num2date
import os
import platform
import sys
import logging
import matplotlib
# generate images without having a window appear
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap, cm
#import cartopy.crs as ccrs
#from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
#import iris
#import iris.plot as iplt
#import iris.quickplot as qplt

##########################################################################
###########################   Units vacabulory   #########################
# cpT:  [J / kg C] * [C]     = [J / kg]
# rho cpT dxdydz = [m/s] * [J / kg] * [kg/m3] * m * m * m = [J]
##########################################################################

# print the system structure and the path of the kernal
print platform.architecture()
print os.path

# switch on the seaborn effect
#sns.set()

# calculate the time for the code execution
start_time = tttt.time()# gz in [m2 / s2] = [ kg m2 / kg s2 ] = [J / kg]

# Redirect all the console output to a file
#sys.stdout = open('F:\DataBase\ORAS4\console.out','w')
sys.stdout = open('/project/Reanalysis/ORAS4/Monthly/Model/console_E.out','w')

# logging level 'DEBUG' 'INFO' 'WARNING' 'ERROR' 'CRITICAL'
#logging.basicConfig(filename = 'F:\DataBase\ORAS4\history.log', filemode = 'w',level = logging.DEBUG,format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.basicConfig(filename = '/project/Reanalysis/ORAS4/Monthly/Model/history_E.log',
                    filemode = 'w', level = logging.DEBUG,
                    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# define the constant:
constant ={'g' : 9.80616,      # gravititional acceleration [m / s2]
           'R' : 6371009,      # radius of the earth [m]
           'cp': 3987,         # heat capacity of sea water [J/(Kg*K)]
           'rho': 1027,        # sea water density [Kg/m3]
            }

################################   Input zone  ######################################
# specify data path
#datapath = 'F:\DataBase\ORAS\ORAS4\Monthly\model'
datapath = '/project/Reanalysis/ORAS4/Monthly/Model'
# time of the data, which concerns with the name of input
# starting time (year)
start_year = 1958
# Ending time, if only for 1 year, then it should be the same as starting year
end_year = 2014
# specify output path for the netCDF4 file
#output_path_fig = 'C:\Yang\PhD\Computation and Modeling\Blue Action\OMET\ORAS4'
output_path = '/project/Reanalysis/ORAS4/Monthly/Model/output'
# benchmark datasets for basic dimensions
#benchmark_path = 'F:\DataBase\ORAS\ORAS4\Monthly\model\\thetao_oras4_1m_1979_grid_T.nc'
#benchmark = Dataset(benchmark_path)
####################################################################################

def var_key(datapath, year):
    # get the path to each datasets
    print "Start retrieving datasets"
    logging.info("Start retrieving variables theta,s,u,v from %d (y)" % (year))
    datapath_theta = datapath + os.sep + 'theta' + os.sep + 'thetao_oras4_1m_%d_grid_T.nc' % (year)
    datapath_s = datapath + os.sep + 's' + os.sep + 'so_oras4_1m_%d_grid_T.nc' % (year)
    datapath_u = datapath + os.sep + 'u' + os.sep + 'uo_oras4_1m_%d_grid_U.nc' % (year)
    datapath_v = datapath + os.sep + 'v' + os.sep + 'vo_oras4_1m_%d_grid_V.nc' % (year)

    # get the variable keys
    theta_key = Dataset(datapath_theta)
    s_key = Dataset(datapath_s)
    u_key = Dataset(datapath_u)
    v_key = Dataset(datapath_v)

    print "Retrieving datasets for the year %d successfully!" % (year)
    logging.info("Retrieving variables for the year %d successfully!" % (year))
    return theta_key, s_key, u_key, v_key

def var_coordinate(datapath):
    '''
    Retrive ORCA1_Z42 grid information and land-sea mask
    '''
    print "Start retrieving the datasets of ORCA1 coordinate and mask info"
    logging.info('Start retrieving the datasets of ORCA1 coordinate and mask info')
    # get the variable keys
    mesh_mask_key = Dataset(datapath+ os.sep + 'mesh_mask.nc')
    subbasin_mesh_key = Dataset(datapath+ os.sep + 'basinmask_050308_UKMO.nc') #sub-basin from DRAKKER project
    #grid_T_key = Dataset(datapath+ os.sep + 'coordinates_grid_T.nc')
    #grid_U_key = Dataset(datapath+ os.sep + 'coordinates_grid_U.nc')
    #grid_V_key = Dataset(datapath+ os.sep + 'coordinates_grid_V.nc')
    #extract variables
    # lat-lon-depth coordinate info
    nav_lat = mesh_mask_key.variables['nav_lat'][:]
    nav_lon = mesh_mask_key.variables['nav_lon'][:]
    nav_lev = mesh_mask_key.variables['nav_lev'][:]
    # lat-lon coordinate of V grid
    gphiv = mesh_mask_key.variables['gphiv'][0,:,:] # lat from -78 to -89
    glamv = mesh_mask_key.variables['glamv'][0,:,:] # lon from -179 to 179
    gphiu = mesh_mask_key.variables['gphiu'][0,:,:] # lat from -78 to -89
    glamu = mesh_mask_key.variables['glamu'][0,:,:] # lon from -179 to 179
    # land-sea mask
    tmask = mesh_mask_key.variables['tmask'][0,:,:,:]
    umask = mesh_mask_key.variables['umask'][0,:,:,:]
    vmask = mesh_mask_key.variables['vmask'][0,:,:,:]
    # land-sea mask for sub-basin
    tmaskatl = subbasin_mesh_key.variables['tmaskatl'][:] # attention that the size is different!
    # grid spacing scale factors (zonal)
    e1t = mesh_mask_key.variables['e1t'][0,:,:]
    e2t = mesh_mask_key.variables['e2t'][0,:,:]
    e1u = mesh_mask_key.variables['e1u'][0,:,:]
    e2u = mesh_mask_key.variables['e2u'][0,:,:]
    e1v = mesh_mask_key.variables['e1v'][0,:,:]
    e2v = mesh_mask_key.variables['e2v'][0,:,:]
    # take the bathymetry
    mbathy = mesh_mask_key.variables['mbathy'][0,:,:]
    # depth of each layer
    e3t_0 = mesh_mask_key.variables['e3t_0'][0,:]
    e3t_ps = mesh_mask_key.variables['e3t_ps'][0,:,:] # depth of partial t cell
    # depth of partial cell t point
    hdept_0 = mesh_mask_key.variables['hdept'][0,:,:]
    # comparison between variables
    #lat_grid_T = grid_T_key.variables['lat'][:]
    #lon_grid_T = grid_T_key.variables['lon'][:]
    #tmask_grid_T = grid_T_key.variables['tmask'][:]

    #lat_grid_U = grid_U_key.variables['lat'][:]
    #lon_grid_U = grid_U_key.variables['lon'][:]
    #umask_grid_U = grid_U_key.variables['umask'][:]

    #lat_grid_V = grid_V_key.variables['lat'][:]
    #lon_grid_V = grid_V_key.variables['lon'][:]
    #vmask_grid_V = grid_V_key.variables['vmask'][:]

    return nav_lat, nav_lon, nav_lev, tmask, umask, vmask, tmaskatl, e1t, e2t, e1u, e2u, e1v, e2v, gphiu, glamu, gphiv, glamv, mbathy, e3t_0, e3t_ps, hdept_0

def mass_transport(v_key,e1v):
    '''
    This function is used to calculate the mass transport.
    The unit is Sv (1E+6 m3/s)
    '''
    print "Compute the meridional overturning stream function for globle and Atlantic!"
    logging.info('Compute the meridional overturning stream function for globle and Atlantic!')
    #dominant equation for stream function
    # psi = e1v(m) * rho(kg/m3) * v(m/s) * dz(m) = (kg/s)
    # extract variables
    #u = u_key.variables['uo'][:]
    v = v_key.variables['vo'][:]
    # define the stream function psi
    psi_globe = np.zeros((len(index_month),level,jj,ji),dtype=float)
    psi_atlantic = np.zeros((len(index_month),level,jj,ji),dtype=float)
    # expand the grid size matrix e1v to avoid more loops
    e1v_3D = np.repeat(e1v[np.newaxis,:,:],level,0)
    e1v_4D = np.repeat(e1v_3D[np.newaxis,:,:,:],len(index_month),0)
    # increase the dimension of vmask
    vmask_4D = np.repeat(vmask[np.newaxis,:,:,:],len(index_month),0)
    tmaskatl_3D = np.repeat(tmaskatl[np.newaxis,:,:],level,0)
    tmaskatl_4D = np.repeat(tmaskatl_3D[np.newaxis,:,:,:],len(index_month),0)
    # increase the dimension of partial cell adjustment matrix
    e3t_adjust_4D = np.repeat(e3t_adjust[np.newaxis,:,:,:],len(index_month),0)
    # take the integral from sea bottom to the surface
    for i in np.arange(level):
        psi_globe[:,i,:,:] = e1v_4D[:,i,:,:] * v[:,i,:,:] * vmask_4D[:,i,:,:] * e3t_0[i] -\
                             e1v_4D[:,i,:,:] * v[:,i,:,:] * vmask_4D[:,i,:,:] * e3t_adjust_4D[:,i,:,:]
        psi_atlantic[:,i,:,:] = e1v_4D[:,i,:,:] * v[:,i,:,:] * vmask_4D[:,i,:,:] * e3t_0[i] * tmaskatl_4D[:,i,:,:] -\
                                e1v_4D[:,i,:,:] * v[:,i,:,:] * vmask_4D[:,i,:,:] * e3t_adjust_4D[:,i,:,:] * tmaskatl_4D[:,i,:,:]
    # take the zonal integral
    psi_globe_zonal_int = np.sum(psi_globe,3)/1e+6 # the unit is changed to Sv
    psi_atlantic_zonal_int = np.sum(psi_atlantic,3)/1e+6 # the unit is changed to Sv
    # take the vertical integral
    psi_globe_vert_int = np.sum(psi_globe,1)/1e+6 # the unit is changed to Sv
    psi_atlantic_vert_int = np.sum(psi_atlantic,1)/1e+6 # the unit is changed to Sv

    print "Compute the mass transport for globle and Atlantic successfully!"
    logging.info('Compute the mass transport for globle and Atlantic successfully!')

    return psi_globe_zonal_int, psi_atlantic_zonal_int, psi_globe_vert_int, psi_atlantic_vert_int

def ocean_heat_content(theta_key):
    '''
    Compute the meridional energy transport in the ocean
    '''
    # extract variables
    print "Start extracting variables for the quantification of meridional energy transport."
    theta = theta_key.variables['thetao'][:] # the unit of theta is Celsius!
    print 'Extracting variables successfully!'
    #logging.info("Extracting variables successfully!")
    # calculate heat flux at each grid point
    OHC_globe = np.zeros((len(index_month),level,jj,ji),dtype=float)
    OHC_atlantic = np.zeros((len(index_month),level,jj,ji),dtype=float)
    # expand the grid size matrix e1v to avoid more loops
    e1t_3D = np.repeat(e1t[np.newaxis,:,:],level,0)
    e1t_4D = np.repeat(e1t_3D[np.newaxis,:,:,:],len(index_month),0)
    e2t_3D = np.repeat(e2t[np.newaxis,:,:],level,0)
    e2t_4D = np.repeat(e2t_3D[np.newaxis,:,:,:],len(index_month),0)
    # increase the dimension of tmask
    tmask_4D = np.repeat(tmask[np.newaxis,:,:,:],len(index_month),0)
    tmaskatl_3D = np.repeat(tmaskatl[np.newaxis,:,:],level,0)
    tmaskatl_4D = np.repeat(tmaskatl_3D[np.newaxis,:,:,:],len(index_month),0)
    # increase the dimension of partial cell adjustment matrix
    e3t_adjust_4D = np.repeat(e3t_adjust[np.newaxis,:,:,:],len(index_month),0)
    for i in np.arange(level):
        OHC_globe[:,i,:,:] = constant['rho'] * constant['cp'] * theta[:,i,:,:] * e1t_4D[:,i,:,:] * e2t_4D[:,i,:,:] * e3t_0[i] * tmask_4D[:,i,:,:] -\
                             constant['rho'] * constant['cp'] * theta[:,i,:,:] * e1t_4D[:,i,:,:] * e2t_4D[:,i,:,:] * e3t_adjust_4D[:,i,:,:] * tmask_4D[:,i,:,:]
        OHC_atlantic[:,i,:,:] = constant['rho'] * constant['cp'] * theta[:,i,:,:] * e1t_4D[:,i,:,:] * e2t_4D[:,i,:,:] * e3t_0[i] * tmask_4D[:,i,:,:] * tmaskatl_4D[:,i,:,:] -\
                                constant['rho'] * constant['cp'] * theta[:,i,:,:] * e1t_4D[:,i,:,:] * e2t_4D[:,i,:,:] * e3t_adjust_4D[:,i,:,:] * tmask_4D[:,i,:,:] * tmaskatl_4D[:,i,:,:]
    # take the zonal integral
    OHC_globe_zonal_int = np.sum(OHC_globe,3)/1e+12 # the unit is changed to tera joule
    OHC_atlantic_zonal_int = np.sum(OHC_atlantic,3)/1e+12 # the unit is changed to tera joule
    # take the vertical integral
    OHC_globe_vert_int = np.sum(OHC_globe,1)/1e+12 # the unit is changed to tera joule
    OHC_atlantic_vert_int = np.sum(OHC_atlantic,1)/1e+12 # the unit is changed to tera joule
    # ocean heat content for certain layers
    # surface to 500m
    OHC_globe_vert_0_500 = np.sum(OHC_globe[:,0:22,:,:],1)/1e+12 # the unit is changed to tera joule
    OHC_atlantic_vert_0_500 = np.sum(OHC_atlantic[:,0:22,:,:],1)/1e+12 # the unit is changed to tera joule
    # 500m to 1000m
    OHC_globe_vert_500_1000 = np.sum(OHC_globe[:,23:26,:,:],1)/1e+12         # layer 26 is in between 800 - 1200
    OHC_atlantic_vert_500_1000 = np.sum(OHC_atlantic[:,23:26,:,:],1)/1e+12
    # 1000m to 2000m
    OHC_globe_vert_1000_2000 = np.sum(OHC_globe[:,27:30,:,:],1)/1e+12
    OHC_atlantic_vert_1000_2000 = np.sum(OHC_atlantic[:,27:30,:,:],1)/1e+12
    # 2000 to bottom
    OHC_globe_vert_2000_inf = np.sum(OHC_globe[:,31:,:,:],1)/1e+12
    OHC_atlantic_vert_2000_inf = np.sum(OHC_atlantic[:,31:,:,:],1)/1e+12
    print '*****************************************************************************'
    print "*****    Computation of ocean heat content in the ocean is finished     *****"
    print "************         The result is in tera-joule (1E+12)         ************"
    print '*****************************************************************************'
    return OHC_globe_zonal_int, OHC_atlantic_zonal_int, OHC_globe_vert_int, OHC_atlantic_vert_int,\
           OHC_globe_vert_0_500, OHC_atlantic_vert_0_500, OHC_globe_vert_500_1000, OHC_atlantic_vert_500_1000,\
           OHC_globe_vert_1000_2000, OHC_atlantic_vert_1000_2000, OHC_globe_vert_2000_inf, OHC_atlantic_vert_2000_inf

def field_statistics(theta_key, u_key, v_key):
    # extract variables
    print "Start extracting variables for the quantification of meridional energy transport."
    theta = theta_key.variables['thetao'][:] # the unit of theta is Celsius!
    u = u_key.variables['uo'][:]
    v = v_key.variables['vo'][:]
    print 'Extracting variables successfully!'
    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!#
    # Due to the nature of the land-sea mask, when we take the mean value we can not
    # use the np.mean to calculate it from the original field, as there are so many
    # empty points. Instead, we must calculate the sum of each variable and then
    # devide the sum of mask.
    # For the mean, we also have to take the cell scale (length, width, height) into
    # consider
    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!#
    # increase the dimension of mask array
    tmask_4D = np.repeat(tmask[np.newaxis,:,:,:],len(index_month),0)
    umask_4D = np.repeat(umask[np.newaxis,:,:,:],len(index_month),0)
    vmask_4D = np.repeat(vmask[np.newaxis,:,:,:],len(index_month),0)
    tmaskatl_3D = np.repeat(tmaskatl[np.newaxis,:,:],level,0)
    tmaskatl_4D = np.repeat(tmaskatl_3D[np.newaxis,:,:,:],len(index_month),0)
    hdept_0_3D = np.repeat(hdept_0[np.newaxis,:,:],len(index_month),0)
    # increase the dimension of partial cell adjustment matrix
    e3t_adjust_4D = np.repeat(e3t_adjust[np.newaxis,:,:,:],len(index_month),0)
    # expand the grid size matrix e1v to avoid more loops
    e1t_3D = np.repeat(e1t[np.newaxis,:,:],level,0)
    e1t_4D = np.repeat(e1t_3D[np.newaxis,:,:,:],len(index_month),0)
    e1u_3D = np.repeat(e1u[np.newaxis,:,:],level,0)
    e1u_4D = np.repeat(e1u_3D[np.newaxis,:,:,:],len(index_month),0)
    e1v_3D = np.repeat(e1v[np.newaxis,:,:],level,0)
    e1v_4D = np.repeat(e1v_3D[np.newaxis,:,:,:],len(index_month),0)

    # vertical mean
    theta_globe_vert_weight = np.zeros((len(index_month),level,jj,ji),dtype=float)
    u_globe_vert_weight = np.zeros((len(index_month),level,jj,ji),dtype=float)
    v_globe_vert_weight = np.zeros((len(index_month),level,jj,ji),dtype=float)

    for i in np.arange(level):
        theta_globe_vert_weight[:,i,:,:] = theta[:,i,:,:] * e3t_0[i] * tmask_4D[:,i,:,:] -\
                                           theta[:,i,:,:] * e3t_adjust_4D[:,i,:,:] * tmask_4D[:,i,:,:]
        u_globe_vert_weight[:,i,:,:] = u[:,i,:,:] * e3t_0[i] * umask_4D[:,i,:,:] -\
                                       u[:,i,:,:] * e3t_adjust_4D[:,i,:,:] * umask_4D[:,i,:,:]
        v_globe_vert_weight[:,i,:,:] = v[:,i,:,:] * e3t_0[i] * vmask_4D[:,i,:,:] -\
                                       v[:,i,:,:] * e3t_adjust_4D[:,i,:,:] * vmask_4D[:,i,:,:]

    theta_globe_vert_mean = np.sum(theta_globe_vert_weight,1) / hdept_0_3D
    u_globe_vert_mean = np.sum(u_globe_vert_weight,1) / hdept_0_3D
    v_globe_vert_mean = np.sum(v_globe_vert_weight,1) / hdept_0_3D

    # zonal mean
    # take the sum of variables
    theta_globe_zonal_weight = np.zeros((len(index_month),level,jj,ji),dtype=float)
    u_globe_zonal_weight = np.zeros((len(index_month),level,jj,ji),dtype=float)
    v_globe_zonal_weight = np.zeros((len(index_month),level,jj,ji),dtype=float)
    theta_atlantic_zonal_weight = np.zeros((len(index_month),level,jj,ji),dtype=float)
    u_atlantic_zonal_weight = np.zeros((len(index_month),level,jj,ji),dtype=float)
    v_atlantic_zonal_weight = np.zeros((len(index_month),level,jj,ji),dtype=float)

    for i in np.arange(level):
        theta_globe_zonal_weight[:,i,:,:] = theta[:,i,:,:] * e1t_4D[:,i,:,:] * tmask_4D[:,i,:,:]
        theta_atlantic_zonal_weight[:,i,:,:] = theta[:,i,:,:] * e1t_4D[:,i,:,:] * tmask_4D[:,i,:,:] * tmaskatl_4D[:,i,:,:]
        u_globe_zonal_weight[:,i,:,:] = u[:,i,:,:] * e1u_4D[:,i,:,:] * umask_4D[:,i,:,:]
        u_atlantic_zonal_weight[:,i,:,:] = u[:,i,:,:] * e1u_4D[:,i,:,:] * umask_4D[:,i,:,:] * tmaskatl_4D[:,i,:,:]
        v_globe_zonal_weight[:,i,:,:] = v[:,i,:,:] * e1v_4D[:,i,:,:] * vmask_4D[:,i,:,:]
        v_atlantic_zonal_weight[:,i,:,:] = v[:,i,:,:] * e1v_4D[:,i,:,:] * vmask_4D[:,i,:,:] * tmaskatl_4D[:,i,:,:]

    # take the zonal mean
    theta_globe_zonal_mean = np.sum(theta_globe_zonal_weight,3) / np.sum(e1t_4D * tmask_4D,3)
    theta_atlantic_zonal_mean = np.sum(theta_atlantic_zonal_weight,3) / np.sum(e1t_4D * tmask_4D * tmaskatl_4D,3)
    u_globe_zonal_mean = np.sum(u_globe_zonal_weight,3) / np.sum(e1u_4D * umask_4D,3)
    u_atlantic_zonal_mean = np.sum(u_atlantic_zonal_weight,3) / np.sum(e1u_4D * umask_4D * tmaskatl_4D,3)
    v_globe_zonal_mean = np.sum(v_globe_zonal_weight,3) / np.sum(e1v_4D * vmask_4D,3)
    v_atlantic_zonal_mean = np.sum(v_atlantic_zonal_weight,3) / np.sum(e1v_4D * vmask_4D * tmaskatl_4D,3)

    return theta_globe_vert_mean, u_globe_vert_mean, v_globe_vert_mean,\
           theta_globe_zonal_mean, theta_atlantic_zonal_mean, u_globe_zonal_mean,\
           u_atlantic_zonal_mean, v_globe_zonal_mean, v_atlantic_zonal_mean

def create_netcdf_point (psi_pool_glo_zonal, psi_pool_atl_zonal, psi_pool_glo_vert, psi_pool_atl_vert,\
                        OHC_pool_glo_zonal, OHC_pool_atl_zonal, OHC_pool_glo_vert, OHC_pool_atl_vert,\
                        OHC_pool_glo_vert_0_500, OHC_pool_atl_vert_0_500, OHC_pool_glo_vert_500_1000,\
                        OHC_pool_atl_vert_500_1000, OHC_pool_glo_vert_1000_2000, OHC_pool_atl_vert_1000_2000,\
                        OHC_pool_glo_vert_2000_inf, OHC_pool_atl_vert_2000_inf, theta_pool_glo_vert,\
                        u_pool_glo_vert, v_pool_glo_vert, theta_pool_glo_zonal, theta_pool_atl_zonal,\
                        u_pool_glo_zonal, u_pool_atl_zonal, v_pool_glo_zonal, v_pool_atl_zonal ,output_path):
    print '*******************************************************************'
    print '*********************** create netcdf file ************************'
    print '********************    statistics on ORCA   **********************'
    print '*******************************************************************'
    logging.info("Start creating netcdf file for the statistics of fields at each grid point.")
    # wrap the datasets into netcdf file
    # 'NETCDF3_CLASSIC', 'NETCDF3_64BIT', 'NETCDF4_CLASSIC', and 'NETCDF4'
    data_wrap = Dataset(output_path + os.sep + 'oras4_model_monthly_orca1_statistics_point.nc' ,'w',format = 'NETCDF3_64BIT')
    # create dimensions for netcdf data
    year_wrap_dim = data_wrap.createDimension('year',len(period))
    month_wrap_dim = data_wrap.createDimension('month',12)
    lat_wrap_dim = data_wrap.createDimension('j',jj)
    lon_wrap_dim = data_wrap.createDimension('i',ji)
    lev_wrap_dim = data_wrap.createDimension('lev',level)
    # create variables
    # 1D
    year_wrap_var = data_wrap.createVariable('year',np.int32,('year',))
    month_wrap_var = data_wrap.createVariable('month',np.int32,('month',))
    lat_wrap_var = data_wrap.createVariable('latitude_aux',np.float32,('j',))
    lev_wrap_var = data_wrap.createVariable('lev',np.float32,('lev',))
    # 2D
    gphit_wrap_var = data_wrap.createVariable('gphit',np.float32,('j','i'))
    glamt_wrap_var = data_wrap.createVariable('glamt',np.float32,('j','i'))
    gphiu_wrap_var = data_wrap.createVariable('gphiu',np.float32,('j','i'))
    glamu_wrap_var = data_wrap.createVariable('glamu',np.float32,('j','i'))
    gphiv_wrap_var = data_wrap.createVariable('gphiv',np.float32,('j','i'))
    glamv_wrap_var = data_wrap.createVariable('glamv',np.float32,('j','i'))
    # 4D
    psi_glo_zonal_wrap_var = data_wrap.createVariable('psi_glo_zonal',np.float64,('year','month','lev','j'))
    psi_atl_zonal_wrap_var = data_wrap.createVariable('psi_atl_zonal',np.float64,('year','month','lev','j'))
    OHC_glo_zonal_wrap_var = data_wrap.createVariable('OHC_glo_zonal',np.float64,('year','month','lev','j'))
    OHC_atl_zonal_wrap_var = data_wrap.createVariable('OHC_atl_zonal',np.float64,('year','month','lev','j'))
    theta_glo_zonal_wrap_var = data_wrap.createVariable('theta_glo_zonal',np.float64,('year','month','lev','j'))
    theta_atl_zonal_wrap_var = data_wrap.createVariable('theta_atl_zonal',np.float64,('year','month','lev','j'))
    u_glo_zonal_wrap_var = data_wrap.createVariable('u_glo_zonal',np.float64,('year','month','lev','j'))
    u_atl_zonal_wrap_var = data_wrap.createVariable('u_atl_zonal',np.float64,('year','month','lev','j'))
    v_glo_zonal_wrap_var = data_wrap.createVariable('v_glo_zonal',np.float64,('year','month','lev','j'))
    v_atl_zonal_wrap_var = data_wrap.createVariable('v_atl_zonal',np.float64,('year','month','lev','j'))

    psi_glo_vert_wrap_var = data_wrap.createVariable('psi_glo_vert',np.float64,('year','month','j','i'))
    psi_atl_vert_wrap_var = data_wrap.createVariable('psi_atl_vert',np.float64,('year','month','j','i'))
    OHC_glo_vert_wrap_var = data_wrap.createVariable('OHC_glo_vert',np.float64,('year','month','j','i'))
    OHC_atl_vert_wrap_var = data_wrap.createVariable('OHC_atl_vert',np.float64,('year','month','j','i'))
    OHC_glo_vert_0_500_wrap_var = data_wrap.createVariable('OHC_glo_vert_0_500',np.float64,('year','month','j','i'))
    OHC_atl_vert_0_500_wrap_var = data_wrap.createVariable('OHC_atl_vert_0_500',np.float64,('year','month','j','i'))
    OHC_glo_vert_500_1000_wrap_var = data_wrap.createVariable('OHC_glo_vert_500_1000',np.float64,('year','month','j','i'))
    OHC_atl_vert_500_1000_wrap_var = data_wrap.createVariable('OHC_atl_vert_500_1000',np.float64,('year','month','j','i'))
    OHC_glo_vert_1000_2000_wrap_var = data_wrap.createVariable('OHC_glo_vert_1000_2000',np.float64,('year','month','j','i'))
    OHC_atl_vert_1000_2000_wrap_var = data_wrap.createVariable('OHC_atl_vert_1000_2000',np.float64,('year','month','j','i'))
    OHC_glo_vert_2000_inf_wrap_var = data_wrap.createVariable('OHC_glo_vert_2000_inf',np.float64,('year','month','j','i'))
    OHC_atl_vert_2000_inf_wrap_var = data_wrap.createVariable('OHC_atl_vert_2000_inf',np.float64,('year','month','j','i'))
    theta_glo_vert_wrap_var = data_wrap.createVariable('theta_glo_vert',np.float64,('year','month','j','i'))
    u_glo_vert_wrap_var = data_wrap.createVariable('u_glo_vert',np.float64,('year','month','j','i'))
    v_glo_vert_wrap_var = data_wrap.createVariable('v_glo_vert',np.float64,('year','month','j','i'))

    # global attributes
    data_wrap.description = 'Monthly mean statistics of fields on ORCA grid'
    # variable attributes
    lev_wrap_var.units = 'm'
    gphit_wrap_var.units = 'ORCA1_latitude_Tgrid'
    glamt_wrap_var.units = 'ORCA1_longitude_Tgrid'
    gphiu_wrap_var.units = 'ORCA1_latitude_ugrid'
    glamu_wrap_var.units = 'ORCA1_longitude_ugrid'
    gphiv_wrap_var.units = 'ORCA1_latitude_vgrid'
    glamv_wrap_var.units = 'ORCA1_longitude_vgrid'

    psi_glo_zonal_wrap_var.units = 'Sv'
    psi_atl_zonal_wrap_var.units = 'Sv'
    OHC_glo_zonal_wrap_var.units = 'tera joule'
    OHC_atl_zonal_wrap_var.units = 'tera joule'
    theta_glo_zonal_wrap_var.units = 'Celsius'
    theta_atl_zonal_wrap_var.units = 'Celsius'
    u_glo_zonal_wrap_var.units = 'm/s'
    u_atl_zonal_wrap_var.units = 'm/s'
    v_glo_zonal_wrap_var.units = 'm/s'
    v_atl_zonal_wrap_var.units = 'm/s'

    psi_glo_vert_wrap_var.units = 'Sv'
    psi_atl_vert_wrap_var.units = 'Sv'
    OHC_glo_vert_wrap_var.units = 'tera joule'
    OHC_atl_vert_wrap_var.units = 'tera joule'
    OHC_glo_vert_0_500_wrap_var.units = 'tera joule'
    OHC_atl_vert_0_500_wrap_var.units = 'tera joule'
    OHC_glo_vert_500_1000_wrap_var.units = 'tera joule'
    OHC_atl_vert_500_1000_wrap_var.units = 'tera joule'
    OHC_glo_vert_1000_2000_wrap_var.units = 'tera joule'
    OHC_atl_vert_1000_2000_wrap_var.units = 'tera joule'
    OHC_glo_vert_2000_inf_wrap_var.units = 'tera joule'
    OHC_atl_vert_2000_inf_wrap_var.units = 'tera joule'
    theta_glo_vert_wrap_var.units = 'Celsius'
    u_glo_vert_wrap_var.units = 'm/s'
    v_glo_vert_wrap_var.units = 'm/s'

    lat_wrap_var.long_name = 'auxillary latitude'
    lev_wrap_var.long_name = 'depth'
    gphit_wrap_var.long_name = 'ORCA1 Tgrid latitude'
    glamt_wrap_var.long_name = 'ORCA1 Tgrid longitude'
    gphiu_wrap_var.long_name = 'ORCA1 ugrid latitude'
    glamu_wrap_var.long_name = 'ORCA1 ugrid longitude'
    gphiv_wrap_var.long_name = 'ORCA1 vgrid latitude'
    glamv_wrap_var.long_name = 'ORCA1 vgrid longitude'

    psi_glo_zonal_wrap_var.long_name = 'Global Meridional Mass Transport (zonal integral)'
    psi_atl_zonal_wrap_var.long_name = 'Atlantic Meridional Mass Transport (zonal integral)'
    OHC_glo_zonal_wrap_var.long_name = 'Global Ocean Heat Content (zonal integral)'
    OHC_atl_zonal_wrap_var.long_name = 'Atlantic Ocean Heat Content (zonal integral)'
    theta_glo_zonal_wrap_var.long_name = 'Global Potential Temperature (zonal mean)'
    theta_atl_zonal_wrap_var.long_name = 'Atlantic Potential Temperature (zonal mean)'
    u_glo_zonal_wrap_var.long_name = 'Global Zonal Velocity (zonal mean)'
    u_atl_zonal_wrap_var.long_name = 'Atlantic Zonal Velocity (zonal mean)'
    v_glo_zonal_wrap_var.long_name = 'Global Meridional Velocity (zonal mean)'
    v_atl_zonal_wrap_var.long_name = 'Atlantic Meridional Velocity (zonal mean)'

    psi_glo_vert_wrap_var.long_name = 'Global Meridional Mass Transport (vertical integral)'
    psi_atl_vert_wrap_var.long_name = 'Atlantic Meridional Mass Transport (vertical integral)'
    OHC_glo_vert_wrap_var.long_name = 'Global Ocean Heat Content (vertical integral)'
    OHC_atl_vert_wrap_var.long_name = 'Atlantic Ocean Heat Content (vertical integral)'
    OHC_glo_vert_0_500_wrap_var.long_name = 'Global Ocean Heat Content from surface to 500 m (vertical integral)'
    OHC_atl_vert_0_500_wrap_var.long_name = 'Atlantic Ocean Heat Content from surface to 500 m (vertical integral)'
    OHC_glo_vert_500_1000_wrap_var.long_name = 'Global Ocean Heat Content from 500 m to 1000 m (vertical integral)'
    OHC_atl_vert_500_1000_wrap_var.long_name = 'Atlantic Ocean Heat Content from 500 m to 1000 m (vertical integral)'
    OHC_glo_vert_1000_2000_wrap_var.long_name = 'Global Ocean Heat Content from 1000 m to 2000 m (vertical integral)'
    OHC_atl_vert_1000_2000_wrap_var.long_name = 'Atlantic Ocean Heat Content from 1000 m to 2000 m (vertical integral)'
    OHC_glo_vert_2000_inf_wrap_var.long_name = 'Global Ocean Heat Content from 2000 m to bottom (vertical integral)'
    OHC_atl_vert_2000_inf_wrap_var.long_name = 'Atlantic Ocean Heat Content from 2000 m to bottom (vertical integral)'
    theta_glo_vert_wrap_var.long_name = 'Global Potential Temperature (vertical mean)'
    u_glo_vert_wrap_var.long_name = 'Global Zonal Velocity (vertical mean)'
    v_glo_vert_wrap_var.long_name = 'Global Meridional Velocity (vertical mean)'
    # writing data
    year_wrap_var[:] = period
    month_wrap_var[:] = np.arange(1,13,1)
    lat_wrap_var[:] = gphiv[:,96]
    lev_wrap_var[:] = nav_lev
    gphit_wrap_var[:] = nav_lat
    glamt_wrap_var[:] = nav_lon
    gphiu_wrap_var[:] = gphiu
    glamu_wrap_var[:] = glamu
    gphiv_wrap_var[:] = gphiv
    glamv_wrap_var[:] = glamv

    psi_glo_zonal_wrap_var[:] = psi_pool_glo_zonal
    psi_atl_zonal_wrap_var[:] = psi_pool_atl_zonal
    OHC_glo_zonal_wrap_var[:] = OHC_pool_glo_zonal
    OHC_atl_zonal_wrap_var[:] = OHC_pool_atl_zonal
    theta_glo_zonal_wrap_var[:] = theta_pool_glo_zonal
    theta_atl_zonal_wrap_var[:] = theta_pool_atl_zonal
    u_glo_zonal_wrap_var[:] = u_pool_glo_zonal
    u_atl_zonal_wrap_var[:] = u_pool_atl_zonal
    v_glo_zonal_wrap_var[:] = v_pool_glo_zonal
    v_atl_zonal_wrap_var[:] = v_pool_atl_zonal

    psi_glo_vert_wrap_var[:] = psi_pool_glo_vert
    psi_atl_vert_wrap_var[:] = psi_pool_atl_vert
    OHC_glo_vert_wrap_var[:] = OHC_pool_glo_vert
    OHC_atl_vert_wrap_var[:] = OHC_pool_atl_vert
    OHC_glo_vert_0_500_wrap_var[:] = OHC_pool_glo_vert_0_500
    OHC_atl_vert_0_500_wrap_var[:] = OHC_pool_atl_vert_0_500
    OHC_glo_vert_500_1000_wrap_var[:] = OHC_pool_glo_vert_500_1000
    OHC_atl_vert_500_1000_wrap_var[:] = OHC_pool_atl_vert_500_1000
    OHC_glo_vert_1000_2000_wrap_var[:] = OHC_pool_glo_vert_1000_2000
    OHC_atl_vert_1000_2000_wrap_var[:] = OHC_pool_atl_vert_1000_2000
    OHC_glo_vert_2000_inf_wrap_var[:] = OHC_pool_glo_vert_2000_inf
    OHC_atl_vert_2000_inf_wrap_var[:] = OHC_pool_atl_vert_2000_inf
    theta_glo_vert_wrap_var[:] = theta_pool_glo_vert
    u_glo_vert_wrap_var[:] = u_pool_glo_vert
    v_glo_vert_wrap_var[:] = v_pool_glo_vert
    # close the file
    data_wrap.close()
    print "Create netcdf file successfully"
    logging.info("The generation of netcdf files for the statisticas of fields in ORAS4 on each grid point is complete!!")

if __name__=="__main__":
    # create the year index
    period = np.arange(start_year,end_year+1,1)
    index_month = np.arange(12)
    # ORCA1_z42 grid infor (Madec and Imbard 1996)
    ji = 362
    jj = 292
    level = 42
    # extract the mesh_mask and coordinate information
    nav_lat, nav_lon, nav_lev, tmask, umask, vmask, tmaskatl, e1t, e2t, e1u, e2u, e1v, e2v,\
    gphiu, glamu, gphiv, glamv, mbathy, e3t_0, e3t_ps, hdept_0 = var_coordinate(datapath)
    print '*******************************************************************'
    print '*******************  Partial cells correction   *******************'
    print '*******************************************************************'
    # construct partial cell depth matrix
    # the size of partial cell is given by e3t_ps
    # for the sake of simplicity of the code, just calculate the difference between e3t_0 and e3t_ps
    # then minus this adjustment when calculate the OMET at each layer with mask
    # Attention! Since python start with 0, the partial cell info given in mbathy should incoporate with this
    e3t_adjust = np.zeros((level,jj,ji),dtype = float)
    for i in np.arange(1,level,1): # start from 1
        for j in np.arange(jj):
            for k in np.arange(ji):
                if i == mbathy[j,k]:
                    e3t_adjust[i-1,j,k] = e3t_0[i-1] - e3t_ps[j,k] # python start with 0, so i-1
    print '*******************************************************************'
    print '************************ create data pool *************************'
    print '*******************************************************************'
    # create a data pool to save the OHC for each year and month
    # zonal integral (vertical profile)
    OHC_pool_glo_zonal = np.zeros((len(period),12,level,jj),dtype = float)
    OHC_pool_atl_zonal = np.zeros((len(period),12,level,jj),dtype = float)
    # vertical integral (horizontal profile)
    OHC_pool_glo_vert = np.zeros((len(period),12,jj,ji),dtype = float)
    OHC_pool_atl_vert = np.zeros((len(period),12,jj,ji),dtype = float)
    # vertical integral (horizontal profile) and OHC for certain layers
    OHC_pool_glo_vert_0_500 = np.zeros((len(period),12,jj,ji),dtype = float)
    OHC_pool_atl_vert_0_500 = np.zeros((len(period),12,jj,ji),dtype = float)
    OHC_pool_glo_vert_500_1000 = np.zeros((len(period),12,jj,ji),dtype = float)
    OHC_pool_atl_vert_500_1000 = np.zeros((len(period),12,jj,ji),dtype = float)
    OHC_pool_glo_vert_1000_2000 = np.zeros((len(period),12,jj,ji),dtype = float)
    OHC_pool_atl_vert_1000_2000 = np.zeros((len(period),12,jj,ji),dtype = float)
    OHC_pool_glo_vert_2000_inf = np.zeros((len(period),12,jj,ji),dtype = float)
    OHC_pool_atl_vert_2000_inf = np.zeros((len(period),12,jj,ji),dtype = float)
    # create a data pool to save the mass transport for each year and month
    # zonal integral (vertical profile)
    psi_pool_glo_zonal = np.zeros((len(period),12,level,jj),dtype = float)
    psi_pool_atl_zonal = np.zeros((len(period),12,level,jj),dtype = float)
    # vertical integral (horizontal profile)
    psi_pool_glo_vert = np.zeros((len(period),12,jj,ji),dtype = float)
    psi_pool_atl_vert = np.zeros((len(period),12,jj,ji),dtype = float)
    # create a data pool to save the mean of fields for each year and month
    # zonal mean (vertical profile)
    theta_pool_glo_zonal = np.zeros((len(period),12,level,jj),dtype = float)
    theta_pool_atl_zonal = np.zeros((len(period),12,level,jj),dtype = float)
    u_pool_glo_zonal = np.zeros((len(period),12,level,jj),dtype = float)
    u_pool_atl_zonal = np.zeros((len(period),12,level,jj),dtype = float)
    v_pool_glo_zonal = np.zeros((len(period),12,level,jj),dtype = float)
    v_pool_atl_zonal = np.zeros((len(period),12,level,jj),dtype = float)
    # vertical mean (horizontal profile)
    theta_pool_glo_vert = np.zeros((len(period),12,jj,ji),dtype = float)
    u_pool_glo_vert = np.zeros((len(period),12,jj,ji),dtype = float)
    v_pool_glo_vert = np.zeros((len(period),12,jj,ji),dtype = float)
    # loop for calculation
    for i in period:
        # get the key of each variable
        theta_key, s_key, u_key, v_key = var_key(datapath, i)
        # calculate the stokes stream function and plot
        psi_globe_zonal, psi_atlantic_zonal, psi_globe_vert, psi_atlantic_vert = mass_transport(v_key,e1v)
        # save output to the pool
        psi_pool_glo_zonal[i-1958,:,:,:] = psi_globe_zonal
        psi_pool_atl_zonal[i-1958,:,:,:] = psi_atlantic_zonal
        psi_pool_glo_vert[i-1958,:,:,:] = psi_globe_vert
        psi_pool_atl_vert[i-1958,:,:,:] = psi_atlantic_vert
        # calculate the meridional energy transport in the ocean
        OHC_glo_zonal, OHC_atl_zonal, OHC_glo_vert, OHC_atl_vert,\
        OHC_glo_vert_0_500, OHC_atl_vert_0_500, OHC_glo_vert_500_1000, OHC_atl_vert_500_1000,\
        OHC_glo_vert_1000_2000, OHC_atl_vert_1000_2000, OHC_glo_vert_2000_inf, OHC_atl_vert_2000_inf\
        = ocean_heat_content(theta_key)
        # save output to the pool
        OHC_pool_glo_zonal[i-1958,:,:,:] = OHC_glo_zonal
        OHC_pool_atl_zonal[i-1958,:,:,:] = OHC_atl_zonal
        OHC_pool_glo_vert[i-1958,:,:,:] = OHC_glo_vert
        OHC_pool_atl_vert[i-1958,:,:,:] = OHC_atl_vert
        OHC_pool_glo_vert_0_500[i-1958,:,:,:] = OHC_glo_vert_0_500
        OHC_pool_atl_vert_0_500[i-1958,:,:,:] = OHC_atl_vert_0_500
        OHC_pool_glo_vert_500_1000[i-1958,:,:,:] = OHC_glo_vert_500_1000
        OHC_pool_atl_vert_500_1000[i-1958,:,:,:] = OHC_atl_vert_500_1000
        OHC_pool_glo_vert_1000_2000[i-1958,:,:,:] = OHC_glo_vert_1000_2000
        OHC_pool_atl_vert_1000_2000[i-1958,:,:,:] = OHC_atl_vert_1000_2000
        OHC_pool_glo_vert_2000_inf[i-1958,:,:,:] = OHC_glo_vert_2000_inf
        OHC_pool_atl_vert_2000_inf[i-1958,:,:,:] = OHC_atl_vert_2000_inf
        # statistical matrix
        # take zonal and vertical mean
        theta_glo_vert, u_glo_vert, v_glo_vert, theta_glo_zonal, theta_atl_zonal,\
        u_glo_zonal, u_atl_zonal, v_glo_zonal, v_atl_zonal= field_statistics(theta_key, u_key, v_key)
        # save output to the pool
        theta_pool_glo_vert[i-1958,:,:,:] = theta_glo_vert
        u_pool_glo_vert[i-1958,:,:,:] = u_glo_vert
        v_pool_glo_vert[i-1958,:,:,:] = v_glo_vert
        theta_pool_glo_zonal[i-1958,:,:,:] = theta_glo_zonal
        theta_pool_atl_zonal[i-1958,:,:,:] = theta_atl_zonal
        u_pool_glo_zonal[i-1958,:,:,:] = u_glo_zonal
        u_pool_atl_zonal[i-1958,:,:,:] = u_atl_zonal
        v_pool_glo_zonal[i-1958,:,:,:] = v_glo_zonal
        v_pool_atl_zonal[i-1958,:,:,:] = v_atl_zonal
    # create NetCDF file and save the output
    create_netcdf_point(psi_pool_glo_zonal, psi_pool_atl_zonal, psi_pool_glo_vert, psi_pool_atl_vert,\
                        OHC_pool_glo_zonal, OHC_pool_atl_zonal, OHC_pool_glo_vert, OHC_pool_atl_vert,\
                        OHC_pool_glo_vert_0_500, OHC_pool_atl_vert_0_500, OHC_pool_glo_vert_500_1000,\
                        OHC_pool_atl_vert_500_1000, OHC_pool_glo_vert_1000_2000, OHC_pool_atl_vert_1000_2000,\
                        OHC_pool_glo_vert_2000_inf, OHC_pool_atl_vert_2000_inf, theta_pool_glo_vert,\
                        u_pool_glo_vert, v_pool_glo_vert, theta_pool_glo_zonal, theta_pool_atl_zonal,\
                        u_pool_glo_zonal, u_pool_atl_zonal, v_pool_glo_zonal, v_pool_atl_zonal, output_path)

print ("--- %s minutes ---" % ((tttt.time() - start_time)/60))
