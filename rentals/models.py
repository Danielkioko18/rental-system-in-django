from django.db import models

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
    house = models.OneToOneField(House, on_delete=models.CASCADE, unique=True)
    overdue_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    credit_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    date_joined = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name


class Payment(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    payment_date = models.DateField()
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=[('cash', 'Cash'), ('bank', 'Bank Transfer'), ('mobile', 'Mobile Payment')])
    overdue_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    is_overdue = models.BooleanField(default=False)

    def __str__(self):
        return f"Payment for {self.tenant.name} on {self.payment_date}"

