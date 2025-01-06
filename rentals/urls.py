from django.urls import path
from .views import DashboardView, HousesView, TenantsView, PaymentsView

app_name = 'rentals'

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('houses/', HousesView.as_view(), name='houses'),
    path('tenants/', TenantsView.as_view(), name='tenants'),
    path('payments/', PaymentsView.as_view(), name='payments'),
]
