#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Realtime Plotting Functions
---------------------------
To be used with realtime Fortran driver and
the subset/sens objects

Created on Tue Mar 27 10:03:04 2018

@author: aucolema
"""

import numpy as np
from netCDF4 import Dataset
from cartopy import crs as ccrs
from cartopy import feature as cfeat
from matplotlib import pyplot as plt
import nclcmaps
import matplotlib.patches as patches
from datetime import timedelta

def plotProbs(probpath, wrfrefpath, time, rbox, subset=False):
    '''
    Plots probabilities for a specified time for each response
    function and overlays the response function box. Output
    file specifies subset or full ens as chosen by input.
    
    Inputs
    ------
    probpath ---- string specifying relative or absolute file
                    path of probability netCDF file.
    wrfrefpath -- string specifying relative or absolute file
                    path for the inner domain WRF reference file.
    time -------- response time in number of forecast hours (only
                    used for label purposes).
    rbox -------- tuple of floats with resbonse box bounds in the
                    order (llon, ulon, llat, ulat).
    subset ------ boolean that defaults to False. If True, changes
                    file name to specify that plot is valid for subset.
    '''
    # Get prob data
    probdat = Dataset(probpath)
    probs = probdat.variables['P_HYD'][0]
    
    # Get lat/lon data
    wrfref = Dataset(wrfrefpath)
    clon, clat = wrfref.CEN_LON, wrfref.CEN_LAT
    tlat1, tlat2 = wrfref.TRUELAT1, wrfref.TRUELAT2
    lons, lats = wrfref.variables['XLONG'][0], wrfref.variables['XLAT'][0]
    
    # Build response box
    llon, ulon, llat, ulat = rbox
    width = ulon - llon
    height = ulat - llat 
    
    # Specific to fotran program probcalcSUBSETnew. Change if fortran
    #  code changes.
    rstrs = ['Reflectivity > 40 dBZ', r'UH > 25 m$^2$/s$^2$', 
             r'UH > 100 m$^2$/s$^2$', 'Wind Speed > 40 mph'] 
    figstrs = ['refl40', 'uh25', 'uh100', 'wspd40']

    for i in range(len(rstrs)):
        fig = plt.figure(figsize=(10, 10))
        ax = fig.add_subplot(1, 1, 1, projection=ccrs.LambertConformal(central_longitude=clon, 
                                                                       central_latitude=clat, 
                                                                       standard_parallels=(tlat1, tlat2)))
        state_borders = cfeat.NaturalEarthFeature(category='cultural',
               name='admin_1_states_provinces_lakes', scale='50m', facecolor='None') 
        ax.add_feature(state_borders, linestyle="-", edgecolor='dimgray')
        ax.add_feature(cfeat.BORDERS, edgecolor='dimgray')
        ax.add_feature(cfeat.COASTLINE, edgecolor='dimgray')
        ax.set_extent([lons[:,0].min(), lons[:,-1].max(), lats[0,:].min(), lats[-1,:].max()])
        rbox = patches.Rectangle((llon, llat), width, height, transform=ccrs.PlateCarree(), 
                             fill=False, color='green', linewidth=2., zorder=3.)
        ax.add_patch(rbox)
        cflevels = np.linspace(0., 100., 11)
        prob = ax.contourf(lons, lats, probs[i], cflevels, transform=ccrs.PlateCarree(), 
                           cmap=nclcmaps.cmap('sunshine_9lev'), alpha=0.7, antialiased=True)
        fig.colorbar(prob, fraction=0.046, pad=0.04, orientation='horizontal', label='Probability (Percent)')
        ax.set_title(r'Probability of {} at f{}'.format(rstrs[i], time))
        if subset:
            plt.savefig('{}probsubset_{}'.format(figstrs[i], time))
        else:
            plt.savefig('{}probfullens_{}'.format(figstrs[i], time))
        plt.close()
    return
        
def plotDiff(fullensprobpath, subsetprobpath, wrfrefpath, rbox, time,
             responsedate, stormreports=False):
    '''
    Method that plots the difference in probabilities between a full
    ensemble and ensemble subset. 
    
    Inputs
    ------
    fullensprobpath -- string specifying path of full ensemble
                        probability netCDF output file.
    subsetprobpath --- string specifying path of subset
                        probability netCDF output file.
    wrfrefpath ------- string specifying path of WRF reference
                        file that contains inner domain data.
    rbox ------------- tuple containing bounds of response function
                        box in order (llon, ulon, llat, ulat).
    responsedate ----- string containing response function date in form
                        2-digit year, month, day (ex. 160508 for May 8
                        2016). Will be used to overlay SPC reports.
    stormreports ----- boolean specifying whether to overlay SPC storm
                        reports.
    '''    
    # Get prob data
    fullensprobdat = Dataset(fullensprobpath)
    fullensprob = fullensprobdat.variables['P_HYD'][0]
    subsetprobdat = Dataset(subsetprobpath)
    subsetprob = subsetprobdat.variables['P_HYD'][0]
    
    # Get lat/lon data
    wrfref = Dataset(wrfrefpath)
    clon, clat = wrfref.CEN_LON, wrfref.CEN_LAT
    tlat1, tlat2 = wrfref.TRUELAT1, wrfref.TRUELAT2
    lons, lats = wrfref.variables['XLONG'][0], wrfref.variables['XLAT'][0]
    
    # Build response box
    llon, ulon, llat, ulat = rbox
    width = ulon - llon
    height = ulat - llat 
    
    # Specific to fotran program probcalcSUBSETnew. Change if fortran
    #  code changes.
    rstrs = ['Reflectivity > 40 dBZ', r'UH > 25 m$^2$/s$^2$', 
             r'UH > 100 m$^2$/s$^2$', 'Wind Speed > 40 mph'] 
    figstrs = ['refl40', 'uh25', 'uh100', 'wspd40']
    
    # Pull storm reports if needed.
    if stormreports:
        tor = np.genfromtxt('http://www.spc.noaa.gov/climo/reports/'+
                            responsedate+'_rpts_torn.csv', delimiter=',', 
                            skip_header=1, usecols=(5,6), dtype=str)
        hail = np.genfromtxt('http://www.spc.noaa.gov/climo/reports/'+
                            responsedate+'_rpts_hail.csv', delimiter=',', 
                            skip_header=1, usecols=(5,6), dtype=str)
        tlats = tor[:,0]
        tlons = tor[:,1]
        hlats = hail[:,0]
        hlons = hail[:,1]
    
    for i in range(len(rstrs)):
        fig = plt.figure(figsize=(10, 10))
        ax = fig.add_subplot(1, 1, 1, projection=ccrs.LambertConformal(central_longitude=clon, 
                                                                       central_latitude=clat, 
                                                                       standard_parallels=(tlat1, tlat2)))
        state_borders = cfeat.NaturalEarthFeature(category='cultural',
               name='admin_1_states_provinces_lakes', scale='50m', facecolor='None') 
        ax.add_feature(state_borders, linestyle="-", edgecolor='dimgray')
        ax.add_feature(cfeat.BORDERS, edgecolor='dimgray')
        ax.add_feature(cfeat.COASTLINE, edgecolor='dimgray')
        ax.set_extent([lons[0,:].min(), lons[0,:].max(), lats[:,0].min(), lats[:,0].max()])
        rbox = patches.Rectangle((llon, llat), width, height, transform=ccrs.PlateCarree(), 
                             fill=False, color='green', linewidth=2., zorder=3.)
        ax.add_patch(rbox)
        cflevels = np.linspace(-20., 20., 21)
        prob = ax.contourf(lons, lats, (subsetprob[i] - fullensprob[i]), cflevels, transform=ccrs.PlateCarree(), 
                           cmap=nclcmaps.cmap('ViBlGrWhYeOrRe'),alpha=0.7, antialiased=True)
        ax.scatter(np.array(tlons, dtype=float), np.array(tlats, dtype=float), transform=ccrs.PlateCarree(), c='red', edgecolor='k', label='Tor Report', alpha=0.3)
        ax.scatter(np.array(hlons, dtype=float), np.array(hlats, dtype=float), transform=ccrs.PlateCarree(), c='green', edgecolor='k', label='Hail Report', alpha=0.3)
        plt.legend()
        fig.colorbar(prob, fraction=0.046, pad=0.04, orientation='horizontal', label='Percent Difference')
        ax.set_title(r'Probability difference (Subset - Full Ensemble) of {} at f{}'.format(rstrs[i], str(time)))
        plt.savefig("{}probdiff_f{}".format(figstrs[i], str(time)))
        plt.close()
    return

def plotHrlySPC(outputdir, runinit, numtimes, wrfrefpath):
    '''
    Plots hourly SPC storm reports up until the response time 
    plus 2 hours (just in case timing of forecast was off).
    
    Inputs
    ------
    outputdir ----- string specifying directory to place hourly
                        storm report output.
    runinit ------- datetime object for the model run initialization
                        time (start of SPC hourly)
    numtimes ------ integer for number of forecast hours to plot
                        (max is 24, only for plotting one day's
                        worth of SPC storm reports)
    wrfrefpath ---- string specifying file path of WRF file that
                        contains lat/lon info on inner domain
    '''
    # Slice time object
    yr, mo, day, hr, mn, sec, wday, yday, isdst = runinit.timetuple()
    if len(str(mo)) < 2: mo = '0' + str(mo)
    if len(str(day)) < 2: day = '0' + str(day)
    
    # Pull tornado and hail report csvs, only taking necessary columns
    tor = np.genfromtxt('http://www.spc.noaa.gov/climo/reports/'+
                            str(yr)[-2:]+str(mo)+str(day)+'_rpts_torn.csv',
                            delimiter=',', skip_header=1, usecols=(0,5,6), dtype=str)
    hail = np.genfromtxt('http://www.spc.noaa.gov/climo/reports/'+
                            str(yr)[-2:]+str(mo)+str(day)+'_rpts_hail.csv', 
                            delimiter=',', skip_header=1, usecols=(0,5,6), dtype=str)
    
    # Splice csv files into locs, and times
    torlats = tor[:,1]
    torlons = tor[:,2]
    tortimes = tor[:,0]
    hlats = hail[:,1]
    hlons = hail[:,2]
    hailtimes = hail[:,0]
    
    # Splice times by hour
    torhr = []
    hailhr = []
    for tortime in tortimes: torhr.append(tortime[:2])
    for hailtime in hailtimes: hailhr.append(hailtime[:2])
    torhr = np.array(torhr, dtype=int)
    hailhr = np.array(hailhr, dtype=int)
    
    # Create list of times to plot
    maxtimes = 24
    if numtimes > maxtimes: 
        numtimes = 24 # Limit number of hours to full day's worth of reports
    times = np.arange(hr, hr+numtimes) % 24
    
    # Get lat/lon data for plot extent
    wrfref = Dataset(wrfrefpath)
    clon, clat = wrfref.CEN_LON, wrfref.CEN_LAT
    tlat1, tlat2 = wrfref.TRUELAT1, wrfref.TRUELAT2
    lons, lats = wrfref.variables['XLONG'][0], wrfref.variables['XLAT'][0]
    
    # Plot
    for i in range(len(times)):
        # Format like SPC (reports run from 12Z day 1 to 1159Z day 2)
        if times[i] < 12: 
            date = runinit + timedelta(days=1, hours=int(times[i]))
        else:
            date = runinit + timedelta(hours=int(times[i]))
        yr, mo, day, hr, mn, sec, wday, yday, isdst = date.timetuple()
        # Match times with masks
        tmask = (torhr[:] == times[i])
        hmask = (hailhr[:] == times[i])
        # Plot
        fig = plt.figure(figsize=(10, 10))
        # Build projection/map
        ax = fig.add_subplot(1, 1, 1, projection=ccrs.LambertConformal(central_longitude=clon, 
                                                                       central_latitude=clat, 
                                                                       standard_parallels=(tlat1, tlat2)))
        state_borders = cfeat.NaturalEarthFeature(category='cultural',
               name='admin_1_states_provinces_lakes', scale='50m', facecolor='None') 
        ax.add_feature(state_borders, linestyle="-", edgecolor='dimgray')
        ax.add_feature(cfeat.BORDERS, edgecolor='dimgray')
        ax.add_feature(cfeat.COASTLINE, edgecolor='dimgray')
        ax.set_extent([lons[0,:].min(), lons[0,:].max(), lats[:,0].min(), lats[:,0].max()])
        # Add tor/hail pts
        if (len(torlons[tmask]) > 0):
            ax.scatter(np.array(torlons[tmask], dtype=float), np.array(torlats[tmask], dtype=float), 
                       transform=ccrs.PlateCarree(), c='red', edgecolor='k', label='Tor Report', alpha=0.7)
        if (len(hlons[hmask]) > 0):
            ax.scatter(np.array(hlons[hmask], dtype=float), np.array(hlats[hmask], dtype=float), 
                       transform=ccrs.PlateCarree(), c='green', edgecolor='k', label='Hail Report', alpha=0.7)
        plt.legend()
        # Name and save
        if len(str(mo)) < 2: mo = '0' + str(mo)
        if len(str(day)) < 2: day = '0' + str(day)
        if len(str(times[i])) < 2: timestr ='0' + str(times[i])
        else: timestr = str(times[i])
        ax.set_title(r'SPC Storm Reports valid {} UTC to {} UTC'.format(str(date+timedelta(hours=-1)), str(date)))
        plt.savefig("{}SPCreport{}{}{}_{}Z".format(outputdir, str(yr), str(mo), 
                    str(day), timestr))
        plt.close()
    return
               
    
    