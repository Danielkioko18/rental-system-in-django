from datetime import date, timedelta
from django.db.models import Sum
from decimal import Decimal
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import HouseType, House, Tenant, Payment

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
        context = super().get_context_data(**kwargs)
        context['houses'] = House.objects.all()  # Fetch all houses
        context['house_types'] = HouseType.objects.all()  # Fetch all house types
        return context

    def post(self, request, *args, **kwargs):
        house_id = request.POST.get('house_id')
        house_number = request.POST.get('house_number')
        house_type_name = request.POST.get('house_type')
        monthly_rent = request.POST.get('monthly_rent')

        if house_id:  # Edit operation
            house = get_object_or_404(House, id=house_id)
            house.number = house_number
            house.house_type = house_type_name
            house.monthly_rent = monthly_rent
            house.save()
        else:  # Add operation
            House.objects.create(
                number=house_number,
                house_type=house_type_name,
                monthly_rent=monthly_rent,
                is_occupied=False,
            )

        return redirect('rentals:houses')


class TenantsView(LoginRequiredMixin, TemplateView):
    template_name = 'tenants.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Tenants'
        context['tenants'] = Tenant.objects.all()
        context['houses'] = House.objects.filter(is_occupied=False) | House.objects.filter(
            tenant__isnull=False)  # Include occupied houses with tenants
        return context

    def post(self, request, *args, **kwargs):
        tenant_id = request.POST.get('tenant_id')
        tenant_name = request.POST.get('tenant_name')
        tenant_phone = request.POST.get('tenant_phone')
        house_number = request.POST.get('house_number')

        house = House.objects.get(number=house_number)

        if tenant_id:  # Edit operation
            tenant = Tenant.objects.get(id=tenant_id)
            # Free the previously occupied house
            if tenant.house != house:
                tenant.house.is_occupied = False
                tenant.house.save()
            tenant.name = tenant_name
            tenant.phone = tenant_phone
            tenant.house = house
            tenant.save()

        else:  # Add operation
            Tenant.objects.create(
                name=tenant_name,
                phone=tenant_phone,
                house=house,
            )
        house.is_occupied = True
        house.save()

        return redirect('rentals:tenants')

    def delete(self, request, *args, **kwargs):
        tenant_id = request.POST.get('tenant_id')
        tenant = Tenant.objects.get(id=tenant_id)
        tenant.house.is_occupied = False
        tenant.house.save()
        tenant.delete()
        return redirect('rentals:tenants')


class PaymentsView(LoginRequiredMixin, TemplateView):
    template_name = 'payments.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Fetch tenants and initialize overdue and credit balances
        tenants = Tenant.objects.all()
        for tenant in tenants:
            tenant.overdue_balance = tenant.overdue_balance or Decimal('0.00')
            tenant.credit_balance = tenant.credit_balance or Decimal('0.00')
        context['tenants'] = tenants
        
        # Fetch payments
        payments = Payment.objects.select_related('tenant', 'tenant__house').all()
        context['payments'] = payments

        # Calculate totals for summary cards
        context['total_collected'] = payments.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
        context['pending_payments'] = tenants.aggregate(total=Sum('overdue_balance'))['total'] or Decimal('0.00')
        context['overdue_payments'] = payments.filter(is_overdue=True).count()
        context['total_credit'] = tenants.aggregate(total=Sum('credit_balance'))['total'] or Decimal('0.00')

        return context

    def post(self, request, *args, **kwargs):
        tenant_id = request.POST.get('tenant_name')
        payment_date = date.fromisoformat(request.POST.get('payment_date'))
        amount_paid = Decimal(request.POST.get('amount_paid'))
        payment_method = request.POST.get('payment_method')

        tenant = Tenant.objects.get(id=tenant_id)
        house = tenant.house
        monthly_rent = house.monthly_rent

        # Calculate total due
        total_due = tenant.overdue_balance + monthly_rent - tenant.credit_balance

        # Apply payment
        if amount_paid >= total_due:
            # Overpayment case
            tenant.credit_balance = amount_paid - total_due
            tenant.overdue_balance = Decimal('0.00')
            is_overdue = False
            overdue_amount = Decimal('0.00')
        else:
            # Partial payment or payment without overpayment
            remaining_due = total_due - amount_paid
            if payment_date > date.today().replace(day=5):
                # Payment is late
                tenant.overdue_balance = remaining_due
                tenant.credit_balance = Decimal('0.00')  # No overpayment
                is_overdue = True
                overdue_amount = remaining_due
            else:
                # Payment is on time but insufficient
                tenant.overdue_balance = remaining_due
                tenant.credit_balance = Decimal('0.00')  # No overpayment
                is_overdue = remaining_due > 0
                overdue_amount = remaining_due

        # Save the tenant's updated balances
        tenant.save()

        # Create the payment record
        Payment.objects.create(
            tenant=tenant,
            payment_date=payment_date,
            amount_paid=amount_paid,
            payment_method=payment_method,
            is_overdue=is_overdue,
            overdue_amount=overdue_amount
        )

        return redirect('rentals:payments')



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
