from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import HouseType

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Dashboard'
        context['welcome_message'] = 'Welcome to the Dashboard!'
        return context


class HousesView(LoginRequiredMixin, TemplateView):
    template_name = 'houses.html'

    def get_context_data(self, **kwargs):
        # Add houses data to be displayed in the table
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Houses'
        context['houses'] = [
            {'number': '101', 'is_occupied': True},
            {'number': '102', 'is_occupied': False},
            {'number': '103', 'is_occupied': True},
            {'number': '104', 'is_occupied': False},
        ]
        return context


class TenantsView(LoginRequiredMixin, TemplateView):
    template_name = 'tenants.html'

    def get_context_data(self, **kwargs):
        # Add tenants data to be displayed in the table
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Tenants'
        context['tenants'] = [
            {'name': 'John Doe', 'phone': '123-456-7890', 'house_number': '101', 'date_joined': '2024-01-01'},
            {'name': 'Jane Smith', 'phone': '987-654-3210', 'house_number': '102', 'date_joined': '2024-02-15'},
            {'name': 'Alice Brown', 'phone': '555-123-4567', 'house_number': '103', 'date_joined': '2024-03-10'},
        ]
        return context


class PaymentsView(LoginRequiredMixin, TemplateView):
    template_name = 'payments.html'

    def get_context_data(self, **kwargs):
        # Sample data for demonstration purposes
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Payments'
        context['total_collected'] = 5000  # Example total collected amount
        context['pending_payments'] = 3  # Example count of pending payments
        context['overdue_payments'] = 2  # Example count of overdue payments
        
        # Sample tenants
        context['tenants'] = [
            {'id': 1, 'name': 'John Doe'},
            {'id': 2, 'name': 'Jane Smith'},
            {'id': 3, 'name': 'Alice Brown'},
        ]

        # Sample payments
        context['payments'] = [
            {
                'tenant_name': 'John Doe',
                'house_number': '101',
                'payment_date': '2025-01-01',
                'amount_paid': 1000,
                'payment_method': 'Cash',
                'overdue_amount': 0,
                'is_overdue': False,
            },
            {
                'tenant_name': 'Jane Smith',
                'house_number': '102',
                'payment_date': '2025-01-10',
                'amount_paid': 900,
                'payment_method': 'Bank Transfer',
                'overdue_amount': 100,
                'is_overdue': True,
            },
            {
                'tenant_name': 'Alice Brown',
                'house_number': '103',
                'payment_date': '2025-01-05',
                'amount_paid': 800,
                'payment_method': 'Mobile Payment',
                'overdue_amount': 200,
                'is_overdue': True,
            },
        ]

        return context


class ReportsView(LoginRequiredMixin, TemplateView):
    template_name = 'reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Reports'

        # Sample Data for Summary Cards
        context['total_rent_collected'] = 15000
        context['total_pending_payments'] = 4000
        context['total_overdue_payments'] = 2000
        context['number_of_tenants'] = 12

        # Sample Data for Detailed Payments Table
        context['detailed_payments'] = [
            {'tenant_name': 'John Doe', 'house_number': '101', 'payment_date': '2025-01-01', 
             'amount_paid': 1000, 'overdue_amount': 0, 'is_overdue': False, 'payment_method': 'Cash'},
            {'tenant_name': 'Jane Smith', 'house_number': '102', 'payment_date': '2025-01-05', 
             'amount_paid': 900, 'overdue_amount': 100, 'is_overdue': True, 'payment_method': 'Bank Transfer'},
            {'tenant_name': 'Alice Brown', 'house_number': '103', 'payment_date': '2025-01-10', 
             'amount_paid': 800, 'overdue_amount': 200, 'is_overdue': True, 'payment_method': 'Mobile Payment'},
        ]

        # Sample Data for House Occupancy Report
        context['house_occupancy'] = [
            {'house_number': '101', 'tenant_name': 'John Doe', 'is_occupied': True, 
             'date_occupied': '2024-12-01', 'date_vacated': None},
            {'house_number': '102', 'tenant_name': 'Jane Smith', 'is_occupied': True, 
             'date_occupied': '2024-11-15', 'date_vacated': None},
            {'house_number': '104', 'tenant_name': None, 'is_occupied': False, 
             'date_occupied': None, 'date_vacated': '2024-10-01'},
        ]

        return context




class SettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['house_types'] = HouseType.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        house_type_name = request.POST.get('house_type')
        monthly_rent = request.POST.get('monthly_rent')
        
        # Update or create the HouseType entry
        house_type, created = HouseType.objects.update_or_create(
            name=house_type_name,
            defaults={'monthly_rent': monthly_rent}
        )

        return redirect('rentals:settings')
