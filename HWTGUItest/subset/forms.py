from django import forms
from django.http import HttpResponse
from threading import Condition
import datetime
import os
import numpy as np

class SubsetForm(forms.Form):
    max1hruh = 'Max 1h UH'
    max6hruh = 'Max 6h UH'
    maxrefl = 'Max Refl'
    maxwindspd ='Max Wind Spd'
    coverage1hruh = '1h UH Cov'
    coverage6hruh = '6h UH Cov'
    coveragerefl = 'Refl Cov'
    coveragewindspd = 'Wind Spd Cov'
    pcp = 'Accum PCP'
    avgrefl = 'Avg Refl'
    avguh = 'Avg 1h UH'
    avgwspd = 'Avg Wind Spd'
    
    now = datetime.datetime.utcnow()
    if (now.hour < 12):
        hr = 0
        day = -1
    else:
        hr = 12
        day = 0
    run = now + datetime.timedelta(days=day)
    newest = datetime.datetime(run.year, run.month,
                               run.day, hr)
    old = newest - datetime.timedelta(hours=12)
    oldest = old - datetime.timedelta(hours=12)
    
    rchoices = (
        (max1hruh, 'Maximum 1h Updraft Helicity'),
        (max6hruh, 'Maximum 6h Updraft Helicity'),
        (maxrefl, 'Maximum Reflectivity'),
        (maxwindspd, 'Maximum Wind Speed'),
        (coverage1hruh, '1h Updraft Helicity Coverage'),
        (coverage6hruh, '6h Updraft Helicity Coverage'),
        (coveragerefl, 'Reflectivity Coverage'),
        (coveragewindspd, 'Wind Speed Coverage'),
        (pcp, 'Accumulated Precipitation'),
        (avgrefl, 'Average Reflectivity'),
        (avguh, 'Average 1h Updraft Helicity'),
        (avgwspd, 'Average Wind Speed'),
    )
    
    runchoices = (
        (newest, str(newest)),
        (old, str(old)),
        (oldest, str(oldest)),
    )
    
    llat = forms.CharField(widget = forms.TextInput(attrs = {'id':'llat'}), 
                           required=True, initial=37.78, label="Lower Latitude")
    ulat = forms.CharField(widget = forms.TextInput(attrs = {'id':'ulat'}), 
                           required=True, initial=42.16, label="Upper Latitude")
    llon = forms.CharField(widget = forms.TextInput(attrs = {'id':'llon'}), 
                           required=True, initial=-99.14, label="Lower Longitude")
    ulon = forms.CharField(widget = forms.TextInput(attrs = {'id':'ulon'}), 
                           required=True, initial=-93.29, label="Upper Longitude")
    #rfuncs = forms.ChoiceField(label="Response Function")
    #rfuncs.choices = rchoices
    rtime = forms.CharField(initial=18, label="Response Time")
    runchoice = forms.ChoiceField(label="Ensemble Run")
    runchoice.choices = runchoices

    def createSubset(self):
        submittime = datetime.datetime.utcnow()
        if self.is_valid():
            # Create input file for fortran sensitivity code driver
            fpath = "subsetTEST.txt"
            txt = [str(self.cleaned_data['rtime']), str(self.cleaned_data['llon']), 
                   str(self.cleaned_data['ulon']), str(self.cleaned_data['llat']), 
                   str(self.cleaned_data['ulat'])]
            np.savetxt(fpath, txt, fmt="%s", delimiter='\n')
            
            # Add run date to subset date archive
            self.addRunDate()
            
            # Wait for plots
            cv = Condition()
            with cv:
                while not os.path.exists("test.png"):
                    cv.wait(timeout=2)
                    
            # Return time of createSubset request
            response = HttpResponse(submittime)    
        else:
            response = "Form is not valid"
            
        return response    
            
    def addRunDate(self):
        '''
        If createSubset() is called, add run initialization to text file containing
        list of all valid subsets.
        '''
        date = self.cleaned_data['runchoice']
        # Store dates in form YYMMDDHH
        datestr = str(date[:4] + '' + date[5:7] + '' + date[8:10] + '' + date[11:13])
        if os.path.exists('dates.txt'):
            f = open('dates.txt', 'a')
            datestr = "," + datestr
        else:
            f = open('dates.txt', 'w')   
        f.write(datestr)
        f.close()
        return
