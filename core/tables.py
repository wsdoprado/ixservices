import django_tables2 as tables
from utilities.tables import BaseTable, ToggleColumn, ChoiceFieldColumn, LinkedCountColumn

from ixservices.ixservices.models import (AS, IX, ServiceTagDomain, ServiceTag, IPv4Address, IPv6Address, MACAddress,
                                          ServiceType, IXService, CustomerService, CustomerConnectionType,
                                          CustomerConnection, CustomerConnectionEndpoint)

from .template_code import ENDPOINT_BUTTONS, CONNECTION_BUTTONS, CONNECTIONENDPOINT_BUTTONS
from .utils import ButtonsColumn


def get_cabletermination_row_class(record):
    if record.mark_connected:
        return 'success'
    elif record.cable:
        return record.cable.get_status_class()
    return ''


def get_interface_state_attribute(record):
    """
    Get interface enabled state as string to attach to <tr/> DOM element.
    """
    if record.enabled:
        return "enabled"
    else:
        return "disabled"



class IXTable(BaseTable):
    pk = ToggleColumn()
    code = tables.Column(linkify=True)
    shortname = tables.Column(linkify=True)
    fullname = tables.Column(linkify=True)
    region = tables.Column(linkify=True)
    # ipv4_prefix = tables.Column(linkify=True)
    # ipv6_prefix = tables.Column(linkify=True)
    # description = tables.Column(linkify=True)   
    class Meta(BaseTable.Meta):
        model = IX
        fields = ('pk', 'code', 'shortname', 'fullname', 'ipv4_prefix', 'ipv6_prefix', 'region', 'description',)
        default_columns = ('pk', 'code', 'shortname', 'fullname', 'ipv4_prefix', 'ipv6_prefix', 'region')

class ASTable(BaseTable):
    pk = ToggleColumn()
    number = tables.Column(linkify=True)
    # description = tables.Column(linkify=True)   
    class Meta(BaseTable.Meta):
        model = AS
        fields = ('pk', 'number', 'description',)
        default_columns = ('pk', 'number', )


class TagTable(BaseTable):
    pk = ToggleColumn()
    tag = tables.Column(linkify=True)
    status = ChoiceFieldColumn()
    ix = tables.Column(linkify=True)
    tag_domain = tables.Column(linkify=True)

    customer_innertag_count = LinkedCountColumn(
        viewname='plugins:ixservices:customerservice_list',
        url_params={'tag_or_outer_id': 'pk'},
        verbose_name='InnerTags'
    )

    customerservice_count = LinkedCountColumn(
        viewname='plugins:ixservices:customerservice_list',
        url_params={'tag_or_outer': 'pk'},
        verbose_name='Services'
    )
    
    class Meta(BaseTable.Meta):
        model = ServiceTag
        fields = ('pk', 'tag', 'status', 'ix', 'tag_domain', 'customerservice_count', 'customer_innertag_count', 'description',)
        default_columns = ('pk', 'tag', 'status', 'ix', 'tag_domain', 'customerservice_count', 'customer_innertag_count',)


class ServiceTagDomainTable(BaseTable):
    pk = ToggleColumn()
    domain_type = tables.Column(linkify=True)
    ix = tables.Column(linkify=True)
    device = tables.Column(
        linkify=True,
        verbose_name='Device'
    )
    interface = tables.Column(
        linkify=True,
        verbose_name='Interface'
    )

    servicetags_count = LinkedCountColumn(
        viewname='plugins:ixservices:servicetag_list',
        url_params={'tag_domain': 'pk'},
        verbose_name='ServiceTags'
    )
    
    class Meta(BaseTable.Meta):
        model = ServiceTagDomain
        fields = ('pk', 'id', 'domain_type', 'ix', 'device', 'interface', 'servicetags_count', 'description',)
        default_columns = ('pk', 'id', 'domain_type', 'ix', 'device', 'interface', 'servicetags_count', )


class IPv4AddressTable(BaseTable):
    pk = ToggleColumn()
    address = tables.Column(linkify=True)
    ix = tables.Column(linkify=True)
    class Meta(BaseTable.Meta):
        model = IPv4Address
        fields = ('pk', 'address', 'ix', 'status', 'description',)
        default_columns = ('pk', 'address', 'ix', 'status' )

class IPv6AddressTable(BaseTable):
    pk = ToggleColumn()
    address = tables.Column(linkify=True)
    ix = tables.Column(linkify=True)
    class Meta(BaseTable.Meta):
        model = IPv6Address
        fields = ('pk', 'address', 'ix', 'status', 'description',)
        default_columns = ('pk', 'address', 'ix', 'status' )

class MACAddressTable(BaseTable):
    pk = ToggleColumn()
    address = tables.Column(linkify=True)
    class Meta(BaseTable.Meta):
        model = MACAddress
        fields = ('pk', 'address', 'description',)
        default_columns = ('pk', 'address',)


### service tables ###

class ServiceTypeTable(BaseTable):
    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    class Meta(BaseTable.Meta):
        model = ServiceType
        fields = ('pk', 'name', 'description',)
        default_columns = ('pk', 'name', 'num_clients',)

class ServiceTable(BaseTable):
    pk = ToggleColumn()
    name = tables.Column(linkify=True)
    service_type = tables.Column(linkify=True)
    ix = tables.Column(linkify=True)
    class Meta(BaseTable.Meta):
        model = IXService
        fields = ('pk', 'name', 'label', 'service_type', 'ix', 'description',)
        default_columns = ('pk', 'name', 'label', 'service_type', 'ix',)

class CustomerServiceTable(BaseTable):
    pk = ToggleColumn()
    id = tables.Column(linkify=True)
    asn = tables.Column(linkify=True)
    service = tables.Column(linkify=True)
    connection = tables.Column(linkify=True)
    # connection__connected_device = tables.Column(linkify=True, verbose_name='Device')
    # connection__connected_device__site__region = tables.Column(linkify=True, verbose_name='Region')
    service_tag = tables.Column(verbose_name='OutterTag:InnerTag')   
   
    class Meta(BaseTable.Meta):
        model = CustomerService
        fields = ('pk', 'id', 'asn', 'service', 'service__ix', 'connection',
                  'connection__is_lag', 'connection__connection_type__connection_name', 'ticket', 'service_tag', 'description',)
        default_columns = ('pk', 'id', 'asn', 'service', 'service__ix', 'connection', 
                           'connection__is_lag', 'connection__connection_type__connection_name', 'ticket', 'service_tag')


### connection tables ###

class CustomerConnectionTypeTable(BaseTable):
    pk = ToggleColumn()
    connection_name = tables.Column(linkify=True)
    class Meta(BaseTable.Meta):
        model = CustomerConnectionType
        fields = ('pk', 'connection_name', 'connection_type', 'description',)
        default_columns = ('pk', 'connection_name', 'connection_type',)


class CustomerConnectionTable(BaseTable):
    pk = ToggleColumn()
    # full_name = tables.Column(linkify=True, verbose_name='Name')
    _name = tables.Column(linkify=True)
    # connection_type = tables.Column(linkify=True)
    asn = tables.Column(linkify=True)

    connected_device = tables.Column(linkify=True, verbose_name='Device')
    # connected_device__site__region = tables.Column(linkify=True, verbose_name='Region')

    customerconnectionendpoint_count = LinkedCountColumn(
        viewname='plugins:ixservices:customerconnectionendpoint_list',
        url_params={'customer_connection_id': 'pk'},
        verbose_name='Endpoints'
    )

    customerservice_count = LinkedCountColumn(
        viewname='plugins:ixservices:customerservice_list',
        url_params={'connection': 'pk'},
        verbose_name='Services'
    )

    tag_domain = tables.Column(linkify=True, verbose_name='ServiceTagDomain')

    actions = ButtonsColumn(
        model=CustomerConnection,
        buttons=('edit', 'delete'),
        prepend_template=CONNECTION_BUTTONS
    )

    class Meta(BaseTable.Meta):
        model = CustomerConnection
        fields = ('pk', '_name', 'asn', 'connection_type', 'connection_type__connection_name', 'is_lag', 
                  'customerconnectionendpoint_count', 'customerservice_count', 'connected_device', 'tag_domain', 'actions', 'description',)
        default_columns = ('pk', '_name', 'asn', 'connection_type__connection_name', 'is_lag', 
                  'customerconnectionendpoint_count', 'customerservice_count', 'connected_device', 'tag_domain', 'actions')


class CustomerConnectionEndpointTable(BaseTable):
    pk = ToggleColumn()
    id = tables.Column(linkify=True)
    customer_connection = tables.Column(linkify=True)

    device__site = tables.Column(
        linkify=True,
        verbose_name='Site'
    )

    device = tables.Column(
        linkify=True,
        verbose_name='Device'
    )
    interface = tables.Column(
        linkify=True,
        verbose_name='Interface'
    )
    frontport = tables.Column(
        linkify=True,
        verbose_name='Frontport'
    )
    rearport = tables.Column(
        linkify=True,
        verbose_name='Rearport'
    )
    actions = ButtonsColumn(
        model=CustomerConnectionEndpoint,
        buttons=('edit', 'delete'),
        prepend_template=CONNECTIONENDPOINT_BUTTONS
    )

    class Meta(BaseTable.Meta):
        model = CustomerConnectionEndpoint
        fields = ('pk', 'id', 'customer_connection', 'customer_connection__asn', 'configured_capacity', 'device', 'device__site',
                  'interface', 'frontport', 'rearport', 'actions', 'description',)
        default_columns = ('pk', 'id', 'customer_connection', 'customer_connection__asn', 'configured_capacity', 'device', 'device__site',
                  'interface', 'frontport', 'rearport', 'actions')



class ConnectionCustomerConnectionEndpointTable(BaseTable):
    '''
    name = tables.TemplateColumn(
        template_code='<i class="mdi mdi-{% if iface.mgmt_only %}wrench{% elif iface.is_lag %}drag-horizontal-variant'
                      '{% elif iface.is_virtual %}circle{% elif iface.is_wireless %}wifi{% else %}ethernet'
                      '{% endif %}"></i> <a href="{{ record.get_absolute_url }}">{{ value }}</a>',
        order_by=Accessor('_name'),
        attrs={'td': {'class': 'text-nowrap'}}
    )'''
    pk = ToggleColumn()
    id = tables.Column(linkify=True)
    device = tables.Column(
        linkify=True,
        verbose_name='Device'
    )
    device__site = tables.Column(
        linkify=True,
        verbose_name='Site'
    )
    interface = tables.Column(
        linkify=True,
        verbose_name='Interface'
    )
    frontport = tables.Column(
        linkify=True,
        verbose_name='Frontport'
    )
    rearport = tables.Column(
        linkify=True,
        verbose_name='Rearport'
    )
    actions = ButtonsColumn(
        model=CustomerConnectionEndpoint,
        buttons=('edit', 'delete'),
        prepend_template=CONNECTIONENDPOINT_BUTTONS
    )

    class Meta(BaseTable.Meta):
        model = CustomerConnectionEndpoint
        fields = (
            'pk', 'id', 'configured_capacity', 'device', 'device__site', 'interface', 'frontport', 'rearport', 'actions',
        )
        order_by = ('name',)
        default_columns = (
            'pk', 'id', 'configured_capacity', 'device', 'device__site', 'interface', 'frontport', 'rearport', 'actions',
        )
        '''
        row_attrs = {
            'class': get_cabletermination_row_class,
            'data-name': lambda record: record.name,
            'data-enabled': get_interface_state_attribute,
        }'''