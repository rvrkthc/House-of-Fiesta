from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class Category(models.Model):
    class Meta:
        verbose_name_plural = 'categories'

    name = models.CharField(max_length=64)
    slug = models.SlugField(primary_key=True, max_length=64)
    description = models.TextField(null=True, blank=True)

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    category = models.ForeignKey(to=Category, null=True,
                                 on_delete=models.SET_NULL)
    title = models.CharField(max_length=64)
    stock_keeping_unit = models.SlugField(primary_key=True, max_length=64)
    description = models.TextField(null=True, blank=True)
    body = models.TextField(null=True, blank=True)
    unit_cost = models.DecimalField(max_digits=7, decimal_places=2)
    unit_price = models.DecimalField(max_digits=7, decimal_places=2)
    is_enabled = models.BooleanField()

    def is_in_stock(self) -> bool:
        """
        Checks if at least one enabled inventory has stock.
        """
        for inventory in self.inventory_set.all():
            if inventory.is_in_stock():
                return True
        return False

    def available_stock(self) -> int:
        """
        Fetches all available inventory counts.
        """
        total_stock = 0
        for inventory in self.inventory_set.all():
            total_stock += inventory.units_in_stock
        return total_stock

    def __str__(self) -> str:
        return self.title


class ProductImage(models.Model):
    product = models.ForeignKey(to=Product, on_delete=models.CASCADE)
    image = models.ImageField()


class WishlistItem(models.Model):
    wished_by = models.ForeignKey(to=User, on_delete=models.CASCADE)
    product = models.ForeignKey(to=Product, on_delete=models.CASCADE)


class Location(models.Model):
    name = models.CharField(max_length=64)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    province = models.CharField(max_length=255)
    region = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.name


class Inventory(models.Model):
    class Meta:
        verbose_name_plural = 'inventories'

    location = models.ForeignKey(to=Location, on_delete=models.CASCADE)
    product = models.ForeignKey(to=Product, on_delete=models.CASCADE)
    units_in_stock = models.PositiveSmallIntegerField()

    def is_in_stock(self) -> bool:
        return self.units_in_stock > 0


class Order(models.Model):
    placed_by = models.ForeignKey(to=User, null=True,
                                  on_delete=models.CASCADE)
    status = models.CharField(max_length=2,
                              choices=[
                                  ('NW', 'NEW'),
                                  ('PR', 'PROCESSING'),
                                  ('DL', 'DELIVERING'),
                                  ('DN', 'DONE'),
                                  ('DE', 'DENIED'),
                                  ('CN', 'CANCELLED')])
    billing_first_name = models.CharField(max_length=64)
    billing_last_name = models.CharField(max_length=64)
    billing_address = models.CharField(max_length=255)
    billing_city = models.CharField(max_length=255)
    billing_province = models.CharField(max_length=255)
    billing_region = models.CharField(max_length=255)
    billing_zip = models.CharField(max_length=10)
    billing_phone = models.CharField(max_length=13)
    shipping_first_name = models.CharField(max_length=64)
    shipping_last_name = models.CharField(max_length=64)
    shipping_address = models.CharField(max_length=255)
    shipping_city = models.CharField(max_length=255)
    shipping_province = models.CharField(max_length=255)
    shipping_region = models.CharField(max_length=255)
    shipping_phone = models.CharField(max_length=13)
    shipping_zip = models.CharField(max_length=10)
    delivery_fee = models.DecimalField(max_digits=7, decimal_places=2)

    def total(self):
        total = 0
        for orderitem in self.orderitem_set.all():
            total += orderitem.total()
        total += self.delivery_fee
        return total


class OrderItem(models.Model):
    order = models.ForeignKey(to=Order, on_delete=models.CASCADE)
    product = models.ForeignKey(to=Product, null=True,
                                on_delete=models.CASCADE)
    unit_price = models.DecimalField(max_digits=7, decimal_places=2)
    quantity = models.PositiveSmallIntegerField()

    def total(self):
        return self.unit_price * self.quantity
