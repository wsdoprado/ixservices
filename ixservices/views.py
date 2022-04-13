from django import forms
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Count
from django.contrib.contenttypes.models import ContentType

from ixservices.ixservices.models import (AS, IX, ServiceTagDomain, ServiceTag, IPv4Address, IPv6Address, MACAddress,
                                          ServiceType, IXService, CustomerService, CustomerConnectionType,
                                          CustomerConnection, CustomerConnectionEndpoint)

from utilities.tables import paginate_table
### netbox core reimplemented
from ixservices.core import generic
from ixservices.core import views
from ixservices.core import forms
from ixservices.core import filterforms
from ixservices.core import filtersets
from ixservices.core import tables
from django.views.generic import View

from ixservices.ixservices.utils.status import TagStatusChoices

def index(request):
    return render(request, 'home.html')


####### HOME Impl. from Netbox v3.0.4 #######################################################

class HomeView(views.HomeView):    

    def get(self, request):
        super().get(request)        

        def build_stats():
            # core data
            app_label = 'ixservices'
            def get_view(model_name):
                return "plugins.{}.view_{}".format(app_label, model_name)
            def get_qs_count(qs):
                return qs.restrict(request.user, 'view').count
            def get_section_model(model_name, label, model, params=None):
                return get_view(model_name), label, get_qs_count(model.objects), params
            def get_section_filter(model_name, label, filtered, params=None):
                return get_view(model_name), label, get_qs_count(filtered), params
            def get_service_types(t):
                return CustomerService.objects.filter(service__service_type__pk=t)
            core = (
                (get_section_model("ix", "IXs", IX)),
                (get_section_model("as", "ASNs", AS)),
                (get_section_model("ipv4address", "IPv4s", IPv4Address)),
                (get_section_model("ipv6address", "IPv6s", IPv6Address)),
                (get_section_model("macaddress", "MACs", MACAddress)),
            ) 
           
            ### filter service types based on data already inserted
            serv = [
                get_section_model("servicetagdomain", "ServiceTagDomains", ServiceTagDomain),
                get_section_model("servicetag", "ServiceTags", ServiceTag),
                get_section_model("servicetype", "ServiceTypes", ServiceType),
                get_section_model("ixservice", "Services", IXService),
                get_section_model("customerservice", "CustomerServices", CustomerService)
            ] 
            serv.extend(
                [
                    get_section_filter(
                        "customerservice", 
                        st.name, 
                        get_service_types(st.pk),
                        params='service__service_type={}'.format(st.pk)
                    ) for st in ServiceType.objects.all()
                ]
            )    


            ### ### filter connection types from data inserted
            qs_cix_types = CustomerConnectionType.objects.exclude(connection_type=0)
            qs_individual = CustomerConnectionType.objects.filter(connection_type=0).first()

            def get_cix_params(qs_types):
                formated_params = (",".join([str(item.pk) for item in  qs_types]).replace(',','&connection_type='))
                return "{}{}".format("connection_type=",formated_params) if qs_types else None
            
            params_cix =  get_cix_params(qs_cix_types)
            params_indiv = 'connection_type={}'.format(qs_individual.pk) if qs_individual else None
            ## connections
            connections = (
                (get_section_model("customerconnectiontype", "CustomerConnectionTypes", CustomerConnectionType)),
                (get_section_model("customerconnection", "CustomerConnections", CustomerConnection)),
                (get_section_model("customerconnectionendpoint", "CustomerConnectionEndpoints", CustomerConnectionEndpoint)),
                ## filter connection types
                (get_section_filter("customerconnection", "CIXs", CustomerConnection.objects.exclude(connection_type__connection_type=0), params=params_cix)),
                (get_section_filter("customerconnection", "Individual", CustomerConnection.objects.filter(connection_type__connection_type=0), params=params_indiv)),
                (get_section_filter("customerconnection", "LAGs", CustomerConnection.objects.filter(is_lag=True), params='is_lag=True')),
            ) 

            sections = (
                ("Core", core, "domain"),
                 ## service data -- service types sections created
                ("Service", ((item for item in serv)), "server"),
                ("Connections", connections, "cable-data"),
            )
            stats = []
            
            for section_label, section_items, icon_class in sections:
                items = []
                for perm, item_label, get_count, params in section_items:
                    plugin_root, app, scope = perm.split(".")
                    url = ":".join((plugin_root, app, scope.replace("view_", "") + "_list"))
                    item = {
                        "label": item_label,
                        "count": None,
                        "url": url,
                        "disabled": True,
                        "icon": icon_class,
                        "params": params
                    }
                    if request.user.has_perm('.'.join([app,scope])):
                        item["count"] = get_count()
                        item["disabled"] = False
                    items.append(item)
                stats.append((section_label, items, icon_class))             

            return stats   

        self.context_data['stats'] = build_stats()  
        return render(request, self.template_name, self.context_data)

# list views
class IXListView(generic.ObjectListView):
    queryset = IX.objects.all()
    filterset = filtersets.IXFilterSet
    filterset_form = filterforms.IXFilterForm
    table = tables.IXTable

class ASListView(generic.ObjectListView):
    queryset = AS.objects.all()
    filterset = filtersets.ASFilterSet
    filterset_form = filterforms.ASFilterForm
    table = tables.ASTable

class TagListView(generic.ObjectListView):
    queryset = ServiceTag.objects.all()
    filterset = filtersets.TagFilterSet
    filterset_form = filterforms.TagFilterForm
    table = tables.TagTable

class ServiceTagDomainListView(generic.ObjectListView):
    queryset = ServiceTagDomain.objects.all()
    filterset = filtersets.ServiceTagDomainFilterSet
    filterset_form = filterforms.ServiceTagDomainFilterForm
    table = tables.ServiceTagDomainTable

class IPv4AddressListView(generic.ObjectListView):
    queryset = IPv4Address.objects.all()
    filterset = filtersets.IPv4AddressFilterSet
    filterset_form = filterforms.IPv4AddressFilterForm
    table = tables.IPv4AddressTable

class IPv6AddressListView(generic.ObjectListView):
    queryset = IPv6Address.objects.all()
    filterset = filtersets.IPv6AddressFilterSet
    filterset_form = filterforms.IPv6AddressFilterForm
    table = tables.IPv6AddressTable

class MACAddressListView(generic.ObjectListView):
    queryset = MACAddress.objects.all()
    filterset = filtersets.MACAddressFilterSet
    filterset_form = filterforms.MACAddressFilterForm
    table = tables.MACAddressTable

### services list views ##
class ServiceTypeListView(generic.ObjectListView):
    queryset = ServiceType.objects.all()
    filterset = filtersets.ServiceTypeFilterSet
    filterset_form = filterforms.ServiceTypeFilterForm
    table = tables.ServiceTypeTable

class ServiceListView(generic.ObjectListView):
    queryset = IXService.objects.all()
    filterset = filtersets.ServiceFilterSet
    filterset_form = filterforms.ServiceFilterForm
    table = tables.ServiceTable

class CustomerServiceListView(generic.ObjectListView):
    queryset = CustomerService.objects.prefetch_related('connection', 'connection__connected_device').order_by('id')
    filterset = filtersets.CustomerServiceFilterSet
    filterset_form = filterforms.CustomerServiceFilterForm
    table = tables.CustomerServiceTable

### connectionn list views
class CustomerConnectionTypeListView(generic.ObjectListView):
    queryset = CustomerConnectionType.objects.all()
    filterset = filtersets.CustomerConnectionTypeFilterSet
    filterset_form = filterforms.CustomerConnectionTypeFilterForm
    table = tables.CustomerConnectionTypeTable


class CustomerConnectionListView(generic.ObjectListView):
    queryset = CustomerConnection.objects.prefetch_related('customerservice', 'customerconnectionendpoint', 'connected_device')
    filterset = filtersets.CustomerConnectionFilterSet
    filterset_form = filterforms.CustomerConnectionFilterForm
    table = tables.CustomerConnectionTable


class CustomerConnectionEndpointListView(generic.ObjectListView):
    queryset = CustomerConnectionEndpoint.objects.all()
    filterset = filtersets.CustomerConnectionEndpointFilterSet
    filterset_form = filterforms.CustomerConnectionEndpointFilterForm
    table = tables.CustomerConnectionEndpointTable




#### views
class ASView(generic.ObjectView):
    template_name = 'ixservices/as.html'
    queryset = AS.objects.all()
    
    def get_extra_context(self, request, instance):
        stats = super().get_extra_context(request, instance)
        qs = CustomerService.objects.filter(asn=instance)
       
        def qs_restrict(qs):
            return qs.restrict(request.user, 'view')
        def get_total_by_ix(qs):
            qs = qs.values('service__ix', 'service__ix__code').annotate(Count('service')).order_by()
            return qs_restrict(qs)
        def get_services(qs):
            tot_services = qs_restrict(qs)
            tot_atmv4 = tot_services.filter(service__service_type__pk=1)
            tot_atmv6 = tot_services.filter(service__service_type__pk=2)
            tot_bilateral = tot_services.filter(service__service_type__pk=3)
            return tot_services.count(), tot_atmv4.count(), tot_atmv6.count(), tot_bilateral.count()
        
        total_by_ix = get_total_by_ix(qs)
        services, atmv4, atmv6, bilateral = get_services(qs)
        
        def get_stats():
            return { 
                'total_ix': total_by_ix.count(),
                'total_by_ix': total_by_ix,
                'total_services': services,
                'total_atmv4': atmv4,
                'total_atmv6': atmv6,
                'total_bilateral': bilateral,
            }
        
        stats['stats'] = get_stats() 
        return stats

class IXView(generic.ObjectView):
    queryset = IX.objects.all()

    def get_extra_context(self, request, instance):
        stats = super().get_extra_context(request, instance)
        qs, st = instance.servicetag_set, TagStatusChoices() 
        def qs_restrict(qs):
            return qs.restrict(request.user, 'view')
        def get_total_asns():
            qs = AS.objects.filter(customerservice__service__ix=instance).distinct()
            return qs_restrict(qs).count()
        def get_by_status(status):
            return qs_restrict(qs).filter(status=status).count()
        def get_total_ips(qs):
            tot_ips = qs_restrict(qs) 
            tot_ips_free = qs.filter(customerservice__isnull=True)
            tot_ips_alloc = qs.filter(customerservice__isnull=False)
            return tot_ips.count(), tot_ips_free.count(), tot_ips_alloc.count()
        def get_services():
            tot_services = CustomerService.objects.filter(service__ix=instance)
            tot_services = qs_restrict(tot_services)
            tot_atmv4 = tot_services.filter(service__service_type__pk=1)
            tot_atmv6 = tot_services.filter(service__service_type__pk=2)
            tot_bilateral = tot_services.filter(service__service_type__pk=3)
            return tot_services.count(), tot_atmv4.count(), tot_atmv6.count(), tot_bilateral.count()
        
        ipv4, ipv4_free, ipv4_alloc = get_total_ips(instance.ipv4address.all())
        ipv6, ipv6_free, ipv6_alloc = get_total_ips(instance.ipv6address.all())
        services, atmv4, atmv6, bilateral = get_services()
        
        def get_stats():
            return { 
                'total_asn': get_total_asns(),
                'total_services': services,
                'total_atmv4': atmv4,
                'total_atmv6': atmv6,
                'total_bilateral': bilateral,
                'total_ipv4': ipv4,
                'total_ipv4_free': ipv4_free,
                'total_ipv4_alloc': ipv4_alloc,
                'total_ipv6': ipv6,
                'total_ipv6_free': ipv6_free,
                'total_ipv6_alloc': ipv6_alloc,
                'tags_avail_count': get_by_status(st.STATUS_AVAILABLE),
                'tags_alloc_count': get_by_status(st.STATUS_ALLOCATED),
                'tags_prod_count':  get_by_status(st.STATUS_PRODUCTION),
            }
        
        stats['stats'] = get_stats() 
        return stats

class TagView(generic.ObjectView):
    template_name = 'ixservices/service/servicetag.html'
    queryset = ServiceTag.objects.prefetch_related('ix')

class ServiceTagDomainView(generic.ObjectView):
    template_name = 'ixservices/service/servicetagdomain.html'
    queryset = ServiceTagDomain.objects.prefetch_related('ix')

    def get_extra_context(self, request, instance):
        stats = super().get_extra_context(request, instance)
        qs, st = instance.servicetags, TagStatusChoices() 
        def qs_restrict(qs):
            return qs.restrict(request.user, 'view')
        def get_by_status(status):
            return qs_restrict(qs).filter(status=status).count()        
        def get_stats():
            return { 
                'tags_avail_count': get_by_status(st.STATUS_AVAILABLE),
                'tags_alloc_count': get_by_status(st.STATUS_ALLOCATED),
                'tags_prod_count':  get_by_status(st.STATUS_PRODUCTION),
            }
        
        stats['stats'] = get_stats() 
        return stats

class IPv4AddressView(generic.ObjectView):
    queryset = IPv4Address.objects.prefetch_related('ix')

class IPv6AddressView(generic.ObjectView):
    queryset = IPv6Address.objects.prefetch_related('ix')

class MACAddressView(generic.ObjectView):
    queryset = MACAddress.objects.all()

### service views ##
class ServiceTypeView(generic.ObjectView):
    template_name = 'ixservices/service/servicetype.html'
    queryset = ServiceType.objects.all()

class ServiceView(generic.ObjectView):
    template_name = 'ixservices/service/ixservice.html'
    queryset = IXService.objects.prefetch_related('ix')

class CustomerServiceView(generic.ObjectView):
    template_name = 'ixservices/service/customerservice.html'
    queryset = CustomerService.objects.prefetch_related(
        'asn', 'service', 'mlpav4_address', 'mlpav6_address', 'mac_address', 'connection')

### connection views ##
class CustomerConnectionTypeView(generic.ObjectView):
    template_name = 'ixservices/customerconnection/customerconnectiontype.html'
    queryset = CustomerConnectionType.objects.all()

class CustomerConnectionView(generic.ObjectView):
    template_name = 'ixservices/customerconnection/customerconnection.html'
    queryset = CustomerConnection.objects.all()

    def get_extra_context(self, request, instance):
        stats = super().get_extra_context(request, instance)
        qs = instance.customerservice.all()
        def qs_restrict(qs):
            return qs.restrict(request.user, 'view')
        def get_total(qs):
            return qs_restrict(qs).count()
        def get_service(qs):
            qs = qs.values('asn', 'asn__number').annotate(Count('asn')).order_by()
            return qs_restrict(qs)        
        
        def get_stats():
            return { 
                'total_services': get_total(qs),
                'customerservice': get_service(qs)
            }
        
        stats['stats'] = get_stats()
        stats['active_tab'] = 'customerconnection'
        return stats

class CustomerConnectionEndpointView(generic.ObjectView):
    template_name = 'ixservices/customerconnection/customerconnectionendpoint.html'
    queryset = CustomerConnectionEndpoint.objects.all()


class ConnectionCustomerConnectionEndpointsView(generic.ObjectView):
    queryset = CustomerConnection.objects.all()
    template_name = 'ixservices/customerconnection/customerconnectionendpoints.html'

    def get_extra_context(self, request, instance):
        content = super().get_extra_context(request, instance)
        endpoints = instance.customerconnectionendpoint.restrict(request.user, 'view').prefetch_related(
            # Prefetch('ip_addresses', queryset=IPAddress.objects.restrict(request.user)),
            # Prefetch('member_interfaces', queryset=Interface.objects.restrict(request.user)),
            'interface', 'frontport', 'rearport',
        )
        endpoints_table = tables.ConnectionCustomerConnectionEndpointTable(
            data=endpoints,
            user=request.user
        )
        if request.user.has_perm('ixservices.change_customerconnectionendpoint') or request.user.has_perm('ixservices.delete_customerconnectionendpoint'):
            endpoints_table.columns.show('pk')
        paginate_table(endpoints_table, request)

        content['endpoints_table'] = endpoints_table
        content['active_tab'] = 'customerconnectionendpoints'
        return content


#### edit views
class IXEditView(generic.ObjectEditView):
    queryset = IX.objects.all()
    model_form = forms.IXForm

class ASEditView(generic.ObjectEditView):
    queryset = AS.objects.all()
    model_form = forms.ASForm

class TagEditView(generic.ObjectEditView):
    queryset = ServiceTag.objects.all()
    model_form = forms.TagForm

class ServiceTagDomainEditView(generic.ObjectEditView):
    queryset = ServiceTagDomain.objects.all()
    model_form = forms.ServiceTagDomainForm


class IPv4AddressEditView(generic.ObjectEditView):
    queryset = IPv4Address.objects.all()
    model_form = forms.IPv4AddressForm

class IPv6AddressEditView(generic.ObjectEditView):
    queryset = IPv6Address.objects.all()
    model_form = forms.IPv6AddressForm

class MACAddressEditView(generic.ObjectEditView):
    queryset = MACAddress.objects.all()
    model_form = forms.MACAddressForm

### services editviews
class ServiceTypeEditView(generic.ObjectEditView):
    queryset = ServiceType.objects.all()
    model_form = forms.ServiceTypeForm

class ServiceEditView(generic.ObjectEditView):
    queryset = IXService.objects.all()
    model_form = forms.ServiceForm

class CustomerServiceEditView(generic.ObjectEditView):
    queryset = CustomerService.objects.all()
    model_form = forms.CustomerServiceForm


### connections editviews
class CustomerConnectionTypeEditView(generic.ObjectEditView):
    queryset = CustomerConnectionType.objects.all()
    model_form = forms.CustomerConnectionTypeForm

class CustomerConnectionEditView(generic.ObjectEditView):
    queryset = CustomerConnection.objects.all()
    model_form = forms.CustomerConnectionEditForm

class CustomerConnectionAddView(generic.ObjectEditView):
    queryset = CustomerConnection.objects.all()
    model_form = forms.CustomerConnectionForm

class CustomerConnectionEndpointEditView(generic.ObjectEditView):
    queryset = CustomerConnectionEndpoint.objects.all()
    model_form = forms.CustomerConnectionEndpointForm

class CustomerConnectionEndpointConnectView(generic.ObjectEditView):
    queryset = CustomerConnectionEndpoint.objects.all()
    template_name = 'ixservices/customerconnection/customerconnectionconnect.html'

    def dispatch(self, request, *args, **kwargs):
        # Set the model_form class based on the type of component being connected
        self.model_form = {
            'interface': forms.ConnectCustomerConnectionToInterfaceForm,
            'frontport': forms.ConnectCustomerConnectionToFrontportForm,
            'rearport': forms.ConnectCustomerConnectionToRearportForm,
        }[kwargs.get('termination_type')]

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        termination_model = kwargs.get('model')
        termination_pk = kwargs.get('customer_connection_id')
        termination_type_name = kwargs.get('termination_type')
        self.termination_type = ContentType.objects.get(model=termination_type_name)
        # Initialize CustomerConnection termination attributes
        connection_obj = termination_model.objects.get(pk=termination_pk)
        # obj.termination_type = self.termination_type

        # Parse initial data manually to avoid setting field values as lists
        initial_data = {k: request.GET[k] for k in request.GET}
        initial_data['customer_connection'] = connection_obj

        connected_device = connection_obj.connected_device
        # Set initial site and region based on device
        if connected_device and 'region' not in initial_data:
            initial_data['region'] = connected_device.site.region
        if connected_device and 'site' not in initial_data:
            initial_data['site'] = connected_device.site
        if connected_device and 'device' not in initial_data:
            initial_data['device'] = connected_device

        form = self.model_form(initial=initial_data)

        return render(request, self.template_name, {
            'obj': None,
            'obj_type': CustomerConnection._meta.verbose_name,
            'connection_obj': connection_obj,
            'termination_type': self.termination_type.name,
            'form': form,
            'return_url': self.get_return_url(request, connection_obj),
        })

### delete views
class IXDeleteView(generic.ObjectDeleteView):
    queryset = IX.objects.all()

class ASDeleteView(generic.ObjectDeleteView):
    queryset = AS.objects.all()

class TagDeleteView(generic.ObjectDeleteView):
    queryset = ServiceTag.objects.all()

class ServiceTagDomainDeleteView(generic.ObjectDeleteView):
    queryset = ServiceTagDomain.objects.all()

class IPv4AddressDeleteView(generic.ObjectDeleteView):
    queryset = IPv4Address.objects.all()

class IPv6AddressDeleteView(generic.ObjectDeleteView):
    queryset = IPv6Address.objects.all()

class MACAddressDeleteView(generic.ObjectDeleteView):
    queryset = MACAddress.objects.all()

## service delete views
class ServiceTypeDeleteView(generic.ObjectDeleteView):
    queryset = ServiceType.objects.all()

class ServiceDeleteView(generic.ObjectDeleteView):
    queryset = IXService.objects.all()

class CustomerServiceDeleteView(generic.ObjectDeleteView):
    queryset = CustomerService.objects.all()


## connection delete views
class CustomerConnectionTypeDeleteView(generic.ObjectDeleteView):
    queryset = CustomerConnectionType.objects.all()

class CustomerConnectionDeleteView(generic.ObjectDeleteView):
    queryset = CustomerConnection.objects.all()

class CustomerConnectionEndpointDeleteView(generic.ObjectDeleteView):
    queryset = CustomerConnectionEndpoint.objects.all()

'''
class ASNBulkImportView(generic.BulkImportView):
    queryset = Site.objects.all()
    model_form = forms.SiteCSVForm
    table = tables.SiteTable


class ASNBulkEditView(generic.BulkEditView):
    queryset = Site.objects.prefetch_related('region', 'tenant')
    filterset = filtersets.SiteFilterSet
    table = tables.SiteTable
    form = forms.SiteBulkEditForm


class ASNBulkDeleteView(generic.BulkDeleteView):
    queryset = Site.objects.prefetch_related('region', 'tenant')
    filterset = filtersets.SiteFilterSet
    table = tables.SiteTable
'''

           
## change logs

class CustomerConnectionObjectChangeLogView(views.ObjectChangeLogView):
    base_template = "ixservices/customerconnection/customerconnection.html"

class CustomerConnectionTypeObjectChangeLogView(views.ObjectChangeLogView):
    base_template = "ixservices/customerconnection/customerconnectiontype.html"

class CustomerConnectionEndpointObjectChangeLogView(views.ObjectChangeLogView):
    base_template = "ixservices/customerconnection/customerconnectiontype.html"


class ServiceObjectChangeLogView(views.ObjectChangeLogView):
    base_template = "ixservices/service/ixservice.html"

class ServiceTypeObjectChangeLogView(views.ObjectChangeLogView):
    base_template = "ixservices/service/servicetype.html"


class ServiceTagDomainObjectChangeLogView(views.ObjectChangeLogView):
    base_template = "ixservices/service/servicetagdomain.html"

class ServiceTagObjectChangeLogView(views.ObjectChangeLogView):
    base_template = "ixservices/service/servicetag.html"

class CustomerServiceObjectChangeLogView(views.ObjectChangeLogView):
    base_template = "ixservices/service/customerservice.html"
