from rest_framework import serializers
from ixservices.ixservices.models import (ASN, IX, ServiceTag, IPv4Address, IPv6Address, MACAddress, CustomerConnectionEndpoint, 
                                          CustomerConnection, CustomerConnectionType, ServiceType, Service, CustomerService)

# netbox imports
from netbox.api.serializers import PrimaryModelSerializer, BaseModelSerializer, WritableNestedSerializer
# serializers especificos que permite insercao/update dentro de um modelo

class BaseModelSerializer(serializers.ModelSerializer):
    display = serializers.SerializerMethodField(read_only=True)

    def get_display(self, obj):
        return str(obj)

class NestedASNSerializer(WritableNestedSerializer):
    class Meta:
        model = ASN
        fields = ('created', 'last_updated', 'number', 'description')


class NestedIXSerializer(WritableNestedSerializer):
    class Meta:
        model = IX
        fields = ('created', 'last_updated', 'code', 'shortname',
                  'fullname', 'ipv4_prefix', 'ipv6_prefix',
                  'management_prefix', 'description', 'tags_policy',)
                  

class NestedIXTagSerializer(WritableNestedSerializer):
    ix_fullname = serializers.CharField(source='ix.fullname')
    class Meta:
        model = ServiceTag
        fields = ('created', 'last_updated', 'tag', 'ix', 'ix_fullname', 'tag_domain', 'status',)


class NestedIPv4AddressSerializer(WritableNestedSerializer):
    class Meta:
        model = IPv4Address
        fields = ('created', 'last_updated', 'ix', 'address', 'reverse_dns',)


class NestedIPv6AddressSerializer(WritableNestedSerializer):
    class Meta:
        model = IPv6Address
        fields = ('created', 'last_updated', 'description', 'ix', 'address', 'reverse_dns',)


class NestedMACAddressSerializer(WritableNestedSerializer):
    class Meta:
        model = MACAddress
        fields = ('created', 'last_updated', 'address',)


class NestedCustomerConnectionEndpointSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomerConnectionEndpoint
        fields = ('created', 'last_updated', 'customer_connection', 'configured_capacity', 'interface', 'frontport', 'rearport', 'port_name', 'switch_ip', 'dio_position', 'dio_pix')

class NestedCustomerConnectionTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomerConnectionType
        fields = ('created', 'last_updated', 'connection_name', 'connection_type')

class NestedCustomerConnectionSerializer(BaseModelSerializer):

    customerconnectionendpoints = serializers.SerializerMethodField('_get_connection_endpoints')
    connection_type = CustomerConnectionTypeSerializer()
    asn = ASNSerializer()

    class Meta:
        model = CustomerConnection
        fields = ('id', 'created', 'last_updated', 'display', 'name', 'is_lag', 'asn', 'ticket', 'connection_type', 
                  'customerconnectionendpoints',)

    def _get_connection_endpoints(self, instance):
        cc_endpoints = instance.customerconnectionendpoint.all() 
        return [ CustomerConnectionEndpointSerializer(item).data for item in cc_endpoints ]


class NestedServiceTypeSerializer(WritableNestedSerializer):
    class Meta:
        model = ServiceType
        fields = ('created', 'last_updated', 'name', 'num_clients',)


class NestedIXServiceSerializer(WritableNestedSerializer):
    service_type = NestedServiceTypeSerializer()
    ix = NestedIXSerializer()
    class Meta:
        model = Service
        fields = ('created', 'last_updated', 'service_type', 'name', 'label', 'ix',)






