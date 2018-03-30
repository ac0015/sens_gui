#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb  8 10:11:46 2018

@author: aucolema
"""
import numpy as np
import os
from datetime import timedelta
from sens import Sens
from esens_subsetting import ensSubset
from interp_analysis import fromDatetime, interpRAPtoWRF, subprocess_cmd
from plot_prob import plot_probs
import realtime_plotting
from netCDF4 import Dataset
    
#################
# Subset class
#################
class Subset:
    '''
    The Subset class encapsulates all the information pertaining
    to a forecast ensemble and its subset which is gathered from
    relevant sensitivity variables and response functions and their
    respective sensitivity fields.
    '''
    
    def __init__(self, sens=Sens(), subset_size=21, subset_method='percent',
                 percent=0.7, sensvalfile="SENSvals.nc"):
        '''
        Constructor for an instance of the Subset class
        '''
        self._sens = sens
        self._fullens = np.arange(1,sens.getEnsnum()+1,1)
        self._subsize = subset_size
        self._methodchoices = {'point' : 1, 'weight' : 2, 'percent' : 3}
        
        try:
            self._method = self._methodchoices[subset_method]
        except:
            dflt_opt = list(self._methodchoices.keys())[-1]
            print("{} not an acceptable choice from {}. Using {} method.".format(str(subset_method),
                  self._methodchoices.keys(), dflt_opt))
            self._method = self._methodchoices[dflt_opt]
        self._subset = []
        
        # Define analysis file path
        self._sensdate = sens.getRunInit() + timedelta(hours=sens.getSensTime())
        yr, mo, day, hr = fromDatetime(self._sensdate, interp=True)
        self._analysis = "{}RAP_interp_to_WRF_{}{}{}{}.nc".format(sens.getDir(),
                          yr, mo, day, hr)
        self._sensvalfile = sens.getDir() + sensvalfile
        
        # Set to True if calcProbs was last run for a subset.
        self._calcprobs_subset = False
        
    def __str__(self):
        return "Subset object with full ensemble of {} members, subset size \
        of {}, and using the {} subsetting method. Based on Sens object: \
        \n {}".format(self._sens.getEnsnum(), self._subsize,
        self._method, str(self._sens))
        
    def setSubsetMethod(self, subset_method):
        '''
        Set the ensemble subsetting method
        '''
        self._method = self._methodchoices[subset_method]
        return
    
    def setAnalysis(self, analysispath):
        '''
        Set the absolute path of the interpolated analysis file
        to be used for verification.
        '''
        self._analysis = analysispath
          
    def getAnalysis(self):
        '''
        Returns path to analysis file at senstime.
        '''
        return self._analysis
    
    def getSubMembers(self):
        '''
        Returns a list of the members in the subset.
        '''
        return self._subset
    
    def interpRAP(self):
        '''
        If using RAP analysis, must call this function to interpolate
        the analysis to our WRF grid before doing any subsetting. Returns
        NULL but will produce outfile with filepath as described by 
        the analysis attribute of the Subset instance.
        '''
        os.chdir(self._sens.getDir())
        yr, mo, day, hr = fromDatetime(self._sensdate, interp=True)
        interpRAPtoWRF(yr, mo, day, hr, self._sens.getRefFileD1()) 
    
    def calcSubset(self):
        '''
        Calls the ensSubset() function from esens_subsetting.py. 
        '''
        S = self._sens
        if (os.path.isfile(self._analysis) == False):
            print("{} does not exist. Running RAP interpolation.".format(self._analysis))
            self.interpRAP()
        if (os.path.isfile(S.getWRFSensFile()) == False):
            print("{} does not exist. Running sensitivity module with Sens obj.".format(S.getOutfile()))
            S.runSENS()
        if (os.path.isfile(self._sensvalfile) == False):
            print("{} does not exist. Running store sens vals with Sens obj.".format(self._sensvalfile))
            S.storeSENSvals()
        self._subset, sensstrings = ensSubset(S.getWRFSensFile(), self._analysis, 
                                              self._sensvalfile, S.getEnsnum(),
                                              self._subsize)
        return
    
    def calcProbs(self, members):
        '''
        Runs the fortran executable calcprobSUBSET to calculate
        probabilities for any number of ensemble members. Takes
        an input file with ensemble number
        '''
        S = self._sens
        
        # Create or navigate into probs directory
        probdir = S.getDir() + "probs/"
        direxists = os.path.exists(probdir)
        if (direxists == False):
            os.mkdir(probdir)
        os.chdir(probdir)
        if len(members) == len(self._fullens): 
            fname = "fullens_probs.in"
            self._calcprobs_subset = False
        else: 
            fname = "subset_probs.in"
            self._calcprobs_subset = True
            
        # Copy members into directory
        for i in range(len(members)):
            os.popen('cp ../mem{}/R{}_{}.out .'.format(members[i], 
                     members[i], S.getRTime()))

        # Format input file
        os.popen('echo {} > {}'.format(len(members), fname))
        os.popen('echo {} >> {}'.format(S.getRTime(),fname))
        
        # Run renaming script
        arg = "/lustre/work/aucolema/scripts/rename_probs.sh <{}".format(fname)
        subprocess_cmd(arg)
        
        # Initialize SUBSETwrfout.prob
        os.popen("cp {} {}".format(S.getRefFileD2(), "SUBSETwrfout.prob"))
        
        # Run fortran executable
        # TO-DO: figure out why this throws a 'not netCDF error'
        args = "module load intel; /lustre/work/aucolema/enkfDART/src/probcalcSUBSETnew <{} >probs.out".format(fname)
        subprocess_cmd(args)
        return
    
    def plotProbs(self, use_subset=False):
        '''
        Calls probability plotting method from plot_prob library. If using
        a probability netCDF that 
        '''
        S = self._sens
        probdir = S.getDir() + "probs/"
        
        # Pull dataset (output from calcProbs). Probs stored in 
        #  P_HYD variable as dictated by fortran program
        #  calcprobsSUBSET.f.
        try:
            os.chdir(probdir)
        except OSError:
            print("{} doesn't exist. Running calcProbs() with full ens".format(probdir))
            self.calcProbs(self._fullens)
            os.chdir(probdir)
        except:
            raise
            
        prob_dataset = Dataset("SUBSETwrfout.prob")
        probs = prob_dataset.variables['P_HYD'][0]
        plot_probs(probs, S.getRefFileD2(), S.getRTime(), S.getRbox(),
                   subset=use_subset)
        return
    
    def realtimePlotProbs(self, use_subset):
        '''
        Calls plotProbs from realtime_plotting library. Passes
        mainly file paths and some metadata and function will
        handle the rest.
        '''
        S = self._sens
        direc = S.getDir()
        fullenspath = direc + "FULLENSwrfout.prob"
        subsetpath = direc + "SUBSETwrfout.prob"
        wrfrefpath = S.getRefFileD2()
        
        if use_subset:
            realtime_plotting.plotProbs(subsetpath, wrfrefpath, S.getRTime(),
                               S.getRbox(), use_subset)
        else:
            realtime_plotting.plotProbs(fullenspath, wrfrefpath, S.getRTime(),
                               S.getRbox(), use_subset)
        return
            
    def realtimePlotDiffs(self, verif_day=False):
        '''
        Calculates and plots delta probabilities between the full ensemble and
        its corresponding subset. Calls plotDiff from realtime_plotting library. 
        Passes only file paths and outside function will handle the rest. If
        verifi_day is set to True, will overlay storm reports onto
        difference plot.
        '''
        S = self._sens
        direc = S.getDir()
        fullenspath = direc + "FULLENSwrfout.prob"
        subsetpath = direc + "SUBSETwrfout.prob"
        wrfrefpath = S.getRefFileD2()
        
        # Format date for storm reports
        date = S.getRunInit()
        SPCdate = str(date)[2:10].replace('-','')
        
        realtime_plotting.plotDiff(fullenspath, subsetpath, wrfrefpath,
                                   S.getRbox(), S.getRTime(), SPCdate,
                                   stormreports=verif_day)
        
        
                                              
        
        
        
        
        
        
        
        