from django.contrib import admin
from .models import (IX, AS, ServiceTag, CustomerConnection, CustomerConnectionEndpoint, CustomerService, IXService, ServiceType, 
                             MACAddress, IPv4Address, IPv6Address)

# Register your models here.

@admin.register(IX)
class IXAdmin(admin.ModelAdmin):
    list_display = ('code',)
    search_fields = ["code"]

@admin.register(AS)
class ASAdmin(admin.ModelAdmin):
    list_display = ('number',)
    search_fields = ["number"]

@admin.register(ServiceTag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('tag',)
    search_fields = ["tag", "ix"]

@admin.register(CustomerConnection)
class CustomerConnectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_lag', 'ticket')
    search_fields = ["name"]

@admin.register(CustomerConnectionEndpoint)
class CustomerConnectionEndpointAdmin(admin.ModelAdmin):
    list_display = ('customer_connection', 'switch_ip', 'port_name')
    search_fields = ["customer_connection"]

@admin.register(CustomerService)
class CustomerServiceAdmin(admin.ModelAdmin):
    list_display = ('asn', 'service',)
    search_fields = ["service"]

@admin.register(IXService)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)
    search_fields = ["name"]

@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'num_clients')
    search_fields = ["name"]

@admin.register(MACAddress)
class MACAddressAdmin(admin.ModelAdmin):
    list_display = ('address',)
    search_fields = ["address"]

@admin.register(IPv4Address)
class IPv4AddressAdmin(admin.ModelAdmin):
    list_display = ('address',)
    search_fields = ["address", 'ix__code']

@admin.register(IPv6Address)
class IPv6AddressAdmin(admin.ModelAdmin):
    list_display = ('address',)
    search_fields = ["address", 'ix__code']

