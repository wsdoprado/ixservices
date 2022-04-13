from django.utils.translation import gettext as _
from django import forms
from django.db.models import Q

from utilities.forms import BootstrapMixin
from utilities.forms import SlugField, APISelect, StaticSelect, BOOLEAN_WITH_BLANK_CHOICES
from extras.forms import CustomFieldModelForm

from ixservices.ixservices.models import (AS, IX, ServiceTagDomain, ServiceTag, IPv4Address, IPv6Address, MACAddress,
                                          ServiceType, IXService, CustomerService, CustomerConnectionType,
                                          CustomerConnection, CustomerConnectionEndpoint)

from ixservices.core.utils import DynamicModelChoiceField, DynamicModelMultipleChoiceField


## import from netbox models
from dcim.models import Region, Site, Device, Interface, FrontPort, RearPort 

#TODO: remover BootstrapMixin para atualizacao ver 3.1.1
class BaseForm(CustomFieldModelForm):
    pass

class IXForm(BaseForm):   
    # slug = SlugField()  
    class Meta:
        model = IX
        fields = [ 'region', 'code', 'shortname', 'fullname', 'ipv4_prefix', 
                    'ipv6_prefix', 'management_prefix', 'description', 'create_ips', 'create_tags']
        fieldsets = (
            ('IX', ('region', 'code', 'shortname', 'fullname', 'ipv4_prefix', 
                    'ipv6_prefix', 'management_prefix', 'description', 'create_ips', 'create_tags',)),
        )
        help_texts = {
            'code': "IX Code",
            'create_ips': 'Create IPv4 and IPv6 range based on prefixes',
            'create_tags': 'Generate all Tags in IX domain'
        }

class ASForm(BaseForm):   
    # slug = SlugField()  
    class Meta:
        model = AS
        fields = [ 'number', 'description', ]
        fieldsets = (
            ('AS', ('number', 'description',)),
        )
        help_texts = {
            'number': "Autonomous System Number",
        }


class TagForm(BaseForm):   
    # slug = SlugField()  
    ix = DynamicModelChoiceField(
        queryset=IX.objects.all(),
        required=False
    )

    region = DynamicModelChoiceField(
        queryset=Region.objects.all(),
        label='Region',
        initial_params={
            'sites': '$site'
        },
        required=False
    )
    site = DynamicModelChoiceField(
        queryset=Site.objects.all(),
        label='Site',
        required=False,
        query_params={
            'region_id': '$region',
        }
    )
    device = DynamicModelChoiceField(
        queryset=Device.objects.all(),
        label='Device',
        required=False,
        query_params={
            'site_id': '$site',
        }
    )

    tag_domain = DynamicModelChoiceField(
        queryset=ServiceTagDomain.objects.all(),
        label='ServiceTagDomain',
        required=False,
        query_params={
            'device_id': '$device',
        }
    )

    class Meta:
        model = ServiceTag
        fields = [ 'tag', 'status', 'ix', 'tag_domain', 'description', ]
        fieldsets = (
            ('Tag', ('tag', 'status', 'ix', 'description',)),
            ('TagDomain', ('region', 'site', 'device', 'tag_domain',)),
        )
        help_texts = {}


class ServiceTagDomainForm(BaseForm):   
    # slug = SlugField()  
    ix = DynamicModelChoiceField(
        queryset=IX.objects.all(),
        required=False
    )

    region = DynamicModelChoiceField(
        queryset=Region.objects.all(),
        label='Region',
        initial_params={
            'sites': '$site'
        },
        required=False
    )
    site = DynamicModelChoiceField(
        queryset=Site.objects.all(),
        label='Site',
        required=False,
        query_params={
            'region_id': '$region',
        }
    )
    device = DynamicModelChoiceField(
        queryset=Device.objects.all(),
        label='Device',
        required=False,
        query_params={
            'site_id': '$site',
        }
    )
    interface = DynamicModelChoiceField(
        queryset=Interface.objects.all(),
        # disabled_indicator='_occupied',
        required=False,
        query_params={
            'device_id': '$device',
            'type': 'lag',
        }
    ) 


    class Meta:
        model = ServiceTagDomain
        fields = [ 'ix', 'domain_type', 'device', 'interface', 'description']
        fieldsets = (
            ('ServiceTagDomain', ('ix', 'domain_type', 'description',)),
            ('Device', ('region', 'site', 'device', 'interface')),
        )
        help_texts = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['interface'].queryset = Interface.objects.filter(type="lag")


class IPv4AddressForm(BaseForm):   
    # slug = SlugField()  
    ix = DynamicModelChoiceField(
        queryset=IX.objects.all(),
        required=False
    )
    class Meta:
        model = IPv4Address
        fields = [ 'address', 'reverse_dns', 'ix', 'description', ]
        fieldsets = (
            ('IPv4Address', ('address', 'reverse_dns', 'ix', 'description',)),
        )
        help_texts = {}


class IPv6AddressForm(BaseForm):   
    # slug = SlugField()  
    ix = DynamicModelChoiceField(
        queryset=IX.objects.all(),
        required=False
    )
    class Meta:
        model = IPv6Address
        fields = [ 'address', 'reverse_dns', 'ix', 'description', ]
        fieldsets = (
            ('IPv6Address', ('address', 'reverse_dns', 'ix', 'description',)),
        )
        help_texts = {}


class MACAddressForm(BaseForm):   
    # slug = SlugField()  
    class Meta:
        model = MACAddress
        fields = [ 'address', 'description', ]
        fieldsets = (
            ('MACAddress', ('address',  'description',)),
        )
        help_texts = {}


### service forms ###

class ServiceTypeForm(BaseForm):   
    # slug = SlugField()  
    class Meta:
        model = ServiceType
        fields = [ 'name', 'num_clients', 'description', ]
        fieldsets = (
            ('ServiceType', ('name',  'num_clients', 'description',)),
        )
        help_texts = {}


class ServiceForm(BaseForm):   
    # slug = SlugField()  
    ix = DynamicModelChoiceField(
        queryset=IX.objects.all(),
        required=False
    )
    class Meta:
        model = IXService
        fields = [ 'name', 'label', 'service_type', 'ix', 'description', ]
        fieldsets = (
            ('Service', ('name', 'label', 'service_type', 'ix', 'description',)),
        )
        help_texts = {}


class CustomerServiceForm(BaseForm):  

    # slug = SlugField()  
    asn = DynamicModelChoiceField(
        queryset=AS.objects.all(),
        # required=False
    )
    ix = DynamicModelChoiceField(
        queryset=IX.objects.all(),
        query_params={
            'region_id': '$region',
        },
        required=False
    )
    mlpav4_address = DynamicModelChoiceField(
        queryset=IPv4Address.objects.all(),
        disabled_indicator='is_allocated',
        query_params={
            'ix_id': '$ix',
        },
        required=False
    )
    mlpav6_address = DynamicModelChoiceField(
        queryset=IPv6Address.objects.all(),
        disabled_indicator='is_allocated',
        query_params={
            'ix_id': '$ix',
        },
        required=False
    )

    tag_domain = DynamicModelChoiceField(
        queryset=ServiceTagDomain.objects.all(),
        query_params={
            'ix': '$ix',
        },
        required=False
    )

    tag_or_outer = DynamicModelChoiceField(
        queryset=ServiceTag.objects.all(),
        query_params={
            'tag_domain': '$tag_domain',
        },
        required=False
    )
    mac_address = DynamicModelMultipleChoiceField(
        queryset=MACAddress.objects.all(),
        required=False,
        label=_('MACAddress'),
        fetch_trigger='open'
    )
    service = DynamicModelChoiceField(
        queryset=IXService.objects.all(),
        query_params={
            'ix_id': '$ix',
        }
        # required=False
    )
    
    connection = DynamicModelChoiceField(
        queryset=CustomerConnection.objects.all(),
        # disabled_indicator='connected_device_id',
        # required=False
    ) 

    class Meta:
        model = CustomerService
        fields = [ 'asn', 'ix','service', 'connection', 'mac_address', 'mlpav4_address', 'mlpav6_address', 
                     'tag_or_outer', 'inner_tag', 'ticket', 'description']
        fieldsets = (
             ('Connection', ('connection',)),
             ('ASN/Service', ('ix', 'service', 'asn')),
             ('Tags', ('tag_domain', 'tag_or_outer', 'inner_tag',)),
             ('Address', ('mlpav4_address', 'mlpav6_address', 'mac_address',)),
             ('Aditional information', ('ticket', 'description',)),
        )
        help_texts = {}

    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['connection'].queryset = self.fields['connection'].queryset.filter(
            Q(customerconnectionendpoint__interface__isnull=False) | Q(customerconnectionendpoint__rearport__isnull=False) | Q(customerconnectionendpoint__frontport__isnull=False)        
        ).distinct()


        if self.initial.get('connection'):
            try:
               self.initial['ix'] =  CustomerConnection.objects.get(
                   pk=self.initial['connection']
                ).connected_device.site.region.ix.first().pk
            except Exception as e:
                print(e)
                pass

        if hasattr(self.instance, 'connection'):
            try:
               self.initial['ix'] =  self.instance.connection.connected_device.site.region.ix.first().pk
            except Exception as e:
                print(e)
                pass




### connection forms ###

class CustomerConnectionTypeForm(BaseForm):   
    # slug = SlugField()  
    class Meta:
        model = CustomerConnectionType
        fields = [ 'connection_name', 'connection_type', 'description', ]
        fieldsets = (
            ('CustomerConnectionType', ('connection_name', 'connection_type', 'description',)),
        )
        help_texts = {}


class CustomerConnectionForm(BaseForm):   
    # slug = SlugField()  

    # region = DynamicModelChoiceField(
    #     required=False,
    #     queryset=Region.objects.all(),
    #     initial_params={
    #         'sites': '$site'
    #     }
    # )

    # site = DynamicModelChoiceField(
    #     required=False,
    #     queryset=Site.objects.all(),
    #     query_params={
    #         'region_id': '$region',
    #     }
    # )

    # device = DynamicModelChoiceField(
    #     # required=False,
    #     queryset=Device.objects.all(),
    #     help_text="Check if Connection name is associated with a device already",
    #     # to_field_name='name',
    #     query_params={
    #         'site_id': '$site',
    #     }
    # )

    asn = DynamicModelChoiceField(
        queryset=AS.objects.all(),
        # required=False
    )

    name = forms.CharField(
        label='Name or Lag name',
        # required=False,
        help_text="Connection name will be displayed as [ASN]-[Lag name]-[Device]",
    )

    tag_domain = DynamicModelChoiceField(
        queryset=ServiceTagDomain.objects.all(),
        # required=False
    )

    def clean_name(self):
        cl_data = self.cleaned_data
        asn, name = cl_data['asn'], cl_data['name']
        if name is None:
            # CustomerConnection.objects.filter(name=name).first()
            raise forms.ValidationError(
                f"CustomerConnection {name} cannot be empty."
            )
        # check connectons already created and related to device
        # if CustomerConnection.objects.filter(
        #       Q(asn=asn, name=name, customerconnectionendpoint__rearport__device=device)
        #     | Q(asn=asn, name=name, customerconnectionendpoint__frontport__device=device)
        #     | Q(asn=asn, name=name, customerconnectionendpoint__interface__device=device)
        #     ).first():
        #     raise forms.ValidationError(
        #         f"CustomerConnection [{asn}]-[{name}]-[{device}] already exist."
        #     )
        return name

    '''
    name = forms.CharField(
        required=False,
        help_text="Name",
        widget=APISelect(
            api_url='/plugins/ixservices/ixservices/api/select/customerconnectionname/{{asn}}/?device={{device}}'
        )
    )
    '''

    class Meta:
        model = CustomerConnection
        fields = [ 'asn', 'name', 'is_lag', 'connection_type', 'tag_domain', 'ticket', 'description', ]
        fieldsets = (
            ('CustomerConnection', ('asn', 'name', 'is_lag', 'connection_type', 'tag_domain', 'ticket', 'description',)),
           # ('Device', ('region', 'site', 'device',)),
        )
        help_texts = {}


class CustomerConnectionEditForm(BaseForm):   
    # slug = SlugField()  
    asn = DynamicModelChoiceField(
        queryset=AS.objects.all(),
        # required=False
    )

    name = forms.CharField(
        label='Name or Lag name',
        # required=False,
        help_text="Connection name will be displayed as [ASN]-[Lag name]-[Device]",
    )

    tag_domain = DynamicModelChoiceField(
        queryset=ServiceTagDomain.objects.all(),
        # required=False
    )

    def clean_name(self):
        asn, name = self.cleaned_data['asn'], self.cleaned_data['name']
        if self.instance.pk:
            cc_endpoint = self.instance.customerconnectionendpoint.filter(
                Q(rearport__isnull=False) | Q(frontport__isnull=False) | Q(interface__isnull=False)
            ).first()
            device = (cc_endpoint.rearport or  cc_endpoint.frontport or 
                      cc_endpoint.interface).device if cc_endpoint else None
            if name is None:
                # CustomerConnection.objects.filter(name=name).first()
                raise forms.ValidationError(
                    f"CustomerConnection {name} cannot be empty."
                )
            # check connectons already created and related to device
            # if CustomerConnection.objects.exclude(pk=self.instance.pk).filter(
            #       Q(asn=asn, name=name, customerconnectionendpoint__rearport__device=device)
            #     | Q(asn=asn, name=name, customerconnectionendpoint__frontport__device=device)
            #     | Q(asn=asn, name=name, customerconnectionendpoint__interface__device=device)
            #     ).first():
            #     raise forms.ValidationError(
            #         f"CustomerConnection [{asn}]-[{name}]-[{device}] already exist."
            #     )
        return name


    class Meta:
        model = CustomerConnection
        fields = [ 'asn', 'name', 'is_lag', 'connection_type', 'tag_domain', 'ticket', 'description', ]
        fieldsets = (
            ('CustomerConnection', ('asn', 'name', 'is_lag', 'connection_type', 'tag_domain', 'ticket', 'description',)),
        )
        help_texts = {}

    

class CustomerConnectionEndpointForm(BaseForm):   
    # slug = SlugField()

    region = DynamicModelChoiceField(
        required=False,
        queryset=Region.objects.all(),
        initial_params={
            'sites': '$site'
        }
    )

    site = DynamicModelChoiceField(
        required=False,
        queryset=Site.objects.all(),
        query_params={
            'region_id': '$region',
        }
    )

    device = DynamicModelChoiceField(
        required=False,
        queryset=Device.objects.all(),
        # to_field_name='name',
        query_params={
            'site_id': '$site',
        }
    )

    is_lag = forms.NullBooleanField(
        required=False,
        widget=StaticSelect(
            choices=BOOLEAN_WITH_BLANK_CHOICES
        )
    )

    customer_connection = DynamicModelChoiceField(
        queryset=CustomerConnection.objects.all(),
        query_params={
            'is_lag': '$is_lag',
        }
        # required=False
    ) 
    interface = DynamicModelChoiceField(
        queryset=Interface.objects.all(),
        disabled_indicator='_occupied',
        required=False,
        query_params={
            'device_id': '$device',
        }
    ) 
    frontport = DynamicModelChoiceField(
        queryset=FrontPort.objects.all(),
        disabled_indicator='_occupied',
        required=False,
        query_params={
            'device_id': '$device',
        }
    ) 
    rearport = DynamicModelChoiceField(
        queryset=RearPort.objects.all(),
        disabled_indicator='_occupied',
        required=False,
        query_params={
            'device_id': '$device',
        }
    ) 
    class Meta:
        model = CustomerConnectionEndpoint
        fields = [ 'region', 'site', 'device','interface', 'frontport', 'rearport', 'is_lag', 'customer_connection', 'configured_capacity', 'interface', 'frontport', 'rearport', 'description', ]
        fieldsets = (            
            ('CustomerConnectionEndpoint', ('is_lag', 'customer_connection', 'configured_capacity', 'description',)),
            ('Device', ('region', 'site', 'device','interface', 'frontport', 'rearport')),
        )
        help_texts = {}

    
    def clean(self):
        cleaned_data = super().clean()
        obj_connect =  cleaned_data.get("rearport") or cleaned_data.get("frontport") \
                          or cleaned_data.get("interface")
        if obj_connect:
            obj_name = obj_connect._meta.verbose_name.title().lower()
            obj_connected = getattr(self.instance, obj_name, None)
            # validate if interface, rear or front device is not the same as connection
            obj_connection = cleaned_data.get("customer_connection")
            if obj_connection.connected_device and isinstance(obj_connect, Interface):
                if obj_connection.connected_device != obj_connect.device:
                   raise forms.ValidationError(_(f"{obj_connect.device} is not associated with CustomerConnection"))

            # validate if interface, rear or front is already connected
            # TODO: check fi verification for cable  '_occupied' field is necessary
            if self.instance.pk:
                if obj_connect and not obj_connected and obj_connect.mark_connected:
                    raise forms.ValidationError(_(f"{obj_name} is already mark_connected"))
                if obj_connect and obj_connected != obj_connect and obj_connect.mark_connected:
                    raise forms.ValidationError(_(f"{obj_name} is already mark_connected"))
            else:
                if obj_connect and obj_connect.mark_connected:
                    raise forms.ValidationError(_(f"{obj_name} is already mark_connected"))
                    
            
            


class ConnectCustomerConnectionToDeviceForm(BaseForm):
    """
    Base form for connecting a CustomerConnection to a Device component
    """
    region = DynamicModelChoiceField(
        queryset=Region.objects.all(),
        label='Region',
        initial_params={
            'sites': '$site'
        },
        required=False
    )
    site = DynamicModelChoiceField(
        queryset=Site.objects.all(),
        label='Site',
        required=False,
        query_params={
            'region_id': '$region',
        }
    )
    device = DynamicModelChoiceField(
        queryset=Device.objects.all(),
        label='Device',
        required=False,
        query_params={
            'site_id': '$site',
        }
    )
    customer_connection = DynamicModelChoiceField(
        queryset=CustomerConnection.objects.all(),
        # required=False
    ) 

    class Meta:
        abstract = True

    '''
    def clean_termination_id(self):
        # Return the PK rather than the object
        return getattr(self.cleaned_data['termination_id'], 'pk', None)
    '''
    
    
    def clean(self):
        cleaned_data = super().clean()
        obj_connect =  cleaned_data.get("rearport") or cleaned_data.get("frontport") \
                          or cleaned_data.get("interface")
        if obj_connect:
            obj_name = obj_connect._meta.verbose_name.title().lower()
            # obj_connected = getattr(self.instance, obj_name, None)
            # validate if interface, rear or front device is not the same as connection
            obj_connection = cleaned_data.get("customer_connection")
            if obj_connection.connected_device and obj_connection.connected_device != obj_connect.device:
                raise forms.ValidationError(_(f"{obj_connect.device} is not associated with CustomerConnection"))

            # validate if interface, rear or front is already connected
            if obj_connect and obj_connect.mark_connected:
                raise forms.ValidationError(_(f"{obj_name} is already mark_connected"))
    


class ConnectCustomerConnectionToInterfaceForm(ConnectCustomerConnectionToDeviceForm):

    interface = DynamicModelChoiceField(
        queryset=Interface.objects.all(),
        label='Name',
        disabled_indicator='_occupied',
        query_params={
            'device_id': '$device',
            'kind': 'physical',
        }
    )

    class Meta:
        model = CustomerConnectionEndpoint
        fields = [
            'region', 'site', 'device', 'customer_connection', 'configured_capacity', 'description','interface']
        widgets = {
            # 'status': StaticSelect,
        }    


class ConnectCustomerConnectionToFrontportForm(ConnectCustomerConnectionToDeviceForm):

    frontport = DynamicModelChoiceField(
        queryset=FrontPort.objects.all(),
        label='Name',
        disabled_indicator='_occupied',
        query_params={
            'device_id': '$device',
            'kind': 'physical',
        }
    )

    class Meta:
        model = CustomerConnectionEndpoint
        fields = [
            'region', 'site', 'device', 'customer_connection', 'configured_capacity', 'description','frontport']
        widgets = {
            # 'status': StaticSelect,
        }

class ConnectCustomerConnectionToRearportForm(ConnectCustomerConnectionToDeviceForm):

    rearport = DynamicModelChoiceField(
        queryset=RearPort.objects.all(),
        label='Name',
        disabled_indicator='_occupied',
        query_params={
            'device_id': '$device',
            'kind': 'physical',
        }
    )

    class Meta:
        model = CustomerConnectionEndpoint
        fields = [
            'region', 'site', 'device', 'customer_connection', 'configured_capacity', 'description','rearport']
        widgets = {
            # 'status': StaticSelect,
        }

