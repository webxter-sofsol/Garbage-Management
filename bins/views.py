from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views import View
from django.utils.decorators import method_decorator
from .models import BinLocation


@method_decorator(login_required, name='dispatch')
class BinMapView(View):
    """Interactive map showing all bin locations."""
    
    def get(self, request):
        bin_types = BinLocation.BIN_TYPE_CHOICES
        return render(request, 'bins/map.html', {'bin_types': bin_types})


@method_decorator(login_required, name='dispatch')
class BinDetailView(View):
    """Detail view for a single bin location."""
    
    def get(self, request, bin_id):
        bin_location = get_object_or_404(BinLocation, bin_id=bin_id, is_active=True)
        return render(request, 'bins/detail.html', {'bin': bin_location})
