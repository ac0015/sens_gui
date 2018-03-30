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

hour='%02d' % int(hour)
start=int(hour)-6; start='%02d' % start
#########################################################


#################   PARAMETERS   ###########################
variable='REFL_10CM'
variable_units='dBZ'
title_var='Reflectivity' ##title_var='Max Sigma 1 Reflectivity'
title_time= str(start) + 'f-'+ str(hour) + 'f' #'18z-00z'
fig_name='paintballDBZ_6h_f' + hour  + '.jpeg'
thresh=40 #threshold grid cells will be paintballed on map
numens=42
memcount = 0
base='/lustre/scratch/bancell/SE2016/2016050800/'
#############################################################


######## DATETIME PROCESSING ###############
h1=int(hour)-5; h2=int(hour)-4 ; h3=int(hour)-3; h4=int(hour)-2; 
h5=int(hour)-1; h6=int(hour);

time1 = datetime.strptime(datem, '%Y%m%d%H')
time1 += timedelta(hours=h1)
time1=time1.strftime('%Y%m%d%H')

time2 = datetime.strptime(datem, '%Y%m%d%H')
time2 += timedelta(hours=h2)
time2=time2.strftime('%Y%m%d%H')

time3 = datetime.strptime(datem, '%Y%m%d%H')
time3 += timedelta(hours=h3)
time3=time3.strftime('%Y%m%d%H')

time4 = datetime.strptime(datem, '%Y%m%d%H')
time4 += timedelta(hours=h4)
time4=time4.strftime('%Y%m%d%H')

time5 = datetime.strptime(datem, '%Y%m%d%H')
time5 += timedelta(hours=h5)
time5=time5.strftime('%Y%m%d%H')

time6 = datetime.strptime(datem, '%Y%m%d%H')
time6 += timedelta(hours=h6)
time6=time6.strftime('%Y%m%d%H')

yyyy1=time1[0:4]; mm1=time1[4:6]; dd1=time1[6:8]; hh1=time1[8:10]
yyyy2=time2[0:4]; mm2=time2[4:6]; dd2=time2[6:8]; hh2=time2[8:10]
yyyy3=time3[0:4]; mm3=time3[4:6]; dd3=time3[6:8]; hh3=time3[8:10]
yyyy4=time4[0:4]; mm4=time4[4:6]; dd4=time4[6:8]; hh4=time4[8:10]
yyyy5=time5[0:4]; mm5=time5[4:6]; dd5=time5[6:8]; hh5=time5[8:10]
yyyy6=time6[0:4]; mm6=time6[4:6]; dd6=time6[6:8]; hh6=time6[8:10]

wrf1='wrfout_d02_red_'+ str(yyyy1) + '-' + str(mm1) + '-' + str(dd1) + '_' + str(hh1) + ':00:00'
wrf2='wrfout_d02_red_'+ str(yyyy2) + '-' + str(mm2) + '-' + str(dd2) + '_' + str(hh2) + ':00:00'
wrf3='wrfout_d02_red_'+ str(yyyy3) + '-' + str(mm3) + '-' + str(dd3) + '_' + str(hh3) + ':00:00'
wrf4='wrfout_d02_red_'+ str(yyyy4) + '-' + str(mm4) + '-' + str(dd4) + '_' + str(hh4) + ':00:00'
wrf5='wrfout_d02_red_'+ str(yyyy5) + '-' + str(mm5) + '-' + str(dd5) + '_' + str(hh5) + ':00:00'
wrf6='wrfout_d02_red_'+ str(yyyy6) + '-' + str(mm6) + '-' + str(dd6) + '_' + str(hh6) + ':00:00'

a=[wrf1,wrf2,wrf3,wrf4,wrf5,wrf6]
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
            var[k,:,:] = ncfile.variables[variable][0,0,:,:] #for 4d refl var
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
