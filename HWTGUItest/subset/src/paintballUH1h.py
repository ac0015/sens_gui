#!/home/smith292/Enthought/Canopy_64bit/User/bin/python2.7

import numpy as np
import netCDF4 as nc
from datetime import datetime, timedelta
import sys
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from cartopy import crs as ccrs
from cartopy import feature as cfeat

############ COMMAND LINE ARGS ############################
datem=sys.argv[1]
hour=sys.argv[2]
thresh=int(sys.argv[3])

hour='%02d' % int(hour)
start=int(hour)-1; start='%02d' % start
#########################################################


#################   PARAMETERS   ###########################
variable="UP_HELI_MAX"
variable_units='$m^2 s^{-2}$'
title_var='Max UH' ##title_var='Max Sigma 1 Reflectivity'
title_time= str(start) + 'f-'+ str(hour) + 'f' #'21z-00z'
fig_name='paintballUH_1h_thresh' + str(thresh) + '_f' + str(hour) + '.jpeg'
#thresh=100 #threshold grid cells will be paintballed on map
numens=42
memcount = 0
base='/lustre/scratch/bancell/SE2016/2016050800/'
#############################################################


############### DATETIME PROCESSING ####################
h1=int(hour)

time1 = datetime.strptime(datem, '%Y%m%d%H')
time1 += timedelta(hours=h1)
time1=time1.strftime('%Y%m%d%H')

yyyy1=time1[0:4]; mm1=time1[4:6]; dd1=time1[6:8]; hh1=time1[8:10]

wrf1='wrfout_d02_red_'+ str(yyyy1) + '-' + str(mm1) + '-' + str(dd1) + '_' + str(hh1) + ':00:00'

a=[wrf1]
###########################################################


######## open one file to get grid dimensions ##########
### If by chance mem1 DNE, go to mem2 ###
if os.path.isfile('/lustre/research/bancell/aucolema/HWT2016runs/2016050800/wrfoutREFd2'):
    getinfo = '/lustre/research/bancell/aucolema/HWT2016runs/2016050800/wrfoutREFd2'
else:
    getinfo = base + 'mem2/' + wrf1

print('reading domain info from: ', getinfo)

ncfile = nc.Dataset(getinfo, 'r')

ny = len(ncfile.dimensions['south_north'])
nx = len(ncfile.dimensions['west_east'])
x_dim = nx 
y_dim = ny
dx = float(ncfile.DX)
dy = float(ncfile.DY)
width_meters = dx * (x_dim - 1)
height_meters = dy * (y_dim - 1)
cen_lat = float(ncfile.CEN_LAT)
cen_lon = float(ncfile.CEN_LON)
truelat1 = float(ncfile.TRUELAT1)
truelat2 = float(ncfile.TRUELAT2)
standlon = float(ncfile.STAND_LON)
x0 = ncfile.variables['XLONG'][0]
y0 = ncfile.variables['XLAT'][0]

ncfile.close()
##############################################################


max_mem_val=np.empty(numens)
paintball=np.empty((numens,ny,nx),dtype='float') #allocate numens x model grid array


for i in range(numens): ###loop through num of members
    
    print(i)
    if os.path.isfile(base + 'mem' + str(i+1) + '/' + a[-1]):
        var=np.empty((len(a),ny,nx),dtype='float')

        memcount += 1

        #### Time Loop, num of wrfouts ####
        for j in a: ###loop through num of files/times

            k=a.index(j) #loop count
            path=base+'mem'+str(i+1)+"/"+j
            print(path)

            ncfile = nc.Dataset(path, 'r')
            var[k,:,:] = ncfile.variables[variable][0,:,:] #for 3d uh var
            ncfile.close()
        ##################################

    ### Back to Each Member ###
        #Now we have our NT x NY x NX array for member i...find max values!
        max=np.max(var,0) #This is max 2d field over three times
        
        max_mem_val[i]=np.max(np.max(max,0))
        print(max_mem_val[i])    
        
        #give occurence integer of mem number
        max[max > thresh] = int(i+1) #if >= thresh, set as 1
        max[max != int(i+1)] = 0 # if not 1 (set from thresh), set as 0
        paintball[i,:,:]=max

## Done getting maxs from each member, now plot ##
## Modified 3/28/18 to use Cartopy ##
fig = plt.figure()
ax = fig.add_subplot(1, 1, 1, projection=ccrs.LambertConformal(central_longitude=cen_lon, 
                                                               central_latitude=cen_lat, 
                                                               standard_parallels=(truelat1, truelat2)))
state_borders = cfeat.NaturalEarthFeature(category='cultural',
               name='admin_1_states_provinces_lakes', scale='50m', facecolor='None') 
ax.add_feature(state_borders, linestyle="-", edgecolor='dimgray')
ax.add_feature(cfeat.BORDERS, edgecolor='dimgray')
ax.add_feature(cfeat.COASTLINE, edgecolor='dimgray')
ax.set_extent([x0[0,:].min(), x0[0,:].max(), y0[:,0].min(), y0[:,0].max()])

levs = np.linspace(0.9999999,memcount,42)
#levs = np.arange(1,memcount,1)
print(levs)
print(len(levs))

for i in range(numens):
    cf = ax.contourf(x0, y0, paintball[i,:,:], levels=levs, cmap=plt.cm.jet,
                     transform=ccrs.PlateCarree(), antialiased=True, alpha=0.5)

cbar = plt.colorbar(cf, ticks=np.arange(0.9999999,memcount,6), label='Member Number')
cbar.ax.set_yticklabels(np.arange(1,memcount,6))

plt.title(title_var+'$\ > $' + str(thresh) + variable_units + ' for '+title_time+' INIT: '+ datem)
plt.savefig("/lustre/research/bancell/aucolema/HWT2016runs/2016050800/"+fig_name, bbox_inches='tight', format='jpeg', dpi=100)
