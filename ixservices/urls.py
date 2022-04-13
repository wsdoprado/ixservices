from django.urls import path, include
from django.contrib import admin

from .views import HomeView, ASListView, ASView, ASEditView, ASDeleteView
from .views import IXListView, IXEditView, IXView, IXDeleteView
from .views import TagListView, TagView, TagEditView, TagDeleteView
from .views import ServiceTagDomainListView, ServiceTagDomainView, ServiceTagDomainEditView, ServiceTagDomainDeleteView
from .views import IPv4AddressListView, IPv4AddressView, IPv4AddressEditView, IPv4AddressDeleteView
from .views import IPv6AddressListView, IPv6AddressView, IPv6AddressEditView, IPv6AddressDeleteView
from .views import MACAddressListView, MACAddressView, MACAddressEditView, MACAddressDeleteView
from .views import ServiceTypeListView, ServiceTypeView, ServiceTypeEditView, ServiceTypeDeleteView
from .views import ServiceListView, ServiceView, ServiceEditView, ServiceDeleteView
from .views import CustomerServiceListView, CustomerServiceView, CustomerServiceEditView, CustomerServiceDeleteView
from .views import CustomerConnectionTypeListView, CustomerConnectionTypeView, CustomerConnectionTypeEditView, CustomerConnectionTypeDeleteView
from .views import CustomerConnectionListView, CustomerConnectionView, CustomerConnectionEditView, CustomerConnectionDeleteView, CustomerConnectionAddView
from .views import CustomerConnectionEndpointListView, CustomerConnectionEndpointView, CustomerConnectionEndpointEditView, CustomerConnectionEndpointDeleteView, ConnectionCustomerConnectionEndpointsView
from .views import CustomerConnectionObjectChangeLogView, CustomerConnectionTypeObjectChangeLogView, CustomerConnectionEndpointObjectChangeLogView, CustomerConnectionEndpointConnectView
from .views import ServiceObjectChangeLogView, ServiceTypeObjectChangeLogView, ServiceTagObjectChangeLogView, ServiceTagDomainObjectChangeLogView, CustomerServiceObjectChangeLogView

from dcim import views

from .models import (AS, IX, ServiceTagDomain, ServiceTag, IPv4Address, IPv6Address, MACAddress,
                     ServiceType, IXService, CustomerService, CustomerConnectionType,
                     CustomerConnection, CustomerConnectionEndpoint)

from ixservices.core.views import ObjectChangeLogView, IXSelectViewSet

# app_name = 'ixservices'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('admin/', admin.site.urls),
    path('api/select/', include('ixservices.core.urls'), name='api-select'),
    
    ### define all models endpoints
    path('ix/', IXListView.as_view(), name='ix_list'),
    path('ix/add/', IXEditView.as_view(), name='ix_add'),
    path('ix/<int:pk>/', IXView.as_view(), name='ix'),
    path('ix/<int:pk>/edit/', IXEditView.as_view(), name='ix_edit'),
    path('ix/<int:pk>/delete/', IXDeleteView.as_view(), name='ix_delete'),
    path('ix/<int:pk>/changelog/', ObjectChangeLogView.as_view(), name='ix_changelog', kwargs={'model': IX}),
  
    path('as/', ASListView.as_view(), name='as_list'),
    path('as/add/', ASEditView.as_view(), name='as_add'),
    # path('asn/import/', views.SiteBulkImportView.as_view(), name='asn_import'),
    # path('asn/edit/', views.SiteBulkEditView.as_view(), name='asn_bulk_edit'),
    # path('asn/delete/', views.SiteBulkDeleteView.as_view(), name='asn_bulk_delete'),
    path('as/<int:pk>/', ASView.as_view(), name='as'),
    path('as/<int:pk>/edit/', ASEditView.as_view(), name='as_edit'),
    path('as/<int:pk>/delete/', ASDeleteView.as_view(), name='as_delete'),
    path('as/<int:pk>/changelog/', ObjectChangeLogView.as_view(), name='as_changelog', kwargs={'model': AS}),
    
    ## core urls for services
    path('tag/', TagListView.as_view(), name='servicetag_list'),
    path('tag/add/', TagEditView.as_view(), name='servicetag_add'),
    path('tag/<int:pk>/', TagView.as_view(), name='servicetag'),
    path('tag/<int:pk>/edit/', TagEditView.as_view(), name='servicetag_edit'),
    path('tag/<int:pk>/delete/', TagDeleteView.as_view(), name='servicetag_delete'),
    path('tag/<int:pk>/changelog/', ServiceTagObjectChangeLogView.as_view(), name='servicetag_changelog', kwargs={'model': ServiceTag}),

    path('servicetagdomain/', ServiceTagDomainListView.as_view(), name='servicetagdomain_list'),
    path('servicetagdomain/add/', ServiceTagDomainEditView.as_view(), name='servicetagdomain_add'),
    path('servicetagdomain/<int:pk>/', ServiceTagDomainView.as_view(), name='servicetagdomain'),
    path('servicetagdomain/<int:pk>/edit/', ServiceTagDomainEditView.as_view(), name='servicetagdomain_edit'),
    path('servicetagdomain/<int:pk>/delete/', ServiceTagDomainDeleteView.as_view(), name='servicetagdomain_delete'),
    path('servicetagdomain/<int:pk>/changelog/', ServiceTagDomainObjectChangeLogView.as_view(), name='servicetagdomain_changelog', kwargs={'model': ServiceTagDomain}),

    path('ipv4/', IPv4AddressListView.as_view(), name='ipv4address_list'),
    path('ipv4/add/', IPv4AddressEditView.as_view(), name='ipv4address_add'),
    path('ipv4/<int:pk>/', IPv4AddressView.as_view(), name='ipv4address'),
    path('ipv4/<int:pk>/edit/', IPv4AddressEditView.as_view(), name='ipv4address_edit'),
    path('ipv4/<int:pk>/delete/', IPv4AddressDeleteView.as_view(), name='ipv4address_delete'),
    path('ipv4/<int:pk>/changelog/', ObjectChangeLogView.as_view(), name='ipv4address_changelog', kwargs={'model': IPv4Address}),

    path('ipv6/', IPv6AddressListView.as_view(), name='ipv6address_list'),
    path('ipv6/add/', IPv6AddressEditView.as_view(), name='ipv6address_add'),
    path('ipv6/<int:pk>/', IPv6AddressView.as_view(), name='ipv6address'),
    path('ipv6/<int:pk>/edit/', IPv6AddressEditView.as_view(), name='ipv6address_edit'),
    path('ipv6/<int:pk>/delete/', IPv6AddressDeleteView.as_view(), name='ipv6address_delete'),
    path('ipv6/<int:pk>/changelog/', ObjectChangeLogView.as_view(), name='ipv6address_changelog', kwargs={'model': IPv6Address}),

    path('macaddress/', MACAddressListView.as_view(), name='macaddress_list'),
    path('macaddress/add/', MACAddressEditView.as_view(), name='macaddress_add'),
    path('macaddress/<int:pk>/', MACAddressView.as_view(), name='macaddress'),
    path('macaddress/<int:pk>/edit/', MACAddressEditView.as_view(), name='macaddress_edit'),
    path('macaddress/<int:pk>/delete/', MACAddressDeleteView.as_view(), name='macaddress_delete'),
    path('macaddress/<int:pk>/changelog/', ObjectChangeLogView.as_view(), name='macaddress_changelog', kwargs={'model': MACAddress}),

    ### urls for services
    path('servicetype/', ServiceTypeListView.as_view(), name='servicetype_list'),
    path('servicetype/add/', ServiceTypeEditView.as_view(), name='servicetype_add'),
    path('servicetype/<int:pk>/', ServiceTypeView.as_view(), name='servicetype'),
    path('servicetype/<int:pk>/edit/', ServiceTypeEditView.as_view(), name='servicetype_edit'),
    path('servicetype/<int:pk>/delete/', ServiceTypeDeleteView.as_view(), name='servicetype_delete'),
    path('servicetype/<int:pk>/changelog/', ServiceTypeObjectChangeLogView.as_view(), name='servicetype_changelog', kwargs={'model': ServiceType}),

    path('service/', ServiceListView.as_view(), name='ixservice_list'),
    path('service/add/', ServiceEditView.as_view(), name='ixservice_add'),
    path('service/<int:pk>/', ServiceView.as_view(), name='ixservice'),
    path('service/<int:pk>/edit/', ServiceEditView.as_view(), name='ixservice_edit'),
    path('service/<int:pk>/delete/', ServiceDeleteView.as_view(), name='ixservice_delete'),
    path('service/<int:pk>/changelog/', ServiceObjectChangeLogView.as_view(), name='ixservice_changelog', kwargs={'model': IXService}),

    path('customerservice/', CustomerServiceListView.as_view(), name='customerservice_list'),
    path('customerservice/<int:service_type>', CustomerServiceListView.as_view(), name='customerservicetype_list'),
    path('customerservice/add/', CustomerServiceEditView.as_view(), name='customerservice_add'),
    path('customerservice/<int:pk>/', CustomerServiceView.as_view(), name='customerservice'),
    path('customerservice/<int:pk>/edit/', CustomerServiceEditView.as_view(), name='customerservice_edit'),
    path('customerservice/<int:pk>/delete/', CustomerServiceDeleteView.as_view(), name='customerservice_delete'),
    path('customerservice/<int:pk>/changelog/', CustomerServiceObjectChangeLogView.as_view(), name='customerservice_changelog', kwargs={'model': CustomerService}),

    ### urls for connections
    path('customerconnectiontype/', CustomerConnectionTypeListView.as_view(), name='customerconnectiontype_list'),
    path('customerconnectiontype/add/', CustomerConnectionTypeEditView.as_view(), name='customerconnectiontype_add'),
    path('customerconnectiontype/<int:pk>/', CustomerConnectionTypeView.as_view(), name='customerconnectiontype'),
    path('customerconnectiontype/<int:pk>/edit/', CustomerConnectionTypeEditView.as_view(), name='customerconnectiontype_edit'),
    path('customerconnectiontype/<int:pk>/delete/', CustomerConnectionTypeDeleteView.as_view(), name='customerconnectiontype_delete'),
    path('customerconnectiontype/<int:pk>/changelog/', CustomerConnectionTypeObjectChangeLogView.as_view(), name='customerconnectiontype_changelog', kwargs={'model': CustomerConnectionType}),
    
    path('customerconnection/', CustomerConnectionListView.as_view(), name='customerconnection_list'),
    path('customerconnection/add/', CustomerConnectionAddView.as_view(), name='customerconnection_add'),
    path('customerconnection/<int:pk>/', CustomerConnectionView.as_view(), name='customerconnection'),
    path('customerconnection/<int:pk>/edit/', CustomerConnectionEditView.as_view(), name='customerconnection_edit'),
    path('customerconnection/<int:pk>/delete/', CustomerConnectionDeleteView.as_view(), name='customerconnection_delete'),
    path('customerconnection/<int:pk>/changelog/', CustomerConnectionObjectChangeLogView.as_view(), name='customerconnection_changelog', kwargs={'model': CustomerConnection}),
    path('customerconnection/<int:pk>/customerconnectionendpoints/', ConnectionCustomerConnectionEndpointsView.as_view(), name='customerconnection_customerconnectionendpoint'),
    path('customerconnection/<int:customer_connection_id>/connect/<str:termination_type>/', CustomerConnectionEndpointConnectView.as_view(), name='customerconnection_connect', kwargs={'model': CustomerConnection}),

    path('customerconnectionendpoint/', CustomerConnectionEndpointListView.as_view(), name='customerconnectionendpoint_list'),
    path('customerconnectionendpoint/add/', CustomerConnectionEndpointEditView.as_view(), name='customerconnectionendpoint_add'),
    path('customerconnectionendpoint/<int:pk>/', CustomerConnectionEndpointView.as_view(), name='customerconnectionendpoint'),
    path('customerconnectionendpoint/<int:pk>/edit/', CustomerConnectionEndpointEditView.as_view(), name='customerconnectionendpoint_edit'),
    path('customerconnectionendpoint/<int:pk>/delete/', CustomerConnectionEndpointDeleteView.as_view(), name='customerconnectionendpoint_delete'),
    path('customerconnectionendpoint/<int:pk>/changelog/', CustomerConnectionEndpointObjectChangeLogView.as_view(), name='customerconnectionendpoint_changelog', kwargs={'model': CustomerConnectionEndpoint}),

]