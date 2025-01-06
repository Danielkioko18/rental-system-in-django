from django.urls import path
from .views import DashboardView,HousesView

app_name = 'rentals'

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('houses/', HousesView.as_view(), name='houses'),
    #path('tenants/', views.tenants, name='tenants'),
    #path('reports/', views.reports, name='reports'),
]
