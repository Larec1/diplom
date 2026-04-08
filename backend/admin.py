from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from backend.models import (
    Category,
    Contact,
    Order,
    OrderItem,
    Parameter,
    Product,
    ProductInfo,
    ProductParameter,
    Shop,
    User,
)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ('email',)
    list_display = ('email', 'username', 'first_name', 'last_name', 'user_type', 'is_staff', 'is_active')
    search_fields = ('email', 'username', 'first_name', 'last_name')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Личные данные', {'fields': ('username', 'first_name', 'last_name', 'company', 'position', 'user_type')}),
        ('Права', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Даты', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('email', 'username', 'password1', 'password2', 'user_type'),
            },
        ),
    )


admin.site.register(Shop)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(ProductInfo)
admin.site.register(Parameter)
admin.site.register(ProductParameter)
admin.site.register(Contact)
admin.site.register(Order)
admin.site.register(OrderItem)
