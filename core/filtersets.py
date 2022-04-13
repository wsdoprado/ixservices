
import django_filters
from django.db.models import Q

from netbox.filtersets import PrimaryModelFilterSet
from utilities.filters import TreeNodeMultipleChoiceFilter

from ixservices.ixservices.models import (AS, IX, ServiceTagDomain, ServiceTag, IPv4Address, IPv6Address, MACAddress,
                                          ServiceType, IXService, CustomerService, CustomerConnectionType,
                                          CustomerConnection, CustomerConnectionEndpoint)

from ixservices.ixservices.utils.status import TagStatusChoices, IPStatusChoices, TagDomainChoices


class BaseFilterSet(PrimaryModelFilterSet):
    q = django_filters.CharFilter(method='search', label='Search',)
    class Meta:
        model = None
        abstract = True
        fields = [ 'id' ]
        q_fields = ['id', 'description__icontains']

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (Q( **{ self.Meta.q_fields[1] : value }))
        try:
            qs_filter |= Q(**{ self.Meta.q_fields[0] : int(value.strip()) })
        except ValueError as ve:
            print(ve)
            pass
        # print(qs_filter)
        return queryset.filter(qs_filter)

### core filtersets ###
class IXFilterSet(BaseFilterSet):
    code = django_filters.CharFilter(method='code', label='Code',)

    class Meta:
        model = IX
        fields = [ 'id', 'code', 'fullname', 'ipv4_prefix', 'ipv6_prefix']
        q_fields = ['id', 'code__icontains']

    def search(self, queryset, name, value):
        return super().search(queryset, name, value)


class ASFilterSet(PrimaryModelFilterSet):
    number = django_filters.CharFilter(method='number', label='Number',)

    customerservice__service__ix = django_filters.ModelMultipleChoiceFilter(
        queryset=IX.objects.all(),
        label='IX (ID)',
    )

    class Meta:
        model = AS
        fields = [ 'id', 'number', 'description',]
        q_fields = ['number', 'description__icontains']

    def search(self, queryset, name, value):
        return super().search(queryset, name, value)


class TagFilterSet(BaseFilterSet):
    tag = django_filters.CharFilter(method='tag', label='Tag',)
    status = django_filters.MultipleChoiceFilter(
        choices=TagStatusChoices().CHOICES,
        null_value=None
    )
    tag_domain = django_filters.ModelMultipleChoiceFilter(
        queryset=ServiceTagDomain.objects.all(),
        label='ServiceTagDomain (ID)',
    )
    ix_id = django_filters.ModelMultipleChoiceFilter(
        queryset=IX.objects.all(),
        label='IX (ID)',
    )

    # ix_id = django_filters.CharFilter(method='tags_by_ix', label='IX',)

    class Meta:
        model = ServiceTag
        fields = [ 'id', 'tag', 'description']
        q_fields = ['tag', 'ix__code__icontains']

    def search(self, queryset, name, value):
        return super().search(queryset, name, value)

    def tags_by_ix(self, queryset, name, value):
        ix = None
        if not value.strip():
            return queryset
        try:
            ix = IX.objects.get(pk=int(value.strip()))
        except Exception:
            pass
        return queryset.filter(ix=ix) if ix else queryset



class ServiceTagDomainFilterSet(BaseFilterSet):
    # tag = django_filters.CharFilter(method='tag', label='Tag',)
    ix = django_filters.ModelMultipleChoiceFilter(
        queryset=IX.objects.all(),
        label='IX (ID)',
    )
    domain_type = django_filters.MultipleChoiceFilter(
        choices=TagDomainChoices().CHOICES,
        null_value=None
    )

    class Meta:
        model = ServiceTagDomain
        fields = [ 'id', 'domain_type', 'description']
        q_fields = ['domain_type', 'ix__code__icontains']

    def search(self, queryset, name, value):
        return super().search(queryset, name, value)
       


class IPv4AddressFilterSet(BaseFilterSet):
    address = django_filters.CharFilter(method='address', label='Address',)   
    is_allocated = django_filters.BooleanFilter(
        method='_is_allocated',
        label='IS ALLOCATED',
    )        
    ix_id = django_filters.ModelMultipleChoiceFilter(
        queryset=IX.objects.all(),
        label='IX (ID)',
    )

    class Meta:
        model = IPv4Address
        fields = [ 'id', 'address', 'description',]
        q_fields = ['id', 'address__icontains']

    def search(self, queryset, name, value):
        return super().search(queryset, name, value)
   
    def _is_allocated(self, queryset, name, value):
        try:
           return queryset.filter(customerservice__isnull=(not value))
        except Exception as e:
            print(e)
            pass
        return queryset
    


class IPv6AddressFilterSet(BaseFilterSet):
    address = django_filters.CharFilter(method='address', label='Address',)
    is_allocated = django_filters.BooleanFilter(
        method='_is_allocated',
        label='IS ALLOCATED',
    )    
    ix_id = django_filters.ModelMultipleChoiceFilter(
        queryset=IX.objects.all(),
        label='IX (ID)',
    )

    class Meta:
        model = IPv6Address
        fields = [ 'id', 'address', 'description',]
        q_fields = ['id', 'address__icontains']

    def search(self, queryset, name, value):
        return super().search(queryset, name, value)

    def _is_allocated(self, queryset, name, value):
        try:
           return queryset.filter(customerservice__isnull=(not value))
        except Exception as e:
            print(e)
            pass
        return queryset


class MACAddressFilterSet(BaseFilterSet):
    address = django_filters.CharFilter(method='address', label='Address',)

    class Meta:
        model = MACAddress
        fields = [ 'id', 'address', 'description',]
        q_fields = ['id', 'address__icontains']

    def search(self, queryset, name, value):
        return super().search(queryset, name, value)

### service filtersets ###
class ServiceTypeFilterSet(BaseFilterSet):
    name = django_filters.CharFilter(method='name', label='Name',)

    class Meta:
        model = ServiceType
        fields = [ 'id', 'name', 'description',]
        q_fields = ['id', 'name__icontains']

    def search(self, queryset, name, value):
        return super().search(queryset, name, value)


class ServiceFilterSet(BaseFilterSet):
    name = django_filters.CharFilter(method='name', label='Name',)
    ix_id = django_filters.ModelMultipleChoiceFilter(
        queryset=IX.objects.all(),
        label='IX (ID)',
    )

    class Meta:
        model = IXService
        fields = [ 'id', 'name', 'label', 'description',]
        q_fields = ['id', 'name__icontains']

    def search(self, queryset, name, value):
        return super().search(queryset, name, value)

class CustomerServiceFilterSet(BaseFilterSet):
    # name = django_filters.CharFilter(method='name', label='Name',)

    service__service_type = django_filters.ModelMultipleChoiceFilter(
        queryset=ServiceType.objects.all(),
        label='ServiceType (ID)',
    )

    service__ix = django_filters.ModelMultipleChoiceFilter(
        queryset=IX.objects.all(),
        label='IX (ID)',
    )

    connection = django_filters.ModelMultipleChoiceFilter(
        queryset=CustomerConnection.objects.all(),
        label='CustomerConnection (ID)',
    )

    asn = django_filters.ModelMultipleChoiceFilter(
        queryset=AS.objects.all(),
        label='ASN (ID)',
    )

    tag_or_outer = django_filters.ModelMultipleChoiceFilter(
        queryset=ServiceTag.objects.all(),
        label='ServiceTag (ID)',
    )

    class Meta:
        model = CustomerService
        fields = [ 'id', 'asn__number', 'service', 'description',]
        q_fields = ['asn__number', 'service__name__icontains']

    def search(self, queryset, name, value):
        return super().search(queryset, name, value)


### connection filtersets ###
class CustomerConnectionTypeFilterSet(BaseFilterSet):
    connection_name = django_filters.CharFilter(method='connection_name', label='connection_name',)

    class Meta:
        model = CustomerConnectionType
        fields = [ 'id', 'connection_name', 'description',]
        q_fields = ['id', 'connection_name__icontains']

    def search(self, queryset, name, value):
        return super().search(queryset, name, value)

class CustomerConnectionFilterSet(BaseFilterSet):
    
    connection_type = django_filters.ModelMultipleChoiceFilter(
        queryset=CustomerConnectionType.objects.all(),
        label='CustomerConnectionType (ID)',
    )

    class Meta:
        model = CustomerConnection
        fields = [ 'id', 'name', 'description', 'is_lag']
        q_fields = ['id', 'name__icontains']

    def search(self, queryset, name, value):
        return super().search(queryset, name, value)


class CustomerConnectionEndpointFilterSet(BaseFilterSet):
    # name = django_filters.CharFilter(method='name', label='name',)

    customer_connection_id = django_filters.ModelMultipleChoiceFilter(
        queryset=CustomerConnection.objects.all(),
        label='CustomerConnection (ID)',
    )

    class Meta:
        model = CustomerConnectionEndpoint
        fields = [ 'id', 'customer_connection', 'description',]
        q_fields = ['id', 'customer_connection__connection_name__icontains']

    def search(self, queryset, name, value):
        return super().search(queryset, name, value)

        