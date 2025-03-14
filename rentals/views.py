from datetime import date
from django.utils.dateparse import parse_date
from django.db.models import Sum, Count
from decimal import Decimal
from django.shortcuts import redirect, get_object_or_404, render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import HouseType, House, Tenant, Payment
from django.db.models.functions import TruncMonth
from django.template.loader import render_to_string
from django.contrib import messages
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from django.db import IntegrityError
from django.views.generic import ListView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.views.generic import UpdateView
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .forms import ProfileUpdateForm
from django.contrib.auth.models import User


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Original cards
        context['total_tenants'] = Tenant.objects.count()
        context['total_houses'] = House.objects.count()
        context['vacant_houses'] = House.objects.filter(is_occupied=False).count()
        context['pending_payments'] = sum(tenant.outstanding_balance() for tenant in Tenant.objects.all() if tenant.outstanding_balance() > 0)
        context['total_payments'] = Payment.objects.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
        context['overdue_tenants'] = sum(1 for tenant in Tenant.objects.all() if tenant.outstanding_balance() > 0)
        context['revenue_this_month'] = Payment.objects.filter(payment_date__year=date.today().year, payment_date__month=date.today().month).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
        context['total_credit_balance'] = CreditBalancesReportView.get_total_credit_balance()[0]
        context['payments_today'] = Payment.objects.filter(payment_date=date.today()).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')

        # Data for charts
        # 1. Payment Trends
        monthly_payments = Payment.objects.annotate(month=TruncMonth('payment_date')).values('month').annotate(total=Sum('amount_paid')).order_by('month')
        context['payment_trends'] = {
            'months': [data['month'].strftime('%b %Y') for data in monthly_payments],
            'totals': [float(data['total']) for data in monthly_payments],
        }

        # 2. Payment Method Distribution
        payment_methods = Payment.objects.values('payment_method').annotate(count=Count('id'))
        context['payment_method_distribution'] = {
            'labels': [method['payment_method'].capitalize() for method in payment_methods],
            'values': [method['count'] for method in payment_methods],
        }

        # 3. Tenant Credit Balances
        _, tenants_with_credit = CreditBalancesReportView.get_total_credit_balance()
        top_credit_tenants = sorted(tenants_with_credit, key=lambda x: x['credit_balance'], reverse=True)[:10]
        context['tenant_credit_balances'] = {
            'names': [tenant['name'] for tenant in top_credit_tenants],
            'balances': [float(tenant['credit_balance']) for tenant in top_credit_tenants],
        }

         # 4. Payment Status Overview (Corrected)
        tenants = Tenant.objects.all()
        outstanding_balance_count = sum(1 for tenant in tenants if tenant.outstanding_balance() > 0)
        no_outstanding_balance_count = len(tenants) - outstanding_balance_count

        context['payment_status_overview'] = {
            'labels': ['Outstanding Balance', 'No Outstanding Balance'],
            'values': [outstanding_balance_count, no_outstanding_balance_count],
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
        context['total_tenants']=Tenant.objects.all().count()
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
        return context


class MonthlyReportsView(LoginRequiredMixin, TemplateView):
    template_name = 'monthly-reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get the month and year parameters from the GET request
        month = self.request.GET.get('month')
        year = self.request.GET.get('year')

        # If no month or year is provided, default to current month and year
        if not month or not year:
            month = str(date.today().month).zfill(2)
            year = str(date.today().year)

        # Construct the date range for the selected month and year
        start_date = f"{year}-{month}-01"
        end_date = f"{year}-{month}-{date(year=int(year), month=int(month), day=1).replace(day=28).strftime('%d')}"

        # Filter payments within the range of the selected month and year
        payments = Payment.objects.filter(payment_date__gte=start_date, payment_date__lte=end_date)

        # Calculate the total payments for the month
        total_collected = payments.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')

        context['payments'] = payments
        context['total_collected'] = total_collected
        context['month'] = month
        context['year'] = year

        return context

    def get(self, request, *args, **kwargs):
        # If the 'generate_pdf' GET parameter is provided, generate the PDF
        if 'generate_pdf' in request.GET:
            return self.generate_pdf_report(request)
        return super().get(request, *args, **kwargs)

    def generate_pdf_report(self, request):
        # Get the month and year parameters from the GET request
        month = request.GET.get('month')
        year = request.GET.get('year')

        # Construct the date range for the selected month and year
        start_date = f"{year}-{month}-01"
        end_date = f"{year}-{month}-{date(year=int(year), month=int(month), day=1).replace(day=28).strftime('%d')}"

        # Filter payments within the range of the selected month and year
        payments = Payment.objects.filter(payment_date__gte=start_date, payment_date__lte=end_date)

        # Calculate the total payments for the month
        total_collected = payments.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')

        # Render the template to HTML for PDF generation
        html_string = render_to_string('monthly-reports.html', {
            'payments': payments,
            'month': month,
            'year': year,
            'total_collected': total_collected,
        })

        # Create the HTTP response with PDF content type
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="monthly_payment_report_{month}_{year}.pdf"'

        # Create the PDF using ReportLab
        p = canvas.Canvas(response, pagesize=letter)

        # Add Title
        p.setFont("Helvetica-Bold", 16)
        p.drawString(200, 750, f"Monthly Payment Report for {month}/{year}")

        # Total Collected Amount
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, 730, f"Total Collected: ${total_collected}")

        # Table Header
        p.setFont("Helvetica-Bold", 10)
        p.drawString(50, 700, "#")
        p.drawString(100, 700, "Tenant Name")
        p.drawString(200, 700, "House No.")
        p.drawString(300, 700, "Payment Date")
        p.drawString(400, 700, "Amount Paid")
        p.drawString(500, 700, "Payment Method")

        # Table Rows
        y_position = 680
        p.setFont("Helvetica", 10)

        serial_number = 1  # Start serial No
        for payment in payments:
            p.drawString(50, y_position, str(serial_number))
            p.drawString(100, y_position, payment.tenant.name)
            p.drawString(200, y_position, payment.tenant.house.number)
            p.drawString(300, y_position, str(payment.payment_date))
            p.drawString(400, y_position, f"${payment.amount_paid}")
            p.drawString(500, y_position, payment.payment_method)
            y_position -= 20
                   
            # Increment serial number for each row
            serial_number += 1


            # Avoid overflow of table rows
            if y_position < 40: 
                p.showPage()  # Create a new page
                y_position = 750  # Reset y_position for the new page

        # Save the PDF
        p.showPage()
        p.save()

        return response


class CreditBalancesReportView(LoginRequiredMixin, TemplateView):
    template_name = 'credit-balances-report.html'

    @classmethod
    def get_total_credit_balance(cls):
        total_credit_balance = Decimal('0.00')
        tenants_with_credit = []  # List to store tenants with credit balances

        for tenant in Tenant.objects.all():
            total_paid = Payment.objects.filter(tenant=tenant).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
            months_since_joining = (date.today().year - tenant.date_joined.year) * 12 + date.today().month - tenant.date_joined.month
            total_due = months_since_joining * tenant.house.monthly_rent
            credit_balance = total_paid - total_due

            if credit_balance > 0:
                total_credit_balance += credit_balance
                tenants_with_credit.append({
                    'name': tenant.name,
                    'house': tenant.house.number,
                    'credit_balance': credit_balance
                })

        return total_credit_balance, tenants_with_credit  # Return both total balance and list of tenants

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total_credit_balance, tenants_with_credit = self.get_total_credit_balance()  # Call the method
        context['total_credit_balance'] = total_credit_balance  # Add total balance to context
        context['tenants'] = tenants_with_credit  # Add list of tenants to context
        return context



class OverdueRentalsReportView(LoginRequiredMixin, TemplateView):
    template_name = 'overdue-rentals-report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all tenants with an outstanding balance
        tenants_with_outstanding_balance = []
        total_overdue_balance = Decimal('0.00')  # Initialize total overdue balance

        for tenant in Tenant.objects.all():
            outstanding_balance = tenant.outstanding_balance()
            if outstanding_balance > 0:
                tenants_with_outstanding_balance.append({
                    'name': tenant.name,
                    'house': tenant.house.number,
                    'outstanding_balance': outstanding_balance
                })
                total_overdue_balance += outstanding_balance  # Add to total overdue balance

        # Add the tenants and total overdue balance to the context
        context['tenants'] = tenants_with_outstanding_balance
        context['total_overdue_balance'] = total_overdue_balance
        
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
    



User = get_user_model()

class UserManagementView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = 'users.html'
    context_object_name = 'users'

    def test_func(self):
        # Only superusers can access this page
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_superuser'] = self.request.user.is_superuser
        return context

    def post(self, request, *args, **kwargs):
        # Handle adding a new user
        if 'add_user' in request.POST:
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')

            if not (username and email and password):
                messages.error(request, 'All fields are required.')
            else:
                # Create the user
                try:
                    User.objects.create_user(
                        username=username,
                        email=email,
                        password=password
                    )
                    messages.success(request, 'User added successfully!')
                except Exception as e:
                    messages.error(request, f'Error adding user: {str(e)}')

        # Handle deleting a user
        elif 'delete_user' in request.POST:
            user_id = request.POST.get('user_id')
            user = get_object_or_404(User, id=user_id)
            user.delete()
            messages.success(request, 'User deleted successfully!')

        return redirect('rentals:users')


class MyProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user  # Pass the logged-in user to the template
        return context
    

class UpdateProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'update_profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user  # Pass the logged-in user to the template
        return context

    def post(self, request, *args, **kwargs):
        user = request.user
        user.username = request.POST.get('username')
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.save()
        messages.success(request, 'Your profile has been updated!')
        return redirect('rentals:profile')


class ChangePasswordView(LoginRequiredMixin, TemplateView):
    template_name = 'change_password.html'

    def post(self, request, *args, **kwargs):
        user = request.user
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')

        # Validate the old password
        if not user.check_password(old_password):
            messages.error(request, 'Your old password was entered incorrectly. Please try again.')
            return redirect('change_password')

        # Validate the new passwords
        if new_password1 != new_password2:
            messages.error(request, 'The new passwords do not match.')
            return redirect('change_password')

        # Update the password
        user.set_password(new_password1)
        user.save()

        # Keep the user logged in
        update_session_auth_hash(request, user)

        # Display success message and redirect
        messages.success(request, 'Your password has been updated!')
        return redirect('rentals:profile')
