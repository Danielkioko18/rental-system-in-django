from django.urls import path
from .views import DashboardView

app_name = 'rentals'

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('houses/', views.houses, name='houses'),
    #path('tenants/', views.tenants, name='tenants'),
    #path('reports/', views.reports, name='reports'),
]
