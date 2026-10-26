from django.db import models
from django.contrib.auth.models import AbstractUser




class Label(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    country = models.CharField(max_length=50, blank=True)
    currency = models.CharField(max_length=4, default='EUR')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class UserRole(models.TextChoices):
    LABEL_OWNER = 'label_owner', 'Label Owner'
    LABEL_MEMBER = 'label_member', 'Member of Label'
    LABEL_MARKETING = 'marketing_manager', 'Marketing Manager'

class User(AbstractUser):
    pass


class Membership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    label = models.ForeignKey(Label, null=True, blank=True, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=25, choices=UserRole.choices, default=UserRole.LABEL_OWNER)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'label'],
                                  name = 'unique_user_label_membership'  )
        ]



class Release(models.Model):
    label = models.ForeignKey(Label, on_delete=models.CASCADE, related_name='releases')
    title = models.CharField(max_length=350)
    artist = models.CharField(max_length=200)
    catalog_number = models.CharField(max_length=50)
    release_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FormatType(models.TextChoices):
    LP = "lp", "LP"
    CD = "cd", "CD"
    CASSETTE = "cassette", "Cassette"
    DIGITAL = "digital", "Digital"
    OTHER = "other", "Other"

class FormatStatus(models.TextChoices):
    PLANNED = "planned", "Planned"
    ACTIVE = "active", "Active"
    SOLD_OUT = "sold_out", "Sold Out"
    ARCHIVED = "archived", "Archived"



class ReleaseFormat(models.Model):
    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name='formats')
    format_type = models.CharField(max_length=40, choices=FormatType.choices)
    catalog_number = models.CharField(max_length=40)
    edition = models.CharField(max_length=40, blank=True)
    quantity_produced = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_quantity = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=FormatStatus.choices, default=FormatStatus.PLANNED)


    def __str__(self):
        return f'{self.release.title} - {self.format_type}'


class Track(models.Model):
    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name='tracks')
    title = models.CharField(max_length=350)
    position = models.IntegerField()
    duration = models.DurationField(null=True, blank=True)


class Contact(models.Model):
    label = models.ForeignKey(Label, on_delete=models.CASCADE, related_name='contacts')
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    contact_type = models.CharField(max_length=50, blank=True)


class OrderStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PENDING = "pending", "Pending"
    PAID = "paid", "Paid"
    SHIPPED = "shipped", "Shipped"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class Order(models.Model):
    label = models.ForeignKey(Label, on_delete=models.CASCADE, related_name='orders')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='orders', null=True, blank=True)
    order_date = models.DateField()
    status = models.CharField(max_length=40 , choices=OrderStatus.choices, default=OrderStatus.DRAFT)
    currency = models.CharField(max_length=4, default="EUR")
    notes = models.TextField(blank=True)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    release_format = models.ForeignKey(ReleaseFormat, on_delete=models.CASCADE, related_name='order_items')
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)