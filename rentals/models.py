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
