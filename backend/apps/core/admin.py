from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Label, Membership, User, Release, ReleaseFormat, Track, Contact, Order, OrderItem


admin.site.register(Label)
admin.site.register(Membership)
admin.site.register(Release)
admin.site.register(ReleaseFormat)
admin.site.register(Track)
admin.site.register(Contact)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "label",
        "contact",
        "status",
        "order_date",
    )

    inlines = [OrderItemInline]


admin.site.register(OrderItem)



@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    pass
