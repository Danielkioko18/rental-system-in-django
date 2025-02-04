from datetime import date
from django.db.models import Sum, Count
from decimal import Decimal
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import HouseType, House, Tenant, Payment
from django.db.models.functions import TruncMonth
from django.contrib import messages
from django.db import IntegrityError

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Original cards
        context['total_tenants'] = Tenant.objects.count()
        context['total_houses'] = House.objects.count()
        context['vacant_houses'] = House.objects.filter(is_occupied=False).count()
        context['pending_payments'] = Payment.objects.filter(is_overdue=True).aggregate(total=Sum('overdue_amount'))['total'] or Decimal('0.00')
        context['total_payments'] = Payment.objects.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
        context['overdue_tenants'] = Tenant.objects.filter(overdue_balance__gt=0).count()
        context['revenue_this_month'] = Payment.objects.filter(
            payment_date__year=date.today().year,
            payment_date__month=date.today().month
        ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
        context['total_credit_balance'] = Tenant.objects.aggregate(total=Sum('credit_balance'))['total'] or Decimal('0.00')
        context['paid_tenants'] = Tenant.objects.filter(overdue_balance=0).count()
        context['payments_today'] = Payment.objects.filter(payment_date=date.today()).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')


        # Data for charts
        # 1. Payment Trends
        monthly_payments = Payment.objects.annotate(month=TruncMonth('payment_date')).values('month').annotate(
            total=Sum('amount_paid')).order_by('month')
        context['payment_trends'] = {
            'months': [data['month'].strftime('%b %Y') for data in monthly_payments],
            'totals': [float(data['total']) for data in monthly_payments],
        }

        # 2. Payment Method Distribution
        payment_methods = Payment.objects.values('payment_method').annotate(
            count=Count('id')
        )
        context['payment_method_distribution'] = {
            'labels': [method['payment_method'].capitalize() for method in payment_methods],
            'values': [method['count'] for method in payment_methods],
        }

        # 3. Tenant Credit Balances
        top_credit_tenants = Tenant.objects.filter(credit_balance__gt=0).order_by('-credit_balance')[:10]
        context['tenant_credit_balances'] = {
            'names': [tenant.name for tenant in top_credit_tenants],
            'balances': [float(tenant.credit_balance) for tenant in top_credit_tenants],
        }

        # 4. Payment Status Overview
        paid_payments = Payment.objects.filter(is_overdue=False).count()
        overdue_payments = Payment.objects.filter(is_overdue=True).count()
        context['payment_status_overview'] = {
            'labels': ['Paid', 'Overdue'],
            'values': [paid_payments, overdue_payments],
        }

        return context


class HousesView(LoginRequiredMixin, TemplateView):
    template_name = 'houses.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['houses'] = House.objects.all()  # Fetch all houses
        context['house_types'] = HouseType.objects.all()  # Fetch all house types
        return context

    def post(self, request, *args, **kwargs):
        # Handle delete operation
        if 'delete_house' in request.POST:
            house_id = request.POST.get('house_id')
            if house_id:
                house = get_object_or_404(House, id=house_id)
                house.delete()
                return redirect('rentals:houses')

        # Handle add/edit operations
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
        tenants = Tenant.objects.all()
        
        for tenant in tenants:
            tenant.outstanding_balance = tenant.outstanding_balance()  # Use model method
            tenant.last_payment = tenant.last_payment()  # Use model method
        
        context['tenants'] = tenants
        context['houses'] = House.objects.filter(is_occupied=False) | House.objects.filter(tenant__isnull=False)
        return context
    
    def post(self, request, *args, **kwargs):
        if 'delete_tenant' in request.POST:
            tenant_id = request.POST.get('tenant_id')
            if tenant_id:
                tenant = get_object_or_404(Tenant, id=tenant_id)
                tenant.house.is_occupied = False
                tenant.house.save()
                tenant.delete()
                return redirect('rentals:tenants')

        tenant_id = request.POST.get('tenant_id')
        tenant_name = request.POST.get('tenant_name')
        tenant_phone = request.POST.get('tenant_phone')
        house_number = request.POST.get('house_number')

        house = get_object_or_404(House, number=house_number)

        if tenant_id:
            tenant = get_object_or_404(Tenant, id=tenant_id)
            if tenant.house != house:
                if house.is_occupied:
                    messages.error(request, f"House {house_number} is already occupied!")
                    return redirect('rentals:tenants')
                tenant.house.is_occupied = False
                tenant.house.save()
            tenant.name = tenant_name
            tenant.phone = tenant_phone
            tenant.house = house
            tenant.save()
            house.is_occupied = True
            house.save()
        else:
            if house.is_occupied:
                messages.error(request, f"House {house_number} is already occupied!")
                return redirect('rentals:tenants')
            Tenant.objects.create(name=tenant_name, phone=tenant_phone, house=house)
            house.is_occupied = True
            house.save()

        return redirect('rentals:tenants')


class PaymentsView(LoginRequiredMixin, TemplateView):
    template_name = 'payments.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenants = Tenant.objects.all()
        
        for tenant in tenants:
            tenant.outstanding_balance = tenant.outstanding_balance()  # Use model method
            tenant.last_payment = tenant.last_payment()  # Use model method
        
        context['tenants'] = tenants
        context['payments'] = Payment.objects.all()
        context['total_collected'] = Payment.objects.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
        return context

    def post(self, request, *args, **kwargs):
        if 'delete_payment' in request.POST:
            payment_id = request.POST.get('payment_id')
            if payment_id:
                payment = get_object_or_404(Payment, id=payment_id)
                payment.delete()
                return redirect('rentals:payments')

        payment_id = request.POST.get('payment_id')
        tenant_id = request.POST.get('tenant_name')
        payment_date = date.fromisoformat(request.POST.get('payment_date'))
        amount_paid = Decimal(request.POST.get('amount_paid'))
        payment_method = request.POST.get('payment_method')

        tenant = get_object_or_404(Tenant, id=tenant_id)
        
        if payment_id:
            payment = get_object_or_404(Payment, id=payment_id)
            payment.payment_date = payment_date
            payment.amount_paid = amount_paid
            payment.payment_method = payment_method
            payment.save()
        else:
            Payment.objects.create(
                tenant=tenant,
                payment_date=payment_date,
                amount_paid=amount_paid,
                payment_method=payment_method
            )
        
        return redirect('rentals:payments')


class ReportsView(LoginRequiredMixin, TemplateView):
    template_name = 'reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Filters
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        view_payment_history = self.request.GET.get('view_payment_history')

        # Fetch tenants
        tenants = Tenant.objects.all()
        context['tenants'] = tenants

        # Filter payments
        payments = Payment.objects.select_related('tenant', 'tenant__house')
        if start_date:
            payments = payments.filter(payment_date__gte=start_date)
        if end_date:
            payments = payments.filter(payment_date__lte=end_date)

        # Handle View Payment History
        if view_payment_history:
            payments = payments.filter(tenant_id=view_payment_history)
            context['viewed_tenant'] = Tenant.objects.get(id=view_payment_history)

        context['detailed_payments'] = payments

        # Financial data
        context['total_rent_collected'] = payments.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
        context['total_pending_payments'] = tenants.aggregate(total=Sum('overdue_balance'))['total'] or Decimal('0.00')
        context['overdue_payments'] = payments.filter(is_overdue=True).count()
        context['total_advance_payments'] = tenants.aggregate(total=Sum('credit_balance'))['total'] or Decimal('0.00')

        # Payment methods
        payment_methods = payments.values('payment_method').annotate(
            count=Count('id'),
            total=Sum('amount_paid')
        )
        context['payment_methods'] = {
            method['payment_method']: {
                'count': method['count'],
                'total': method['total']
            }
            for method in payment_methods
        }

        # Time-based reports
        time_based_reports = {}
        for payment in payments:
            period = payment.payment_date.strftime('%Y-%m')
            time_based_reports[period] = time_based_reports.get(period, Decimal('0.00')) + payment.amount_paid
        context['time_based_reports'] = time_based_reports

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
