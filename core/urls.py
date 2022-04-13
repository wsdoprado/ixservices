from rest_framework import routers
# from django.urls import path, include

from netbox.api import OrderedDefaultRouter

from .views import (RootView, IXSelectViewSet, ASSelectViewSet, ServiceTagSelectViewSet, 
                    IPv4AddressSelectViewSet, IPv6AddressSelectViewSet, MACAddressSelectViewSet,
                    ServiceSelectViewSet, CustomerConnectionSelectViewSet, ServiceTypeSelectViewSet,
                    ServiceTagDomainSelectViewSet, CustomerConnectionTypeSelectViewSet, CustomerConnectionNameSelectViewSet, InterfaceLagSelectViewSet)

# v1router = routers.DefaultRouter()

v1router = OrderedDefaultRouter()
v1router.APIRootView = RootView

v1router.register('ix', IXSelectViewSet, 'ix')
v1router.register('as', ASSelectViewSet, 'as')
v1router.register('servicetag', ServiceTagSelectViewSet, 'servicetag')
v1router.register('servicetagdomain', ServiceTagDomainSelectViewSet, 'servicetagdomain')
v1router.register('ipv4address', IPv4AddressSelectViewSet, 'ipv4address')
v1router.register('ipv6address', IPv6AddressSelectViewSet, 'ipv6address')
v1router.register('macaddress', MACAddressSelectViewSet, 'macaddress')
v1router.register('ixservice', ServiceSelectViewSet, 'ixservice')
v1router.register('servicetype', ServiceTypeSelectViewSet, 'servicetype')
v1router.register('customerconnection', CustomerConnectionSelectViewSet, 'customerconnection')
v1router.register('customerconnectiontype', CustomerConnectionTypeSelectViewSet, 'customerconnectiontype')
v1router.register('interface', InterfaceLagSelectViewSet, 'interface')

# connection name based on device name and asn
# v1router.register('customerconnectionname', CustomerConnectionNameSelectViewSet, 'customerconnectionname')

app_name = 'api-select'

urlpatterns = v1router.urls
