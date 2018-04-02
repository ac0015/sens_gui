from django.shortcuts import render
from django.http import HttpResponse
from .forms import SubsetForm
import numpy as np
import os

def index(request):
    form = SubsetForm()
    context = {'form': form}
    return render(request, 'subset.html', context)

def results(request):
    form = SubsetForm(request.POST)
    return render(request, 'results.html', {'response': form.createSubset(), 'form': form})

def evaluate(request):
    lastten = np.genfromtxt('dates.txt', delimiter=',', dtype=str)[-1:-10:-1]
    basedir = '.'
    #for date in lastten:
    #    #if os.path.exists(basedir + date):
    #        # keep date in list #
    return render(request, 'eval.html', {'lastten': lastten})
