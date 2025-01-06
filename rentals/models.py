from django.db import models

class HouseType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} - £{self.monthly_rent}"
