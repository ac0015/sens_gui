#################################################
# esens_subsetting.py
#
# Contains methods to subset an ensemble

import numpy as np
from netCDF4 import Dataset
    
def point(matrix):
    '''
    Builds a mask that is true for a matrix everywhere 
    except the highest value point in the matrix.
    '''
    point = np.where(matrix == np.max(matrix))
    mask = (matrix != matrix[point])
    return mask

def percent(matrix, percent):
    '''
    Builds a mask that is true for the lowest 
    n percent of values in a matrix.
    '''
    mask = (matrix < percent*matrix)
    return mask 

def ensSubset(wrfsensfile, analysis, memvalsfile, fullensnum, newensnum, method=3):
    '''
    Uses the WRF sensitivity and interpolated analysis file as well as the
    sensitivity variable values for each member to determine the optimal
    ensemble subset given desired subset size and subsetting method.
    
    Inputs
    ------
    wrfsensfile --- String containing path to sensitivity NC file. Assumes
                    sensitivity data is stored in 'P_HYD' as dictated by
                    esensSPC.f.
    analysis ------ String containing path to interpolated analysis file.
    memvalsfile --- String containing path to output of sensvector.f that
                    stores sensitivity variable values for each member.
    fullensnum ---- Integer describing the number of members in the full
                    ensemble.
    newensnum ----- Integer describing subset size.
    method -------- Integer from 1-3 to choose subsetting technique.
                    (1) Automatically chooses the single highest sensitivity
                        grid point and subsets based on the lowest errors
                        at this grid point.
                    (2) Weights all sensitivity variable fields by the 
                        sensitivity field and subsets based on lowest
                        total error.
                    (3) Takes the top n% (optimal number tbd) of the
                        sensitivity field and only calculates and sums
                        errors at these grid points, subsetting on
                        lowest total error.
    Outputs
    -------
    Returns an integer list of subset ensemble members as well as a 
    list of the names of sensitivity variables used.
    '''
    # Define varkeys for analysis and sensinds for WRF - hardcode for testing
    varkeys = ['500_hPa_GPH']
    sensinds = [1]
    
    # Pull sensitivity field with dimensions (sensitivity variable index, ydim, xdim)
    wrfsens = Dataset(wrfsensfile)
    smat = wrfsens.variables['P_HYD']    
    lons, lats = wrfsens.variables['XLONG'][0], wrfsens.variables['XLAT'][0]  
    sensmat = smat[0,sensinds[:],:,:]
    
    try:
        if method == 1:
            # Mask by point
            mask = point(sensmat)
        elif method == 2:
            # Don't mask anything (will weight field by sensitivity)
            mask = False
        elif method == 3:
            # Mask by percentage of field
            mask = percent(sensmat, 0.7)
        else:  
            raise NameError("Invalid method choice: {}".format(str(method)))
    except:
        dflt = 3
        print("Setting subsetting technique to {}".format(str(dflt)))
        mask = percent(sensmat, 0.7)
        
    # Mask of underground and missing data
    missing = (sensmat >= 9e9)
    
    # Build total mask
    tmask = (mask | missing)
    
    # Pull analysis
    anl = Dataset(analysis)
    anlvar = np.zeros((len(varkeys), len(lats[:,0]), len(lons[0,:])))
    for i in range(len(varkeys)):
        anlvar[i,:,:] = anl.variables[varkeys[i]][:,:]
    sensstrings = [varkey.replace("_"," ") for varkey in varkeys]
    
    # Clobber varkeys for sensitivity variable values
    varkeys = ['GPH_500']
    
    # Pull sensitivity variable values from each member
    memvals = Dataset(memvalsfile)
    memvar = np.zeros((len(varkeys), fullensnum, len(lats[:,0]), len(lons[0,:])))
    for i in range(len(varkeys)):
        memvar[i,:,:] = memvals.variables[varkeys[i]][:,:]
    
    # Start calculating differences between obs and members
    error = np.zeros((len(varkeys), fullensnum, len(lats[:,0]), len(lons[0,:])))
    # Apply percent sensfield and missing masks to analysis
    anlvar_masked = np.ma.masked_array(anlvar, mask=tmask)
    #print("RAP value(s): ", anlvar_masked[tmask==False])
    for k in range(len(varkeys)):
        for i in range(fullensnum):
            # Apply percent sensfield and missing masks to member
            mem_masked = np.ma.masked_array(memvar[k,i], mask=tmask[k])
            #print("Member "+str(i+1)+": ", mem_masked[tmask[k]==False])
            error[k,i,:,:] = (mem_masked[:,:]-anlvar_masked[:,:])/anlvar_masked[:,:]
            # Restructure for later mask
            error[k,i][tmask[k]] = 9e9
    # Mask all error data that was masked from member fields
    error_masked = np.ma.masked_array(error, mask=(error == 9e9))
    print("Min error: ", np.min(error_masked))
    print("Max error: ", np.max(error_masked))
    
    # Sum total error and choose members with least error for subset
    summed_error = np.zeros((fullensnum))
    if method == 2:
        error_masked = error_masked * sensmat
    for i in range(fullensnum): summed_error[i] = np.sum(abs(error_masked[:,i,:,:]))
    sorted_inds = summed_error.argsort()
    subset_mems = sorted_inds[:newensnum]+1 # Add one to correct zero-based
    
    return subset_mems, sensstrings

