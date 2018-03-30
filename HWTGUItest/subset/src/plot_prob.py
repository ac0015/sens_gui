import numpy as np
from netCDF4 import Dataset
from cartopy import crs as ccrs
from cartopy import feature as cfeat
from matplotlib import pyplot as plt
import nclcmaps
import matplotlib.patches as patches

def plot_probs(prob_array, wrfref_path, time, rbox, subset=False):
    # Get lat/lon data
    wrfref = Dataset(wrfref_path)
    clon, clat = wrfref.CEN_LON, wrfref.CEN_LAT
    tlat1, tlat2 = wrfref.TRUELAT1, wrfref.TRUELAT2
    lons, lats = wrfref.variables['XLONG'][0], wrfref.variables['XLAT'][0]
    
    # Build response box
    llon, ulon, llat, ulat = rbox
    width = ulon - llon
    height = ulat - llat    
    
    # Specific to fotran program probcalcSUBSET. Change if fortran
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
        prob = ax.contourf(lons, lats, prob_array[i], cflevels, transform=ccrs.PlateCarree(), 
                           cmap=nclcmaps.cmap('sunshine_9lev'), alpha=0.7, antialiased=True)
        fig.colorbar(prob, fraction=0.046, pad=0.04, orientation='horizontal', label='Probability (Percent)')
        ax.set_title(r'Probability of {} at f{}'.format(rstrs[i], time))
        if subset:
            plt.savefig('{}probsubset_{}'.format(figstrs[i], time))
        else:
            plt.savefig('{}probfullens_{}'.format(figstrs[i], time))
        plt.close()
        
    return
        
def plot_diff(fullensprob, subsetprob, responsedate, wrfref_path):
    '''
    Method that plots the difference in probabilities between a full
    ensemble and ensemble subset. 
    
    Inputs
    ------
    fullensprob -- output from calc_probs for full ensemble.
    subsetprob --- output from calc_probs for subset of ensemble.
    responsedate - string containing response function date in form
                     2-digit year, month, day (ex. 160508 for May 8
                     2016). Will be used to overlay SPC reports.
    '''
    # Get lat/lon data
    wrfref = Dataset("wrfoutREFd2")
    clon, clat = wrfref.CEN_LON, wrfref.CEN_LAT
    lons, lats = wrfref.variables['XLONG'][0], wrfref.variables['XLAT'][0]
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
    
    for i in range(len(fullensprob)):
        fig = plt.figure(figsize=(10, 10))
        ax = fig.add_subplot(1, 1, 1, projection=ccrs.LambertConformal(central_longitude=clon, central_latitude=clat))
        state_borders = cfeat.NaturalEarthFeature(category='cultural',
               name='admin_1_states_provinces_lakes', scale='50m', facecolor='None') 
        ax.add_feature(state_borders, linestyle="-", edgecolor='dimgray')
        ax.add_feature(cfeat.BORDERS, edgecolor='dimgray')
        ax.add_feature(cfeat.COASTLINE, edgecolor='dimgray')
        ax.set_extent([lons[0,:].min(), lons[0,:].max(), lats[:,0].min(), lats[:,0].max()])
        cflevels = np.linspace(-20., 20., 21)
        prob = ax.contourf(lons, lats, (subsetprob[i] - fullensprob[i])*100., cflevels, transform=ccrs.PlateCarree(), 
                           cmap=nclcmaps.cmap('ViBlGrWhYeOrRe'),alpha=0.7, antialiased=True)
        ax.scatter(np.array(tlons, dtype=float), np.array(tlats, dtype=float), transform=ccrs.PlateCarree(), c='red', edgecolor='k', label='Tor Report', alpha=0.3)
        ax.scatter(np.array(hlons, dtype=float), np.array(hlats, dtype=float), transform=ccrs.PlateCarree(), c='green', edgecolor='k', label='Hail Report', alpha=0.3)
        plt.legend()
        fig.colorbar(prob, fraction=0.046, pad=0.04, orientation='horizontal', label='Percent Difference')
        ax.set_title(r'Probability difference (Subset - Full Ensemble) of UH > 25 m$^2$/s$^2$ at f'+str(i))
        plt.savefig("uh25prob_diff"+str(i))
        plt.close()

def calc_probs(subset=[0], ensnum=42, numtimes=49, starthr=0, nbr=False):
    '''
    Method that calculates the probability of a response function occuring
    at the forecast hour recorded in the sensmetafile. Assumes member files
    are formatted as laid out by rename_wrfout.sh. Also assumes wrfoutREFd2
    contains lat/lon metadata in directory in which method is being called.
    
    Inputs
    ------
    subset   - optionally provide a list of member indices to plot response
                    probabilities from a subset of the full ensemble.
    ensnum   - integer specifying number of members in full ensemble
    numtimes - integer specifying number of forecast hours after starthr
                **Note** Because we're including f00 (analysis), be sure
                to use the number of (fhrs + 1) to account for the first hr
                being the analysis
    starthr  - integer specifying starting forecast hour
    nbr      - boolean, if true use 20 mi neighborhood
    
    Output
    ------
    Array containing the probabilities of a response function over a certain
    threshold.
    '''
    # Determine members used for probability calculation
    if len(subset) > 1: 
        members = subset
    else: 
        members = np.arange(1,ensnum+1)
    
    # Get lat/lon data
    wrfref = Dataset("wrfoutREFd2")
    lons, lats = wrfref.variables['XLONG'][0], wrfref.variables['XLAT'][0]
    dx, dy = wrfref.DX, wrfref.DY
    gridx = np.arange(0,len(lons[0,:]))*dx
    gridy = np.arange(0,len(lats[:,0]))*dy
    x, y = np.meshgrid(gridx, gridy)
    prob_uhmax25 = np.zeros((numtimes,len(lats[:,0]),len(lons[0,:])))
    
    if nbr:
        # Figure out how many indices around center to take for
        #   neighborhood using two random i,j points
        i, j = 180, 240
        nearest20 = np.where(np.sqrt((dx*i - x)**2 + (dy*j - y)**2) < 32186.9)
        ix = np.array(nearest20[1][:]-i, dtype=int)
        jy = np.array(nearest20[0][:]-j, dtype=int)
        print(ix, jy)
        
        plt.figure()
        plt.scatter((gridx[i+ix]-gridx[i])*0.000621371, (gridy[j+jy]-gridy[j])*0.000621371, s=100., c='blue')
        plt.scatter(0, 0, s=100., c='purple', edgecolor='k')
        plt.xlabel('mi')
        plt.ylabel('mi')
        plt.title('Test 20 mi Neighborhood')
        plt.savefig('test')
        plt.close()
        
        # Start pulling member response variables
        for k in range(len(members)):
            ind = str(members[k])
            print("Calculating probs with member: ", ind)
            for t in range(starthr, starthr+numtimes):
                filepath = "mem"+ind+"/R"+ind+"_"+str(t)+".out"
                mem = Dataset(filepath)
                uhmax = mem.variables['UP_HELI_MAX'][0]
                # Apply 20-mi neighborhood
                # 32186.9 m in 20 mi
                # Start at 20 mi-radius and end 20 mi- before boundary
                ist, ie = abs(np.min(ix)), len(lons[0,:])-np.max(ix)
                jst, je = abs(np.min(jy)), len(lats[:,0])-np.max(jy) 
                for i in range(ist, ie-1):
                    for j in range(jst, je-1):
                        if (any(uhmax[j+jy,i+ix] > 25.)):
                            prob_uhmax25[t,j,i] = prob_uhmax25[t,j,i] + 1.
                
    else:
        for k in range(len(members)):
            ind = str(members[k])
            print("Calculating probs with member: ", ind)
            for t in range(starthr, starthr+numtimes):
                filepath = "mem"+ind+"/R"+ind+"_"+str(t)+".out"
                mem = Dataset(filepath)
                uhmax = mem.variables['UP_HELI_MAX'][0]
                uh25 = uhmax>25.
                prob_uhmax25[t,uh25] = prob_uhmax25[t,uh25] + 1.
    prob_uhmax25 = prob_uhmax25/len(members)
    print("Max Prob: ", np.max(prob_uhmax25))
    return prob_uhmax25