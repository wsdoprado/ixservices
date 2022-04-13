from rest_framework import routers

from .views import (ASViewSet, TagDomainViewSet, TagViewSet, IXViewSet, IPv4AddressViewSet, IPv6AddressViewSet, MacAddressViewSet, ServiceTypeViewSet, ServiceViewSet,  
                    CustomerServiceViewSet, CustomerConnectionViewSet, ATMv4ServiceViewSet, ATMv6ServiceViewSet, BilateralServiceViewSet, CustomerServiceProtectedViewSet, 
                    CustomerConnectionProtectedViewSet, FreeCustomerConnectionViewSet, BusyCustomerConnectionViewSet, InterfaceDViewSet, InterfaceFViewSet, InterfaceBViewSet,
                    FrontPortViewSet, RearPortViewSet, RearPortDViewSet, InterfaceFrontPortRearPortViewSet, CustomerConnectionTypeViewSet, CustomerConnectionEndpointViewSet,
                    CreateNewCustomerConnectionViewSet, CreateOrUpdateCustomerServiceViewSet)

v1router = routers.DefaultRouter()

v1router.register('as', ASViewSet, 'as')
v1router.register('ix', IXViewSet, 'ix')
v1router.register('tag', TagViewSet, 'tag')
v1router.register('tagdomain', TagDomainViewSet, 'tagdomain')
v1router.register('ipv4', IPv4AddressViewSet, 'ipv4')
v1router.register('ipv6', IPv6AddressViewSet, 'ipv6')
v1router.register('mac', MacAddressViewSet, 'mac')
v1router.register('servicetype', ServiceTypeViewSet, 'servicetype')
v1router.register('service', ServiceViewSet, 'service')

v1router.register('customerservice', CustomerServiceViewSet, 'customerservice')
v1router.register('createorupdatecustomerservice', CreateOrUpdateCustomerServiceViewSet, 'createorupdatecustomerservice')
# v1router.register('customerservice-protected', CustomerServiceProtectedViewSet, 'customerservice-protected')
v1router.register('customerconnectiontype', CustomerConnectionTypeViewSet, 'customerconnectiontype')
v1router.register('customerconnection', CustomerConnectionViewSet, 'customerconnection')
v1router.register('createnewcustomerconnection', CreateNewCustomerConnectionViewSet, 'createnewcustomerconnection')
v1router.register('customerconnectionendpoint', CustomerConnectionEndpointViewSet, 'customerconnectionendpoint')
# v1router.register('customerconnection-protected', CustomerConnectionProtectedViewSet, 'customerconnection-protected')
v1router.register('atmv4', ATMv4ServiceViewSet, 'atmv4')
v1router.register('atmv6', ATMv6ServiceViewSet, 'atmv6')
v1router.register('bilateral', BilateralServiceViewSet, 'bilateral')

v1router.register('interfaces-device', InterfaceDViewSet, 'interfaces-device')
v1router.register('interfaces-free', InterfaceFViewSet, 'interfaces-free')
# v1router.register('interfacefrontportrearport', InterfaceFrontPortRearPortViewSet, 'interfacefrontportrearport')
v1router.register('frontport', FrontPortViewSet, 'frontport')
v1router.register('rearport', RearPortViewSet, 'rearport')
v1router.register('rearports-device', RearPortDViewSet, 'rearports-device')
v1router.register('interfaces-busy', InterfaceBViewSet, 'interfaces-busy')
v1router.register('customerconnection-free', FreeCustomerConnectionViewSet, 'customerconnection-free')
v1router.register('customerconnection-busy', BusyCustomerConnectionViewSet, 'customerconnection-busy')

app_name = 'ixservices'

urlpatterns = v1router.urls
