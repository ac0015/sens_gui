from django import forms
from django.http import HttpResponse
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
    #run = forms.ChoiceField(label="Ensemble Run")
    #run.choices = runchoices

    def createSubset(self):
        submittime = datetime.datetime.utcnow()
        displaystr = "You have called the create subset function. Congrats dawg"
        if self.is_valid():
            # Create namelist for fortran sensitivity code driver
            fpath = "subsetTEST.txt"
            txt = [str(self.cleaned_data['rtime']), str(self.cleaned_data['llon']), 
                   str(self.cleaned_data['ulon']), str(self.cleaned_data['llat']), 
                   str(self.cleaned_data['ulat'])]
            np.savetxt(fpath, txt, fmt="%s", delimiter='\n')
            # Format UI as strings
            llat = "Lower Latitude: " + self.cleaned_data['llat']
            ulat = "Upper Latitude: " + self.cleaned_data['ulat']
            wlon = "Western Longitude: " + self.cleaned_data['llon']
            elon = "Eastern Longitude: " + self.cleaned_data['ulon']
            #rfunc = "Response Function: " + self.cleaned_data['rfuncs']
            rtime = "Response Function Time: " + self.cleaned_data['rtime']
            #run = "Ensemble Run: " + self.cleaned_data['run']
            # Format time submitted as string
            request_time = "Create Subset Request Submitted at: " + str(submittime)
            # Format response string
            inputstr = llat + "<br>" + ulat + "<br>" + wlon + "<br>" \
                + elon + "<br>" + rtime + "<br>" + request_time 
            response = HttpResponse(displaystr + "<br><br>Subset Attributes:<br>" + inputstr)            
        else:
            response = "Form is not valid"
            
        return response