from rest_framework import serializers
from ixservices.ixservices.models import (AS, IX, ServiceTagDomain, ServiceTag, IPv4Address, IPv6Address, MACAddress, CustomerConnectionEndpoint, 
                                          CustomerConnection, CustomerConnectionType, ServiceType, IXService, CustomerService)

from django.db import transaction

# netbox imports
from netbox.api.serializers import PrimaryModelSerializer, BaseModelSerializer, WritableNestedSerializer
from dcim.models import Device, Interface


class BaseModelSerializer(PrimaryModelSerializer):
    display = serializers.SerializerMethodField(read_only=True)

    def get_display(self, obj):
        return str(obj)

# serializers especificos que permite insercao/update dentro de um modelo


class NestedASSerializer(WritableNestedSerializer):
    class Meta:
        model = AS
        fields = ('id', 'display', 'created', 'last_updated', 'number', 'description')


class NestedIXSerializer(WritableNestedSerializer):
    class Meta:
        model = IX
        fields = ('id', 'display', 'created', 'last_updated', 'code', 'shortname',
                  'fullname', 'ipv4_prefix', 'ipv6_prefix',
                  'management_prefix', 'description', 'tags_policy',)
                  

class NestedServiceTagSerializer(WritableNestedSerializer):
    class Meta:
        model = ServiceTag
        fields = ('id', 'display', 'created', 'last_updated', 'tag', 'ix', 'tag_domain', 'status',)


class NestedIPv4AddressSerializer(WritableNestedSerializer):
    class Meta:
        model = IPv4Address
        fields = ('id', 'display', 'created', 'last_updated', 'ix', 'address', 'reverse_dns', 'is_allocated')


class NestedIPv6AddressSerializer(WritableNestedSerializer):
    class Meta:
        model = IPv6Address
        fields = ('id', 'display', 'created', 'last_updated', 'ix', 'address', 'reverse_dns', 'is_allocated')


class NestedMACAddressSerializer(WritableNestedSerializer):
    class Meta:
        model = MACAddress
        fields = ('id', 'display', 'created', 'display', 'last_updated', 'address',)


class NestedCustomerConnectionEndpointSerializer(WritableNestedSerializer):

    class Meta:
        model = CustomerConnectionEndpoint
        fields = ('id', 'display', 'created', 'last_updated', 'customer_connection', 'configured_capacity', 'interface', 'frontport', 'rearport', 'port_name', 'switch_ip', 'dio_position', 'dio_pix')

class NestedCustomerConnectionTypeSerializer(WritableNestedSerializer):

    class Meta:
        model = CustomerConnectionType
        fields = ('id', 'display', 'created', 'last_updated', 'connection_name', 'connection_type')

class NestedCustomerConnectionSerializer(WritableNestedSerializer):

    connection_type = NestedCustomerConnectionTypeSerializer()
    asn = NestedASSerializer()

    class Meta:
        model = CustomerConnection
        fields = ('id', 'display', 'created', 'last_updated', 'display', 'name', 'is_lag', 'asn', 'ticket', 'connection_type', 'connected_device_id')



class NestedServiceTypeSerializer(WritableNestedSerializer):
    class Meta:
        model = ServiceType
        fields = ('id', 'display', 'created', 'last_updated', 'name', 'num_clients',)


class NestedIXServiceSerializer(WritableNestedSerializer):
    service_type = NestedServiceTypeSerializer()
    ix = NestedIXSerializer()
    class Meta:
        model = IXService
        fields = ('id', 'display', 'created', 'last_updated', 'service_type', 'name', 'label', 'ix',)


##############################################################################################################################################

class ASSerializer(PrimaryModelSerializer):
    class Meta:
        model = AS
        fields = ('id', 'created', 'last_updated', 'number', 'description', 'is_exempt')


class IXSerializer(BaseModelSerializer):
    class Meta:
        model = IX
        fields = ('id', 'created', 'display', 'last_updated', 'region', 'code', 'shortname',
                  'fullname', 'ipv4_prefix', 'ipv6_prefix',
                  'management_prefix', 'description', 'tags_policy',)


class ServiceTagDomainSerializer(BaseModelSerializer):
    ix = NestedIXSerializer()
    #tags = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ServiceTagDomain
        fields = ('id', 'display', 'created', 'last_updated', 'ix', 'domain_type', 'device', 'interface',) #'tags',)
    
    # def get_tags(self, obj):
    #     tagset = ServiceTag.objects.filter(tag_domain=obj, status='AVAILABLE')
    #     #return [ ServiceTagSerializer(item).data for item in tagset ]

    #     # first available
    #     if tagset:
    #         # it's better to use nested serializer
    #         # avoiding ix detailed info
    #         return NestedServiceTagSerializer(tagset[0]).data
    #     else:
    #         return None
                 

class ServiceTagSerializer(BaseModelSerializer):
    # ix_fullname = serializers.CharField(source='ix.fullname', read_only=True)
    ix = NestedIXSerializer(required=False)
    class Meta:
        model = ServiceTag
        fields = ('id', 'display', 'created', 'last_updated', 'tag', 'ix', 'tag_domain', 'status',)


class IPv4AddressSerializer(BaseModelSerializer):
    ix = NestedIXSerializer()
    status = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = IPv4Address
        fields = ('id', 'display', 'created', 'last_updated', 'ix', 'address', 'status', 'reverse_dns', 'is_allocated')

    def get_status(self, obj):
        return obj.get_status()    


class IPv6AddressSerializer(BaseModelSerializer):
    ix = NestedIXSerializer()
    status = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = IPv6Address
        fields = ('id', 'display', 'created', 'last_updated', 'ix', 'address', 'status', 'reverse_dns', 'is_allocated')

    def get_status(self, obj):
        return obj.get_status()    



class MACAddressSerializer(BaseModelSerializer):
    class Meta:
        model = MACAddress
        fields = ('id', 'display', 'created', 'last_updated', 'address',)


class CustomerConnectionEndpointSerializer(BaseModelSerializer):

    customer_connection = NestedCustomerConnectionSerializer()

    # read only fields
    port_name = serializers.CharField(source='customerconnectionendpoint.port_name', read_only=True)
    switch_ip = serializers.CharField(source='customerconnectionendpoint.switch_ip', read_only=True)
    dio_position = serializers.CharField(source='customerconnectionendpoint.dio_position', read_only=True)
    dio_pix = serializers.CharField(source='customerconnectionendpoint.dio_pix', read_only=True)

    class Meta:
        model = CustomerConnectionEndpoint
        fields = ('id', 'display', 'created', 'last_updated', 'customer_connection', 'configured_capacity', 'interface', 'frontport', 'rearport', 'port_name', 'switch_ip', 'dio_position', 'dio_pix', 'status')


class CreateOrUpdateCcEndpointSerializer(BaseModelSerializer):

    # id = serializers.IntegerField(required=False)

    class Meta:
        model = CustomerConnectionEndpoint
        fields = ('id', 'customer_connection', 'configured_capacity', 'interface', 'frontport', 'rearport',)


class CustomerConnectionTypeSerializer(BaseModelSerializer):

    class Meta:
        model = CustomerConnectionType
        fields = ('id', 'display', 'created', 'last_updated', 'connection_name', 'connection_type')

class CustomerConnectionSerializer(BaseModelSerializer):

    customerconnectionendpoints = serializers.SerializerMethodField('_get_connection_endpoints')
    connection_type = NestedCustomerConnectionTypeSerializer()
    asn = NestedASSerializer()

    class Meta:
        model = CustomerConnection
        fields = ('id', 'display', 'created', 'last_updated', 'display', 'name', 'is_lag', 'asn', 'ticket', 'connection_type', 'tag_domain',
                  'customerconnectionendpoints', 'connected_device_id', 'status')

    def _get_connection_endpoints(self, instance):
        cc_endpoints = instance.customerconnectionendpoint.all() 
        return [ CustomerConnectionEndpointSerializer(item).data for item in cc_endpoints ]


class CreateOrUpdateCustomerConnectionSerializer(serializers.Serializer):

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=50)
    asn = NestedASSerializer()
    connection_type = NestedCustomerConnectionTypeSerializer()
    customerconnectionendpoints = CreateOrUpdateCcEndpointSerializer(required=False, many=True)


    class Meta:
        model = CustomerConnection
        fields = ('id', 'display', 'created', 'last_updated', 'display', 'name', 'is_lag', 'asn', 'ticket', 'connection_type', 'customerconnectionendpoints')


    def _create_update_instance_keys(self, instance, key, list_validated_data):
        for endpoint in list_validated_data:
            endpoint[key] = instance
            CustomerConnectionEndpoint.objects.create(**endpoint, status='ACTIVATION')
        return


    def _update_instance_keys(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()


    def _get_tag_domain(self, instance, list_validated_data):
        interface = Interface.objects.get(id=list_validated_data[0].pop('interface').id)

        tag_domain = ServiceTagDomain.objects.filter(interface__id=interface.id, domain_type='PORT-CHANNEL')

        if(tag_domain.count()>0):
            instance.tag_domain = tag_domain.first()
            instance.save()
            return

        tag_domain = ServiceTagDomain.objects.filter(device__id=interface.device.id, domain_type='DEVICE-DOMAIN')

        if(tag_domain.count()>0):
            instance.tag_domain = tag_domain.first()
            instance.save()
            return

        tag_domain = ServiceTagDomain.objects.filter(ix__code=interface.device.site.region.slug, domain_type='IX-DOMAIN')

        if(tag_domain.count()>0):
            instance.tag_domain = tag_domain.first()
            instance.save()
            return

        return


    @transaction.atomic
    def create(self, validated_data):

        customerconnectionendpoints = validated_data.pop('customerconnectionendpoints')

        connection = CustomerConnection.objects.create(**validated_data, status='ACTIVATION')

        if len(customerconnectionendpoints)>0:
            self._create_update_instance_keys(connection, 'customer_connection', customerconnectionendpoints)
            tag_domain = connection._get_tagdomain_by_device()
            connection.tag_domain = tag_domain
            connection.save(update_fields=['tag_domain'])
            # self._get_tag_domain(connection, customerconnectionendpoints)

        return connection


    @transaction.atomic
    def update(self, instance, validated_data):

        customerconnectionendpoints = validated_data.pop('customerconnectionendpoints')

        if len(customerconnectionendpoints)>0:
            self._create_update_instance_keys(instance, 'customer_connection', customerconnectionendpoints)

        return instance


class ConnectedDeviceSerializer(BaseModelSerializer):

    class Meta:
        model = CustomerConnection
        fields = ('id', 'display', 'destination_device_info', 'tag_domain', 'connection_type')


class ConnectedInterfaceSerializer(BaseModelSerializer):

    connection_type = NestedCustomerConnectionTypeSerializer()
    asn = NestedASSerializer()

    class Meta:
        model = CustomerConnection
        fields = ('id', 'name', 'asn', 'connection_type', 'tagdomain', 'connected_device_info', 'device_id_by_interface', 'connected_interfaces', 'status',)

    
class ServiceTypeSerializer(BaseModelSerializer):

    class Meta:
        model = ServiceType
        fields = ('id', 'display', 'created', 'last_updated', 'description', 'name', 'num_clients',)


class IXServiceSerializer(BaseModelSerializer):
    service_type = NestedServiceTypeSerializer()
    ix = NestedIXSerializer()
    class Meta:
        model = IXService
        fields = ('id', 'display', 'created', 'last_updated', 'service_type', 'name', 'label', 'ix',)


class CustomerServiceSerializer(BaseModelSerializer):
# class CustomerServiceSerializer(serializers.Serializer):

    id = serializers.IntegerField(read_only=True)
    service = NestedIXServiceSerializer()
    connection = NestedCustomerConnectionSerializer()
    asn = NestedASSerializer()
    mlpav4_address = NestedIPv4AddressSerializer(required=False)
    mlpav6_address = NestedIPv6AddressSerializer(required=False)
    # mac_address = NestedMACAddressSerializer(read_only=True)
    tag_or_outer = NestedServiceTagSerializer(required=False)
    ticket = serializers.IntegerField(required=False)

    # display field tag that shoud not be used by serializer
    # service_tag = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CustomerService
        fields = ('id', 'display', 'created', 'last_updated', 'asn', 'service', 'connection', 'mac_address', 'inner_tag', 'tag_or_outer', 'mlpav4_address', 'mlpav6_address', 'mac_address', 'ticket')


class CreateOrUpdateCustomerServiceSerializer(BaseModelSerializer):

    id = serializers.IntegerField(read_only=True)
    service = NestedIXServiceSerializer(required=False)
    # connection = NestedCustomerConnectionSerializer()
    asn = NestedASSerializer()
    mlpav4_address = NestedIPv4AddressSerializer(required=False)
    mlpav6_address = NestedIPv6AddressSerializer(required=False)
    # mac_address = NestedMACAddressSerializer(read_only=True)
    # tag_or_outer = NestedServiceTagSerializer(required=False)
    ticket = serializers.IntegerField(required=False)
    
    # display field tag that shoud not be used by serializer
    # service_tag = serializers.SerializerMethodField(read_only=True)

    def get_service_tag(self, obj):
        return ServiceTagSerializer(obj.tag_or_outer).data
    
    def get_tag_domain_id(self, obj):
        return obj.tag_domain_id
    
    class Meta:
        model = CustomerService
        fields = ('id', 'display', 'created', 'last_updated', 'asn', 'service', 'connection', 'mac_address', 'inner_tag', 'tag_or_outer', 'mlpav4_address', 'mlpav6_address', 'mac_address', 'ticket')
    
    def _update_instance_keys(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()

    def create(self, validated_data):
        cservice = CustomerService.objects.create(**validated_data)
        return cservice

    def update(self, instance, validated_data):
        previous_tag = instance.tag_or_outer
        self._update_instance_keys(instance, validated_data)
        # change previous tag status when object tag is changed
        if previous_tag and previous_tag.customerservice.all().count() == 0:
            previous_tag.status = "AVAILABLE"
            previous_tag.save()
        return instance


class CustomerConnectionNameSerializer(serializers.ModelSerializer):
    
    connection_name = serializers.SerializerMethodField(read_only=True)

    def get_connection_name(self, obj):
        text = self.context['request'].query_params.get('device', None)
        return str(obj.number) + ('[{}] '.format(str(text)) if text else '')

    class Meta:
        model = AS
        fields = ('id', 'connection_name',)
