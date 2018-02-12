from django.shortcuts import render
from django.http import HttpResponse
from .forms import SubsetForm
from django.template import loader

def index(request):
    form = SubsetForm()
    context = {'form': form}
    return render(request, 'subset.html', context)

def results(request):
    form = SubsetForm(request.POST)
    return form.createSubset()
