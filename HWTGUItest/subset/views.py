from django.shortcuts import render
from django.http import HttpResponse
from .forms import SubsetForm
import numpy as np
import os
from django.views.decorators.cache import never_cache

@never_cache
def index(request):
    form = SubsetForm()
    context = {'form': form}
    return render(request, 'subset.html', context)

@never_cache
def results(request):
    form = SubsetForm(request.POST)
    return render(request, 'results.html', {'response': form.createSubset(), 'form': form})

@never_cache
def evaluate(request):
    try:
        lastten = np.genfromtxt('/home/aucolema/sens_gui/dates.txt', delimiter='\n', dtype=str)[-1:-34:-1]
    except IOError:
        print("dates.txt does not exist.")
        lastten = []
    except IndexError:
        print("Insufficient number of values in dates.txt. Using last val")
        lastval = np.genfromtxt('/home/aucolema/sens_gui/dates.txt', delimiter='\n', dtype=str)
        lastten = [lastval]
    except Exception as e:
        raise(e)
    return render(request, 'eval.html', {'lastten': lastten})
