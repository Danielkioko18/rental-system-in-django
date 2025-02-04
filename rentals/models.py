from django.db import models
from django.db.models import Sum
from datetime import date
from decimal import Decimal

class HouseType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} - £{self.monthly_rent}"


class House(models.Model):
    HOUSE_TYPES = [
        ('Bedsitter', 'Bedsitter'),
        ('One Bedroom', 'One Bedroom'),
        ('Two Bedroom', 'Two Bedroom'),
        ('Three Bedroom', 'Three Bedroom'),
    ]

    number = models.CharField(max_length=20, unique=True)
    house_type = models.CharField(max_length=50, choices=HOUSE_TYPES)
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2)
    is_occupied = models.BooleanField(default=False)

    def __str__(self):
        return f"House {self.number} ({self.house_type})"


class Tenant(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=15)
    house = models.OneToOneField('House', on_delete=models.CASCADE, unique=True)
    date_joined = models.DateField(auto_now_add=True)
    
    def outstanding_balance(self):
        months_since_joining = (date.today().year - self.date_joined.year) * 12 + date.today().month - self.date_joined.month
        total_due = months_since_joining * self.house.monthly_rent
        total_paid = Payment.objects.filter(tenant=self).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
        return total_due - total_paid
    
    def last_payment(self):
        last_payment = Payment.objects.filter(tenant=self).order_by('-payment_date').first()
        return last_payment.payment_date if last_payment else None  # Return None instead of a string

    def __str__(self):
        return self.name

class Payment(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    payment_date = models.DateField()
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        max_length=20, 
        choices=[('cash', 'Cash'), ('bank', 'Bank Transfer'), ('mobile', 'Mobile Payment')]
    )

    def __str__(self):
        return f"Payment for {self.tenant.name} on {self.payment_date}"
