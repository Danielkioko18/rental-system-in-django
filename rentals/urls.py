from django.urls import path
from .views import (DashboardView, HousesView, TenantsView, PaymentsView, ReportsView, SettingsView,
                    MonthlyReportsView, CreditBalancesReportView, OverdueRentalsReportView, UserManagementView, 
                    MyProfileView, ChangePasswordView, UpdateProfileView)

app_name = 'rentals'

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('houses/', HousesView.as_view(), name='houses'),
    path('tenants/', TenantsView.as_view(), name='tenants'),
    path('payments/', PaymentsView.as_view(), name='payments'),
    path('reports/', ReportsView.as_view(), name='reports'),
    path('settings/', SettingsView.as_view(), name='settings'),
    path('users/', UserManagementView.as_view(), name='users'),
    path('reports/monthly/', MonthlyReportsView.as_view(), name='monthly-reports'),
    path('reports/credit-balances/', CreditBalancesReportView.as_view(), name='credit-balances-report'),
    path('reports/overdue/', OverdueRentalsReportView.as_view(), name='overdue-rentals-report'),
    path('profile/', MyProfileView.as_view(), name='profile'),
    path('profile/update_profile', UpdateProfileView.as_view(), name='update_profile'),
    path('profile/change_password', ChangePasswordView.as_view(), name='change_password'),
]
