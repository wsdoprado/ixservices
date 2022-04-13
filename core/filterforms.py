

from django import forms
from django.utils.translation import gettext as _

from utilities.forms import BootstrapMixin, StaticSelectMultiple, StaticSelect, BOOLEAN_WITH_BLANK_CHOICES
from extras.forms import CustomFieldModelFilterForm

from ixservices.ixservices.models import (AS, IX, ServiceTagDomain, ServiceTag, IPv4Address, IPv6Address, MACAddress,
                                          ServiceType, IXService, CustomerService, CustomerConnectionType,
                                          CustomerConnection, CustomerConnectionEndpoint)

from ixservices.ixservices.utils.status import TagStatusChoices, IPStatusChoices, TagDomainChoices
from ixservices.core.utils import DynamicModelMultipleChoiceField

#TODO: remover BootstrapMixin para atualizacao ver 3.1.1
class BaseFilterForm(CustomFieldModelFilterForm):
    model = None
    field_order = ['q']
    field_groups = [ ['q'] ]
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': _('All Fields')}),
        label=_('Search')
    )

    class Meta:
        abstract = True


### core filterforms ###

class IXFilterForm(BaseFilterForm):
    model = IX
    
class ASFilterForm(BaseFilterForm):
    model = AS

    field_order = ['q',  'customerservice__service__ix']
    field_groups = [ ['q'], [ 'customerservice__service__ix']]

    customerservice__service__ix = DynamicModelMultipleChoiceField(
        queryset=IX.objects.all(),
        required=False,
        label=_('IX'),
        fetch_trigger='open'
    )

class TagFilterForm(BaseFilterForm):
    model = ServiceTag
    field_order = ['q',  'status', 'tag_domain']
    field_groups = [ ['q'], [ 'status'], ['tag_domain']]
    status = forms.MultipleChoiceField(
        choices=TagStatusChoices().CHOICES,
        required=False,
        widget=StaticSelectMultiple(),
    )
    tag_domain = DynamicModelMultipleChoiceField(
        queryset=ServiceTagDomain.objects.all(),
        required=False,
        label=_('ServiceTagDomain'),
        fetch_trigger='open'
    )
    '''
    ix_id = DynamicModelMultipleChoiceField(
        queryset=IX.objects.all(),
        required=False,
        label=_('IX'),
        fetch_trigger='open'
    )'''

class ServiceTagDomainFilterForm(BaseFilterForm):
    model = ServiceTagDomain
    field_order = ['q', 'domain_type', 'ix']
    field_groups = [ ['q'], ['domain_type'], ['ix'] ]

    domain_type = forms.MultipleChoiceField(
        choices=TagDomainChoices().CHOICES,
        required=False,
        widget=StaticSelectMultiple(),
    )

    ix = DynamicModelMultipleChoiceField(
        queryset=IX.objects.all(),
        required=False,
        label=_('IX'),
        fetch_trigger='open'
    )


class IPv4AddressFilterForm(BaseFilterForm):
    model = IPv4Address
    
    field_order = ['q',  'is_allocated']
    field_groups = [ ['q'], [ 'is_allocated']]

    is_allocated = forms.NullBooleanField(
        required=False,
        label='IS ALLOCATED',
        widget=StaticSelect(
            choices=BOOLEAN_WITH_BLANK_CHOICES
        )
    )

    

class IPv6AddressFilterForm(BaseFilterForm):
    model = IPv6Address

    field_order = ['q',  'is_allocated']
    field_groups = [ ['q'], [ 'is_allocated']]

    is_allocated = forms.NullBooleanField(
        required=False,
        label='IS ALLOCATED',
        widget=StaticSelect(
            choices=BOOLEAN_WITH_BLANK_CHOICES
        )
    )

class MACAddressFilterForm(BaseFilterForm):
    model = MACAddress


### service filterforms ####
class ServiceTypeFilterForm(BaseFilterForm):
    model = ServiceType
  
class ServiceFilterForm(BaseFilterForm):
    model = IXService

class CustomerServiceFilterForm(BaseFilterForm):
    model = CustomerService

    field_order = ['q', 'service__service_type']
    field_groups = [ ['q'], ['service__service_type'] ]

    
    service__service_type = DynamicModelMultipleChoiceField(
        queryset=ServiceType.objects.all(),
        required=False,
        label=_('Service Type'),
        fetch_trigger='open'
    )

    service__ix = DynamicModelMultipleChoiceField(
        queryset=IX.objects.all(),
        required=False,
        label=_('IX'),
        fetch_trigger='open'
    )

    connection = DynamicModelMultipleChoiceField(
        queryset=CustomerConnection.objects.all(),
        required=False,
        label=_('CustomerConnection'),
        fetch_trigger='open'
    )

    asn = DynamicModelMultipleChoiceField(
        queryset=AS.objects.all(),
        required=False,
        label=_('ASN'),
        fetch_trigger='open'
    )

    tag_or_outer = DynamicModelMultipleChoiceField(
        queryset=ServiceTag.objects.all(),
        required=False,
        label=_('ServiceTag'),
        fetch_trigger='open'
    )


### connection filterforms ####
class CustomerConnectionTypeFilterForm(BaseFilterForm):
    model = CustomerConnectionType

class CustomerConnectionFilterForm(BaseFilterForm):
    model = CustomerConnection

    field_order = ['q', 'connection_type']
    field_groups = [ ['q'], ['connection_type'] ]

    connection_type = DynamicModelMultipleChoiceField(
        queryset=CustomerConnectionType.objects.all(),
        required=False,
        label=_('CustomerConnectionType'),
        fetch_trigger='open'
    )

    is_lag = forms.NullBooleanField(
        required=False,
        widget=StaticSelect(
            choices=BOOLEAN_WITH_BLANK_CHOICES
        )
    )

class CustomerConnectionEndpointFilterForm(BaseFilterForm):
    model = CustomerConnectionEndpoint

    field_order = ['q', 'customer_connection']
    field_groups = [ ['q'], ['customer_connection'] ]

    customer_connection = DynamicModelMultipleChoiceField(
        queryset=CustomerConnection.objects.all(),
        required=False,
        label=_('CustomerConnection'),
        fetch_trigger='open'
    )