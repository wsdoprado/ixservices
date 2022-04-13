from rest_framework.viewsets import ModelViewSet
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from django.http import HttpResponse, HttpResponseBadRequest
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.mixins import PermissionRequiredMixin
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from django.db import transaction
from django.db.models import Q, F, TextField, Case, When, Count
from django.db.models.functions import Cast
from django.core.exceptions import ValidationError
from django.contrib.postgres.aggregates.general import ArrayAgg
from itertools import product

from ixservices.ixservices.models import AS, IX, ServiceTag, IPv4Address, IPv6Address, MACAddress, CustomerConnection, CustomerConnectionType, CustomerConnectionEndpoint, CustomerService, ServiceTagDomain, ServiceType, IXService
from .serializers import (ASSerializer, IXSerializer, ServiceTagDomainSerializer, ServiceTagSerializer, IPv4AddressSerializer, IPv6AddressSerializer, MACAddressSerializer, CustomerConnectionEndpointSerializer,
                          CustomerServiceSerializer, CustomerConnectionSerializer, CustomerConnectionTypeSerializer, ServiceTypeSerializer, IXServiceSerializer, ConnectedDeviceSerializer,
                          ConnectedInterfaceSerializer, CreateOrUpdateCustomerConnectionSerializer, CreateOrUpdateCustomerServiceSerializer)

# netbox imports                          
from dcim.api.serializers import InterfaceSerializer, FrontPortSerializer, RearPortSerializer
from dcim.models import Interface, FrontPort, RearPort, CablePath
from netbox.api.views import ModelViewSet as NetboxModelViewSet

from ..ixservices.utils.whoisutils import get_parsed_whois
from ixservices.ixservices.utils.status import TagStatusChoices

class NoAuthViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    authentication_classes = []
    permission_classes = []
    serializer_class = None
    queryset = []


class AuthViewSet(NetboxModelViewSet):
    # authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = None
    queryset = []


class ReadOnlyViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    # authentication_classes = [SessionAuthentication, BasicAuthentication]
    # permission_classes = [IsAuthenticated]
    serializer_class = None
    queryset = []


class PermissionRequiredViewSet(viewsets.ModelViewSet):
    # permission_required = 'extras.view_tag'
    # set permissions
    # permission_required = 'ixservices.view_customerservice'
    serializer_class = None
    queryset = []


class ASViewSet(AuthViewSet):
    serializer_class = ASSerializer
    queryset = AS.objects.all()   
    filter_fields = ("number", )

    @action(detail=False, methods=['GET'])
    def getASWhois(self, request, **kwargs):
        number = request.GET.get('number', False)
        if not number:
            return Response("Informar AS", status.HTTP_400_BAD_REQUEST)

        try:
            final_list = get_parsed_whois(int(number))
        except Exception as e:
            #return HttpResponseBadRequest(f"AS{number} não existe!")
            msg = str(e).lower()
            if msg.find('exist') >= 0:
                return Response(f"AS{number} não existe!", status.HTTP_400_BAD_REQUEST)
            else:
                return Response(f"AS{number} inválido!", status.HTTP_400_BAD_REQUEST)


        return Response(final_list)


class IXViewSet(AuthViewSet):
    serializer_class = IXSerializer
    queryset = IX.objects.all()  
    filter_fields = ("code", "region_id")

    @action(detail=False, methods=['GET'])
    def getIPsFromIX(self, request, **kwargs):
        ix = request.GET.get('code', False)
        version = request.GET.get('version', False)
        not_allocated = request.GET.get('not_allocated', False)
        if not ix or not version:
            return HttpResponseBadRequest("Informar IX e/ou Versão IP")

        qs = self.filter_queryset(self.get_queryset())

        version = version.lower()
        if version == "ipv4":

            data = qs.annotate(
                ipv4_id=F('ipv4address__id'),
                ipv4=F('ipv4address__address'),
                customerserviceipv4=F('ipv4address__customerservice'),
                asnipv4=F('ipv4address__customerservice__asn__number'),
            ).values('ipv4_id', 'ipv4', 'customerserviceipv4', 'asnipv4').order_by('ipv4',)

            data = data.exclude(
                customerserviceipv4__isnull=False,
                asnipv4__isnull=False,
            ) if not_allocated == '1' else data

        elif version == "ipv6":

            data = qs.annotate(
                ipv6_id=F('ipv6address__id'),
                ipv6=F('ipv6address__address'),
                customerserviceipv6=F('ipv6address__customerservice'),
                asnipv6=F('ipv6address__customerservice__asn__number'),
            ).values('ipv6_id', 'ipv6', 'customerserviceipv6', 'asnipv6').order_by('ipv6',)

            data = data.exclude(
                customerserviceipv6__isnull=False,
                asnipv6__isnull=False,
            ) if not_allocated == '1' else data

        else:
            return HttpResponseBadRequest("Versão IP inválida")

        return Response(data)


    @action(detail=False, methods=['GET'])
    def getIXs(self, request, **kwargs):
        data = self.queryset.values('code', 'fullname')
        return Response(data)


    @action(detail=False, methods=['GET'])
    def getPIXesFromIX(self, request, **kwargs):
        ix = request.GET.get('code', False)
        if not ix:
            return HttpResponseBadRequest("Informar IX")

        qs = self.filter_queryset(self.get_queryset())

        qs = qs.annotate(
            pix_id=F("region__sites__id"),
            pix_name=F("region__sites__name")
        )

        data = qs.values("pix_id", "pix_name")

        return Response(data)


    @action(detail=False, methods=['GET'])
    def getPixFromIX(self, request, **kwargs):
        ix = request.GET.get('code', False)
        pix__id = request.GET.get('pix__id', False)
        if not ix or not pix__id:
            return HttpResponseBadRequest("Informar IX e/ou PIX")

        qs = self.filter_queryset(self.get_queryset())
        qs = qs.filter(region__sites__id=pix__id)
        qs = qs.annotate(
            pix_id=F("region__sites__id"),
            pix_name=F("region__sites__name")
        )

        data = qs.values("pix_id", "pix_name")

        return Response(data)


    @action(detail=False, methods=['GET'])
    def getDioList(self, request, **kwargs):
        ix = request.GET.get('code', False)
        pix__id = request.GET.get('pix__id', False)
        if not ix or not pix__id:
            return HttpResponseBadRequest("Informar IX e/ou PIX")

        qs = self.filter_queryset(self.get_queryset())
        qs = qs.filter(
            region__sites__id=pix__id, region__sites__devices__device_role__slug="diop",
            region__sites__devices__tenant__name='production',
        )

        qs = qs.annotate(
            device_id=F("region__sites__devices__id"),
            device_name=F("region__sites__devices__name"),
        )

        data = qs.values('device_id', 'device_name').order_by('device_id')

        return Response(data)


    @action(detail=False, methods=['GET'])
    def getDevicesFromPix(self, request, **kwargs):
        ix = request.GET.get('code', False)
        pix__id = request.GET.get('pix__id', False)
        if not ix or not pix__id:
            return HttpResponseBadRequest("Informar IX e/ou PIX")

        qs = self.filter_queryset(self.get_queryset())

        qs = qs.filter(
            region__sites__id=pix__id, region__sites__devices__device_role__slug__in=["diop", "pe", "l2"],
            region__sites__devices__tenant__name='production',
        )

        qs = qs.annotate(
            device_id=F("region__sites__devices__id"),
            device_name=F("region__sites__devices__name"),
            device_ip=Cast("region__sites__devices__primary_ip4__address", TextField()),
            device_role_name=F("region__sites__devices__device_role__name"),
            device_role_slug=F("region__sites__devices__device_role__slug")
        )

        data = qs.values("device_id", "device_name", "device_ip", "device_role_name", "device_role_slug")

        return Response(data)


    @action(detail=False, methods=['GET'])
    def getDeviceDetails(self, request, **kwargs):
        ix = request.GET.get('code', False)
        device__id = request.GET.get('device__id', False)
        if not ix or not device__id:
            return HttpResponseBadRequest("Informar IX e/ou Device")

        qs = self.filter_queryset(self.get_queryset())

        qs = qs.filter(
            region__sites__devices__id=device__id,
            region__sites__devices__device_role__slug__in=["diop", "pe", "l2"],
            region__sites__devices__tenant__name='production',
        )

        qs = qs.annotate(
            device_id=F("region__sites__devices__id"),
            device_name=F("region__sites__devices__name"),
            device_type=F("region__sites__devices__device_type__model"),
            device_ip=Cast("region__sites__devices__primary_ip4__address", TextField()),
            device_pix=F("region__sites__devices__site__name"),
        )

        data = qs.values("device_id", "device_name", "device_type", "device_ip", "device_pix")

        return Response(data)


    @action(detail=False, methods=['GET'])
    def getFreePositionsFromDevice(self, request, **kwargs):
        ix = request.GET.get('code', False)
        device__id = request.GET.get('device__id', False)
        if not ix or not device__id:
            return HttpResponseBadRequest("Informar IX e/ou Device")

        qs = self.filter_queryset(self.get_queryset())

        qs = qs.filter(
            Q(region__sites__devices__id=device__id) &
            (
                (
                    Q(region__sites__devices__interfaces__cable__isnull=True) &
                    Q(region__sites__devices__interfaces__mark_connected=False) &
                    Q(region__sites__devices__interfaces__customerconnectionendpoint__isnull=True) &
                    Q(region__sites__devices__interfaces__custom_field_data__InterfaceRole='Participant')
                ) |
                (
                    Q(region__sites__devices__rearports__cable__isnull=True) &
                    Q(region__sites__devices__rearports__mark_connected=False)
                )
            )
        )

        qs = qs.annotate(
            device_id=F("region__sites__devices__id"),
            device_name=F("region__sites__devices__name"),
        )

        qs = qs.annotate(
            position_id=F("region__sites__devices__interfaces__id"),
            position_name=F("region__sites__devices__interfaces__name"),
        ).distinct().order_by("position_name")

        interfaces = qs.values("device_id", "device_name", "position_id", "position_name")

        qs = qs.annotate(
            position_id=F("region__sites__devices__rearports__id"),
            position_name=F("region__sites__devices__rearports__name"),
        ).distinct().order_by("position_name")

        rearports = qs.values("device_id", "device_name", "position_id", "position_name")

        data = interfaces.union(rearports)

        return Response(data)


    @action(detail=False, methods=['GET'])
    def getInterfaceFromDevice(self, request, **kwargs):
        ix = request.GET.get('code', False)
        device__id = request.GET.get('device__id', False)
        interface__id = request.GET.get('interface__id', False)

        if not ix or not device__id or not interface__id:
            return HttpResponseBadRequest("Informar IX, Device e/ou Interface")

        qs = self.filter_queryset(self.get_queryset())

        qs = qs.filter(
            region__sites__devices__id=device__id,
            region__sites__devices__interfaces__id=interface__id,
        )

        qs = qs.annotate(
            position_id=F("region__sites__devices__interfaces__id"),
            position_name=F("region__sites__devices__interfaces__name"),
            position_type=F("region__sites__devices__interfaces__type"),
            device_ip=Cast("region__sites__devices__primary_ip4__address", TextField())
        ).distinct().order_by("position_name")

        data = qs.values("position_id", "position_name", "position_type", "device_ip")

        return Response(data)


class TagViewSet(AuthViewSet):
    serializer_class = ServiceTagSerializer
    queryset = ServiceTag.objects.all()   
    filter_fields = ("ix__code", "status", "tag", "tag_domain")


    @action(detail=False, methods=['GET'])
    def getBilateralTag(self, request, **kwargs):
        ix = request.GET.get('ix__code', False)
        if not ix:
            return HttpResponseBadRequest("Informar IX")

        qs = self.filter_queryset(self.get_queryset())
        data = qs.filter(status='AVAILABLE', tag__gt=1000).values('id', 'tag').first()

        return Response(data)


    @action(detail=False, methods=['GET'])
    def getAvailableTagsFromIX(self, request, **kwargs):
        ix = request.GET.get('ix__code', False)
        if not ix:
            return HttpResponseBadRequest("Informar IX")

        qs = self.filter_queryset(self.get_queryset())
        data = qs.filter(status='AVAILABLE').values('id', 'tag').order_by('tag')

        return Response(data)


    @action(detail=False, methods=['GET'])
    def getCountTags(self, request, **kwargs):
        ix = request.GET.get('ix__code', False)
        if not ix:
            return HttpResponseBadRequest("Informar IX")

        ix = ix.lower()
        availableTags = self.queryset.filter(ix__code=ix, status='AVAILABLE').count()
        allocatedTags = self.queryset.filter(ix__code=ix, status='ALLOCATED').count()
        productionTags = self.queryset.filter(ix__code=ix, status='PRODUCTION').count()

        data = {
            'availableTags': availableTags,
            'allocatedTags': allocatedTags,
            'productionTags': productionTags
        }

        return Response(data)


    @action(detail=False, methods=['GET'])
    def getTagsFromIX(self, request, **kwargs):
        ix = request.GET.get('ix__code', False)
        if not ix:
            return HttpResponseBadRequest("Informar IX")

        qs = self.filter_queryset(self.get_queryset())

        count = {
            'AVAILABLE': qs.filter(status='AVAILABLE').count(),
            'PRODUCTION': qs.filter(status='PRODUCTION').count(),
        }

        tags = qs.values('tag', 'status', 'customerservice')

        return Response({'count': count, 'tags': tags})


    @action(detail=False, methods=['GET'])
    def getServiceFromTag(self, request, **kwargs):
        tag = request.GET.get('tag', False)
        ix = request.GET.get('ix__code', False)
        if not ix or not tag:
            return HttpResponseBadRequest("Informar IX e/ou Tag")

        qs = self.filter_queryset(self.get_queryset())

        tag = qs.get()

        data = {
            'tag': tag.tag,
            'status': tag.status
        }

        if tag.customerservice.count()>0:

            connections = tag.customerservice.values_list('connection_id')
            connections = [connection[0] for connection in connections]
            connections = CustomerConnection.objects.filter(pk__in=connections).distinct()
            connections = ConnectedInterfaceSerializer(connections, many=True)

            service = tag.customerservice.values(
                'id', 'asn__number', 'mlpav4_address__address', 'mlpav6_address__address', 'connection_id', 'service__service_type__name',
            ).distinct().order_by()

            data['connections'] = connections.data
            data['services'] = service

            return Response(data)

        return Response(data)


class TagDomainViewSet(AuthViewSet):
    """
    
    /api/plugins/ixservices/tagdomain/?...
    retorna tagdomain conforme filtro: ix__code, device_id, interface_id

    /api/plugins/ixservices/tagdomain/getTags/?id=DOMAIN_ID...
    retorna JSON com as tags do dominio especificado, agrupadas por status

    { 'PRODUCTION': { 0: ... }, ... }

    """
    serializer_class = ServiceTagDomainSerializer
    queryset = ServiceTagDomain.objects.all()

    # ex: status=ALLOCATED only return used tags
    #     id=3 tags from domain_id=3

    filter_fields = ("ix__code", "ix_id", "device_id", "interface_id", "id")

    # TODO search domains by device
    # 1. is there a device domain? ok send allocated tags (processing via frontend)
    # 2. no device domain? ok look for IX domain and/or port channel domain
    # 2a. send allocated tags for existent domain

    # return tags in given status from specific domain 
    @action(detail=False, methods=['GET'])
    def getTags(self, request, **kwargs):
        # 
        id = request.GET.get('id', False)
        if not id:
            return Response('Informar id para o servicetagdomain', status.HTTP_400_BAD_REQUEST)

        # using model defined tuple: STATUSES
        # comprehension
        tagd = { key: [] for key,txt in ServiceTag.STATUSES }

        #tagstatus = request.GET.get('status', False)
        #if not tagstatus:
        for key in tagd:
            qstag = ServiceTag.objects.filter(tag_domain__id=id,status=key).annotate(tag_id=F('id')).values('tag_id','tag')
            verif_cs = qstag.filter(customerservice__isnull=False)
            if verif_cs:
                # somente tag que esteja em producao e "atribuida" a um customerservice
                tagid_list = list(verif_cs.values_list('id', flat=True))
                # aggregate customerservice
                tag_qs = IXService.objects.filter(
                        customerservice__tag_or_outer__id__in=tagid_list
                    ).annotate(
                        tag=F('customerservice__tag_or_outer__tag'),
                        tag_id=F('customerservice__tag_or_outer__id'))
                #tag_list = tag_qs.values('customerservice','tag','tag_id')
                ixsrvs = tag_qs.annotate(ncs=Count('customerservice')).values('name','service_type__name','ncs')
                detail_list = []
                for srv in ixsrvs:
                    listx = tag_qs.filter(name=srv['name'])
                    
                    # customerservice list
                    # https://docs.djangoproject.com/en/4.0/ref/contrib/postgres/aggregates/
                    srv['tags'] = listx.annotate(
                                        asn_list=ArrayAgg(F('customerservice__asn__number'),),
                                        inner_tag_list=ArrayAgg(F('customerservice__inner_tag'), filter=Q(customerservice__inner_tag__isnull=False))
                                  ).values('tag','tag_id','asn_list', 'inner_tag_list')
                    detail_list.append(srv)
                
                tagd.update({key:detail_list})

                #cslist = verif_cs.aggregate('customerservice__service')
            else:
                tagd.update({key:qstag})

        return Response(tagd)

class IPv4AddressViewSet(AuthViewSet):
    serializer_class = IPv4AddressSerializer
    queryset = IPv4Address.objects.all()
    filter_fields = ("ix__code", "address")


    @action(detail=False, methods=['GET'])
    def getIPv4ToCustomerService(self, request, **kwargs):
        ix = request.GET.get('ix__code', False)
        only_v4 = request.GET.get('only_v4', False)
        if not ix:
            return HttpResponseBadRequest("Informar IX")

        qs = self.filter_queryset(self.get_queryset())

        v4 = qs.filter(customerservice__isnull=True).values('id', 'address')

        if v4.count() == 0:
            return HttpResponseBadRequest("Nenhum IPv4 livre encontrado.")

        if not only_v4 or only_v4 == '0':
            v6 = IPv6Address.objects.filter(ix__code=ix, customerservice__isnull=True).values('id', 'address')

            ips_list = product(v4, v6)
            ipv4, ipv6 = next((
                ips for ips in ips_list
                if int(ips[0]['address'].rsplit(".", 1)[-1]) == int(ips[1]['address'].rsplit(":", 1)[-1])), (None, None))

            if ipv4 is None:
                ipv4 = v4.first()
                ipv6 = v6.first()

            return Response({
                'ipv4': ipv4,
                'ipv6': ipv6
            })

        return Response({'ipv4': v4.first()})


class IPv6AddressViewSet(AuthViewSet):
    serializer_class = IPv6AddressSerializer
    queryset = IPv6Address.objects.all()   
    filter_fields = ("ix__code", "address")


    @action(detail=False, methods=['GET'])
    def getIPv6ToCustomerService(self, request, **kwargs):
        ix = request.GET.get('ix__code', False)
        if not ix:
            return HttpResponseBadRequest("Informar IX")

        qs = self.filter_queryset(self.get_queryset())

        v6 = qs.filter(customerservice__isnull=True).values('id', 'address')

        if v6.count() == 0:
            return HttpResponseBadRequest("Nenhum IPv6 livre encontrado.")

        return Response({'ipv6': v6.first()})


class MacAddressViewSet(AuthViewSet):
    serializer_class = MACAddressSerializer
    queryset = MACAddress.objects.all()
    filter_fields = ("address", )


    @action(detail=False, methods=['GET'])
    def searchVendor(self, request, **kwargs):
        vendor = request.GET.get('vendor', False)
        if not vendor:
            return HttpResponseBadRequest("Informar Vendor")

        qs = self.queryset.filter(address__startswith=vendor)
        return Response({'count': qs.count()})


    @action(detail=False, methods=['GET'])
    def searchMac(self, request, **kwargs):
        ix = request.GET.get('ix__code', False)
        address = request.GET.get('address', False)
        if not address:
            return HttpResponseBadRequest("Informar IX e/ou MAC")

        qs = CustomerService.objects.annotate(
            rearport_pix_name=F('connection__customerconnectionendpoint__rearport__device__site__name'),
            interface_pix_name=F('connection__customerconnectionendpoint__interface__device__site__name'),
        ).filter(
            service__ix__code=ix,
            mac_address__address=address
        ).values('asn__number', 'service__service_type__name', 'mlpav4_address__address', 'mlpav6_address__address', 'rearport_pix_name', 'interface_pix_name').order_by()

        data = qs.values('asn__number', 'service__service_type__name', 'mlpav4_address__address', 'mlpav6_address__address', 'rearport_pix_name', 'interface_pix_name').order_by()
        return Response(data)
        

class ServiceTypeViewSet(AuthViewSet):
    serializer_class = ServiceTypeSerializer
    queryset = ServiceType.objects.all()

class ServiceViewSet(AuthViewSet):
    serializer_class = IXServiceSerializer
    queryset = IXService.objects.all()
    filter_fields = ("ix__code", "name")
    
class CustomerConnectionTypeViewSet(AuthViewSet):
    serializer_class = CustomerConnectionTypeSerializer
    queryset = CustomerConnectionType.objects.all()


class CustomerServiceViewSet(AuthViewSet):
    serializer_class = CustomerServiceSerializer
    queryset = CustomerService.objects.all()
    filter_fields = ("service__ix__code", "asn__number", "connection__asn__number", "connection", "mlpav4_address__address", "mac_address__address",)


    @action(detail=False, methods=['GET'])
    def getServiceFromIpOrMac(self, request, **kwargs):

        ip = request.GET.get('mlpav4_address__address', False)
        mac = request.GET.get('mac_address__address', False)
        if not ip and not mac:
            return HttpResponseBadRequest("Informar IP ou MAC")

        qs = self.filter_queryset(self.get_queryset())

        if qs.count()>0:
            connections = [service.connection_id for service in qs]
            connections = CustomerConnection.objects.filter(pk__in=connections).distinct()
            connections = ConnectedInterfaceSerializer(connections, many=True)

            service = qs.values(
                'id', 'asn__number', 'tag_or_outer__tag', 'mlpav4_address__address', 'mlpav6_address__address', 'connection_id', 'service__service_type__name',
            ).distinct().order_by()

            data = {
                'connections': connections.data,
                'services': service
            }

            return Response(data)

        return Response({})


    @action(detail=False, methods=['GET'])
    def getASNsFromPIX(self, request, **kwargs):
        ix = request.GET.get('service__ix__code', False)
        pix__id = request.GET.get('pix__id', False)
        if not ix or not pix__id:
            return HttpResponseBadRequest("Informar IX e/ou PIX")

        connections = CustomerConnection.objects.filter(customerservice__service__ix__code=ix).distinct()

        connections = connections.filter(
            (Q(customerconnectionendpoint__rearport__device__site__id=pix__id) | Q(customerconnectionendpoint__interface__device__site__id=pix__id))
        )
        asns_connections = connections.values('asn__number').distinct().order_by('asn__number')

        idConnections = [item[0] for item in connections.values_list('id').distinct()]

        qs = self.filter_queryset(self.get_queryset())
        asns_services = qs.filter(connection__id__in=idConnections).values('asn__number').distinct().order_by('asn__number')

        asns = asns_connections.union(asns_services)

        return Response(asns)


    @action(detail=False, methods=['GET'])
    def getCountServicesAndCixFromPIX(self, request, **kwargs):
        ix = request.GET.get('service__ix__code', False)
        pix__id = request.GET.get('pix__id', False)
        if not ix or not pix__id:
            return HttpResponseBadRequest("Informar IX e/ou PIX")

        connections = CustomerConnection.objects.filter(customerservice__service__ix__code=ix).distinct()

        connections = connections.filter(
            (Q(customerconnectionendpoint__rearport__device__site__id=pix__id) | Q(customerconnectionendpoint__interface__device__site__id=pix__id))
        )

        cix = connections.exclude(connection_type__id=1).count()

        idConnections = [item[0] for item in connections.values_list('id').distinct()]

        qs = self.filter_queryset(self.get_queryset())

        data = {
            'atmv4': qs.filter(connection__id__in=idConnections, service__service_type__name='ATMv4').count(),
            'atmv6': qs.filter(connection__id__in=idConnections, service__service_type__name='ATMv6').count(),
            'bilaterais': qs.filter(connection__id__in=idConnections, service__service_type__name='Bilateral').count(),
            'cix': cix,
        }

        return Response(data)


    @action(detail=False, methods=['GET'])
    def getServicesFromConnection(self, request, **kwargs):
        ix = request.GET.get('service__ix__code', False)
        connection = request.GET.get('connection', False)
        if not ix or not connection:
            return HttpResponseBadRequest("Informar IX e/ou Connection")


        qs = self.filter_queryset(self.get_queryset())
        qs = qs.annotate(
            ccid=F('connection__id')
        )

        data = qs.values('id', 'ccid')

        return Response(data)


    @action(detail=False, methods=['GET'])
    def getAsnServicesFromIX(self, request, **kwargs):
        ix = request.GET.get('service__ix__code', False)
        asn = request.GET.get('asn__number', False)
        if not ix or not asn:
            return HttpResponseBadRequest("Informar IX e/ou ASN")

        connections = CustomerConnection.objects.filter(customerservice__service__ix__code=ix, customerservice__asn__number=asn).distinct()

        connections = ConnectedInterfaceSerializer(connections, many=True)

        # qs = qs.annotate(
        #     ccendpoint_id=F('connection__customerconnectionendpoint__id'),
        #     rearport=F('connection__customerconnectionendpoint__rearport'),
        #     interface=F('connection__customerconnectionendpoint__interface'),
        #     configured_capacity=F('connection__customerconnectionendpoint__configured_capacity'),
        #     connection_type=F('connection__connection_type__connection_type'),
        #     asn_connection=F('connection__asn__number'),
        #     cc_ticket=F('connection__ticket')
        # )


        # ### Buscando dados através da rearport
        # qs = qs.annotate(
        #     port_name=F('connection__customerconnectionendpoint__rearport__name'),
        #     port_type=F('connection__customerconnectionendpoint__rearport__type'),
        #     pix_id=F('connection__customerconnectionendpoint__rearport__device__site__id'),
        #     pix=F('connection__customerconnectionendpoint__rearport__device__site__name'),
        #     device_id=F('connection__customerconnectionendpoint__rearport__device__id'),
        #     device_name=F('connection__customerconnectionendpoint__rearport__device__name'),
        #     device_slug=F('connection__customerconnectionendpoint__rearport__device__device_role__slug'),
        #     device_ip=Cast('connection__customerconnectionendpoint__rearport__device__primary_ip4__address', TextField()),
        # )

        # connections_rearport = qs.values(
        #     'connection_id', 'asn_connection', 'connection_type', 'connection__name', 'connection__is_lag', 'port_name', 'port_type', 'device_id', 'device_name', \
        #     'device_slug', 'device_ip', 'pix_id', 'pix', 'ccendpoint_id', 'configured_capacity', 'interface', 'rearport'
        # ).exclude(rearport__isnull=True).distinct().order_by()


        # ### Buscando dados através da interface
        # qs = qs.annotate(
        #     port_name=F('connection__customerconnectionendpoint__interface__name'),
        #     port_type=F('connection__customerconnectionendpoint__interface__type'),
        #     pix_id=F('connection__customerconnectionendpoint__interface__device__site__id'),
        #     pix=F('connection__customerconnectionendpoint__interface__device__site__name'),
        #     device_id=F('connection__customerconnectionendpoint__interface__device__id'),
        #     device_name=F('connection__customerconnectionendpoint__interface__device__name'),
        #     device_slug=F('connection__customerconnectionendpoint__interface__device__device_role__slug'),
        #     device_ip=Cast('connection__customerconnectionendpoint__interface__device__primary_ip4__address', TextField()),
        # )

        # connections_interface = qs.values(
        #     'connection_id', 'asn_connection', 'connection_type', 'connection__name', 'connection__is_lag', 'port_name', 'port_type', 'device_id', 'device_name', \
        #     'device_slug', 'device_ip', 'pix_id', 'pix', 'ccendpoint_id', 'configured_capacity', 'interface', 'rearport'
        # ).exclude(interface__isnull=True).distinct().order_by()


        # connections = connections_rearport.union(connections_interface)

        qs = self.filter_queryset(self.get_queryset())

        qs = qs.annotate(
            ccendpoint_id=F('connection__customerconnectionendpoint__id'),
            cc_ticket=F('connection__ticket')
        )

        services = qs.values(
            'id', 'connection_id', 'ticket', 'cc_ticket', 'asn__number', 'service__name', 'service__service_type__name', 'tag_or_outer__id', 'tag_or_outer__tag',
            'tag_or_outer__status', 'inner_tag', 'mac_address__address', 'mlpav4_address__address', 'mlpav6_address__address'
        ).distinct().order_by()


        qsBilaterais = qs.filter(service__service_type__name='Bilateral')
        tags = [tag[0] for tag in qsBilaterais.values_list('tag_or_outer__tag')]

        bilaterais = self.queryset.filter(
            service__ix__code=ix,
            tag_or_outer__tag__in=tags
        ).exclude(
            asn__number=asn
        ).annotate(
            ccendpoint_id=F('connection__customerconnectionendpoint__id'),
            cc_ticket=F('connection__ticket')
        ).values(
            'id', 'connection_id', 'ticket', 'cc_ticket', 'asn__number', 'service__service_type__name', 'tag_or_outer__id', 'tag_or_outer__tag',
            'tag_or_outer__status', 'inner_tag', 'mac_address__address', 'mlpav4_address__address', 'mlpav6_address__address'
        ).distinct().order_by()

        data = {
            'connections': connections.data,
            'services': services,
            'bilaterais': bilaterais
        }

        return Response(data)


    @action(detail=False, methods=['GET'])
    def getServicesFromIX(self, request, **kwargs):
        ix = request.GET.get('service__ix__code', False)
        if not ix:
            return HttpResponseBadRequest("Informar IX")

        ix = ix.lower()

        totASs = AS.objects.filter(
            (
                Q(customerservice__service__ix__code=ix)
            ) |
            (
                Q(customerconnection__tag_domain__ix__code=ix)
            )
        ).distinct().count()

        totServicesATMv4 = self.queryset.filter(service__ix__code=ix, service__service_type__name="ATMv4").count()
        totServicesATMv6 = self.queryset.filter(service__ix__code=ix, service__service_type__name="ATMv6").count()
        totServicesBilateral = self.queryset.filter(service__ix__code=ix, service__service_type__name="Bilateral").count()

        totFreeInterfaces = IX.objects.filter(
            Q(code=ix) &
            Q(region__sites__devices__device_role__slug__in=['pe', 'l2']) &
            (
                (
                    Q(region__sites__devices__interfaces__cable__isnull=True) &
                    Q(region__sites__devices__interfaces__mark_connected=False) &
                    Q(region__sites__devices__interfaces__customerconnectionendpoint__isnull=True) &
                    Q(region__sites__devices__interfaces__custom_field_data__InterfaceRole='Participant')
                ) |
                (
                    # Q(region__sites__devices__rearports__cable__isnull=True) &
                    # Q(region__sites__devices__rearports__mark_connected=False) &
                    Q(region__sites__devices__interfaces__customerconnectionendpoint__isnull=True) &
                    Q(region__sites__devices__interfaces__custom_field_data__InterfaceRole='Participant')
                )
            )
        ).count()

        data = {
            "totASs": totASs,
            "totServicesATMv4": totServicesATMv4,
            "totServicesATMv6": totServicesATMv6,
            "totServicesBilateral": totServicesBilateral,
            "totFreeInterfaces": totFreeInterfaces,
        }

        return Response(data)


    @action(detail=False, methods=['GET'])
    def getCIXesFromIX(self, request):
        ix = request.GET.get('service__ix__code', False)
        if not ix:
            return HttpResponseBadRequest("Informar IX e/ou ASN")

        qs = self.filter_queryset(self.get_queryset())

        qs = qs.exclude(
            connection__connection_type=1
        )

        qs = qs.annotate(
            rearport_pix_name=F('connection__customerconnectionendpoint__rearport__device__site__name'),
            interface_pix_name=F('connection__customerconnectionendpoint__interface__device__site__name'),
        )

        qs = qs.annotate(
            pix_name=Case(
                When(rearport_pix_name__isnull=False, then=F('rearport_pix_name')),
                When(interface_pix_name__isnull=False, then=F('interface_pix_name')),
            )
        )

        qs = qs.filter(
            connection__asn__number=F('asn__number'),
        ).values('asn__number', 'connection_id', 'pix_name').distinct().order_by()

        data = {
            'cixes': [asn for asn in qs],
        }

        return Response(data)


    @action(detail=False, methods=['GET'])
    def getASNsFromCIX(self, request):
        ix = request.GET.get('service__ix__code', False)
        connection = request.GET.get('connection', False)
        if not ix or not connection:
            return HttpResponseBadRequest("Informar IX e/ou ASN")

        qs = self.filter_queryset(self.get_queryset())
        qs = qs.exclude(connection__connection_type=1)

        data = {
            'asns': qs.values('asn__number').distinct().order_by(),
            'atmv4': qs.filter(service__service_type__name='ATMv4').count(),
            'atmv6': qs.filter(service__service_type__name='ATMv6').count(),
            'bilaterais': qs.filter(service__service_type__name='Bilateral').count(),
        }
        return Response(data)


    @action(detail=False, methods=['GET'])
    def getAsnIxPresent(self, request):
        asn = request.GET.get('asn__number', False)
        if not asn:
            return HttpResponseBadRequest("Informar ASN")


        ## Buscando dados através dos Services
        qs = self.filter_queryset(self.get_queryset())
        qs = qs.annotate(ix__fullname=F('service__ix__fullname'), ix__code=F('service__ix__code'))
        asnServicesPresent = qs.values('ix__fullname', 'ix__code').distinct().order_by()

        qs = CustomerConnection.objects.filter(asn__number=asn)


        ## Buscando dados através da Rearport
        qs_rearport = qs.annotate(
            ix__fullname=F('customerconnectionendpoint__rearport__device__site__region__name'),
            ix__code=F('customerconnectionendpoint__rearport__device__site__region__slug')
        )

        asnRearportPresent = qs_rearport.values('ix__fullname', 'ix__code').distinct().order_by().exclude(ix__fullname__isnull=True, ix__code=True)


        ## Buscando dados através da Interface
        qs_interface = qs.annotate(
            ix__fullname=F('customerconnectionendpoint__interface__device__site__region__name'),
            ix__code=F('customerconnectionendpoint__interface__device__site__region__slug')
        )

        asnInterfacePresent = qs_interface.values('ix__fullname', 'ix__code').distinct().order_by().exclude(ix__fullname__isnull=True, ix__code=True)


        data = asnServicesPresent.union(asnRearportPresent)
        data = data.union(asnInterfacePresent)

        return Response(data)


class CreateOrUpdateCustomerServiceViewSet(AuthViewSet):
    serializer_class = CreateOrUpdateCustomerServiceSerializer
    queryset = CustomerService.objects.all()
    filter_fields = ("service__ix__code", "asn__number", "connection__asn__number", "connection")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, many=isinstance(request.data,list))
        if isinstance(self.request.data,list):
            serializer_data = self.perform_create(serializer)
        else:
            self.perform_create(serializer)
            serializer_data = serializer.data
        headers = self.get_success_headers(serializer_data)
        return Response(serializer_data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        # raise ValidationError("**TESTE DE PARAMETROS NA VIEW OK**\n{}".format(vars(self.request)))
        if isinstance(self.request.data,list):
            serializer_data = []
            with transaction.atomic():
                for item_data in self.request.data:
                    # tag_or_outer = object_data.get("tag_or_outer")
                    # tag_domain_id = item_data.get("tag_domain_id")
                    connection_id = item_data.get("connection")
                    tag_domain_id = self._get_tag_domain_id(connection_id)

                    if tag_domain_id:
                        tag_or_outer_v4 = item_data.get("tag_number_v4")
                        tag_or_outer_v6 = item_data.get("tag_number_v6")
                        tag_or_outer_bilateral = item_data.get("tag_or_outer_bilateral")
                        # create service for ipv4 only or ipv6 only
                        if tag_or_outer_v4 or tag_or_outer_v6 or tag_or_outer_bilateral:
                            tag_or_outer = self._get_tag_by_domain(
                                tag_domain_id,
                                tag_or_outer_v4 or tag_or_outer_v6 or tag_or_outer_bilateral
                            )
                            if tag_or_outer:
                                if tag_or_outer_bilateral:
                                    # service = self._get_bilateral_service(
                                    #     tag_domain_id,
                                    #     tag_number=tag_or_outer.tag,
                                    #     asn_number=item_data.get('asn')['number']
                                    # )

                                    # tag_or_outer.status = "AVAILABLE"
                                    # tag_or_outer.save()

                                    obj_serializer = self.get_serializer(data=item_data)
                                    obj_serializer.is_valid(raise_exception=True)
                                    obj_serializer.save(tag_or_outer=tag_or_outer,)# service=service)
                                    serializer_data.append(obj_serializer.data)
                                else:
                                    obj_serializer = self.get_serializer(data=item_data)
                                    obj_serializer.is_valid(raise_exception=True)
                                    obj_serializer.save(tag_or_outer=tag_or_outer)
                                    serializer_data.append(obj_serializer.data)
            return serializer_data
        else:
            serializer.is_valid(raise_exception=True)
            serializer.save()


    @transaction.atomic
    def perform_update(self, serializer):
        # raise ValidationError("**TESTE DE PARAMETROS NA VIEW OK**\n{}".format(vars(self.request)))
        # tag_domain_id = self.request.data.get("tag_domain_id")
        connection_id = self.request.data.get("connection")
        tag_domain_id = self._get_tag_domain_id(connection_id)
        tag_or_outer = self.request.data.get("tag_or_outer")
        if not tag_or_outer and tag_domain_id:
            tag_or_outer_v4 = self.request.data.get("tag_number_v4")
            tag_or_outer_v6 = self.request.data.get("tag_number_v6")
            tag_or_outer_bilateral = self.request.data.get("tag_or_outer_bilateral")
            # create service for ipv4 only or ipv6 only
            if tag_or_outer_v4 or tag_or_outer_v6 or tag_or_outer_bilateral:
                tag_or_outer = self._get_tag_by_domain(
                    tag_domain_id,
                    tag_or_outer_v4 or tag_or_outer_v6 or tag_or_outer_bilateral
                )
                if tag_or_outer:
                    serializer.save(tag_or_outer=tag_or_outer)
        else:
            serializer.is_valid(raise_exception=True)
            serializer.save()


    def _get_tag_domain_id(self, connection_id):
        try:
            cc = CustomerConnection.objects.get(pk=connection_id)
        except Exception as e:
            # dominio nao foi encontrado pelo id informado
            raise ValidationError("*** CustomerConnection not found: {}".format(connection_id))

        try:
            tag_domain_id = cc.tag_domain.id
            return tag_domain_id
        except:
            raise ValidationError("*** Tag Domain not found for CustomerConnection: {}".format(tag_domain_id))


    def _get_tag_by_domain(self, tag_domain_id, tag_number=None, option=None):
        # validacao de tag e dominio
        try:
            tag_domain = ServiceTagDomain.objects.get(pk=tag_domain_id)
        except Exception as e:
            # dominio nao foi encontrado pelo id informado
            raise ValidationError("*** ServiceTagDomain not found: {}".format(tag_domain_id))
        if tag_number:
            # verifica se a tag e dominio existem e retorna o objeto se nao cria uma nova
            service_tag = ServiceTag.objects.filter(tag=tag_number, tag_domain=tag_domain).first()
            return service_tag or ServiceTag.objects.create(tag=tag_number, tag_domain=tag_domain)
        else:
            # caso a tag noa seja informada verifica se exista uma tag disponivel e retorn o objeto
            service_tag = ServiceTag.objects.filter(status="AVAILABLE", tag_domain=tag_domain).first()
            if not service_tag:
                # a tag disponivel nao foi encontrada entao nao sera validada para o dominio informado
                raise ValidationError("*** No ServiceTag available for domain: {}".format(tag_domain_id))
            return service_tag
        # caso nao seja retornada uma tag valida o objeto permanece vazio
        return


    def _get_bilateral_service(self, tag_domain_id, tag_number=None, asn_number=None):
        try:
            tag_domain = ServiceTagDomain.objects.get(pk=tag_domain_id)
        except Exception as e:
            # dominio nao foi encontrado pelo id informado
            raise ValidationError("*** ServiceTagDomain not found: {}".format(tag_domain_id))

        bilateral = ServiceType.objects.get(name="Bilateral")
        cstag = CustomerService.objects.filter(tag_or_outer__tag=tag_number).first()

        if cstag:
            service = IXService.objects.filter(id=cstag.service.id).first()
            peer_asn = cstag.asn.number

            try:
                service_name = f'{tag_domain.ix.code}-as{peer_asn}-as{asn_number}'
                service.name = service_name
                service.save()
            except:
                ixservices_count = IXService.objects.filter(name__startswith=service_name).count()
                service_name = f'{tag_domain.ix.code}-as{peer_asn}-as{asn_number}-{ixservices_count}'
                service.name = service_name
                service.save()

        else:
            ixservices_dict = {
                'name': f'Bilateral-{tag_domain.ix.code}-{tag_number}',
                'service_type': bilateral,
                'label': ' ',
                'ix':tag_domain.ix
            }

            service = IXService.objects.create(**ixservices_dict)


        return service

 
class CustomerConnectionViewSet(AuthViewSet):
    serializer_class = CustomerConnectionSerializer
    queryset = CustomerConnection.objects.all()
    filter_fields = ('id', 'asn__number', 'connection_type', 'customerservice__asn__number',)


    @action(detail=False, methods=['GET'])
    def getTotCix(self, request, **kwargs):
        ix = request.GET.get('ix__code', False)
        if not ix:
            return HttpResponseBadRequest("Informar IX")

        ix = ix.lower()

        qs = self.queryset.filter(
            tag_domain__ix__code=ix,
            connection_type__id__in=[2,3,4],
        ).distinct()

        return Response({
            'count': qs.count()
        })


    @action(detail=False, methods=['GET'])
    def getConnectedDevices(self, request, **kwargs):
        ix = request.GET.get('ix__code', False)
        if not ix:
            return HttpResponseBadRequest("Informar IX")

        qs = self.filter_queryset(self.get_queryset())

        qs = qs.filter(
            Q(customerconnectionendpoint__interface__device__site__region__slug=ix) |
            Q(customerconnectionendpoint__rearport__device__site__region__slug=ix)
        ).distinct()

        connected_devices = ConnectedDeviceSerializer(qs, many=True)

        return Response(connected_devices.data)
    

    @action(detail=False, methods=['GET'])
    def getAsnConnections(self, request, **kwargs):
        ix = request.GET.get('ix__code', False)
        if not ix:
            return HttpResponseBadRequest("Informar IX")

        qs = self.filter_queryset(self.get_queryset())

        qs = qs.filter(Q(customerservice__service__ix__code=ix) | Q(customerconnectionendpoint__interface__device__site__region__slug=ix) | \
            Q(customerconnectionendpoint__rearport__device__site__region__slug=ix)).distinct()

        connected_interfaces = ConnectedInterfaceSerializer(qs, many=True)

        return Response(connected_interfaces.data)


    @action(detail=False, methods=['GET'])
    def switch(self, request):
        ip = request.GET.get('ip', False)
        if not ip:
            return HttpResponseBadRequest("Informar IP do switch")
        qip = self.queryset.filter(customerconnectionendpoint__switch_ip=ip)
        ## return Response(qip.values())
        dd = CustomerConnectionSerializer(qip, many=True).data
        return Response(dd)

    @action(detail=False, methods=['GET'])
    def nome(self, request):
        nm = request.GET.get('nome', False)
        if not nm:
            return HttpResponseBadRequest("Informar nome da conexão")
        qname = self.queryset.filter(name=nm)
        ## return Response(qip.values())
        dd = CustomerConnectionSerializer(qname, many=True).data
        return Response(dd)


class CreateNewCustomerConnectionViewSet(AuthViewSet):
    serializer_class = CreateOrUpdateCustomerConnectionSerializer
    queryset = CustomerConnection.objects.all()
    lookup_field = "id"


class CustomerConnectionEndpointViewSet(AuthViewSet):
    serializer_class = CustomerConnectionEndpointSerializer
    queryset = CustomerConnectionEndpoint.objects.all()


class ATMv4ServiceViewSet(ReadOnlyViewSet):
    serializer_class = CustomerServiceSerializer
    queryset = CustomerService.objects.all()
    filter_fields = ("service__ix__code", )
    
    def get_queryset(self): 
        atmv4 = ServiceType.objects.filter(pk=1).first()
        services = IXService.objects.filter(service_type=atmv4)
        return CustomerService.objects.filter(service__in=services)
    

class ATMv6ServiceViewSet(ReadOnlyViewSet):   
    serializer_class = CustomerServiceSerializer
    queryset = CustomerService.objects.all()
    
    def get_queryset(self): 
        atmv6 = ServiceType.objects.filter(pk=2).first()
        services = IXService.objects.filter(service_type=atmv6)
        return CustomerService.objects.filter(service__in=services)

class BilateralServiceViewSet(ReadOnlyViewSet):    
    serializer_class = CustomerServiceSerializer
    queryset = CustomerService.objects.all()
    
    def get_queryset(self): 
        bilateral = ServiceType.objects.filter(pk=3).first()
        services = IXService.objects.filter(service_type=bilateral)
        return CustomerService.objects.filter(service__in=services)


class InterfaceDViewSet(ReadOnlyViewSet):
    queryset = Interface.objects.all()
    serializer_class = InterfaceSerializer
    filter_fields = ['device_id']


    @action(detail=False, methods=['GET'])
    def getFreeInterfacesFromDevice(self, request, **kwargs):
        device_id = request.GET.get('device_id', False)
        if not device_id:
            return HttpResponseBadRequest("Informar IX e/ou PIX")

        qs = self.filter_queryset(self.get_queryset())
        qs = qs.filter(custom_field_data__InterfaceRole='Participant')
        data = []
        for item in qs:

            dio_connected = None

            dataItem = {}

            trace = item.trace()
            flag_ccendpoint = False

            if len(trace)>0:
                for line in trace:
                    for searchCcEndpoint in line:
                        try:
                            getattr(searchCcEndpoint, 'customerconnectionendpoint')
                            flag_ccendpoint = False
                            break
                        except:
                            flag_ccendpoint = True
                    if flag_ccendpoint == False:
                        break
            else:
                try:
                    getattr(item, 'customerconnectionendpoint')
                except:
                    flag_ccendpoint = True

            # if(len(trace) > 2):
            #     try:
            #         getattr(trace[-1][-1], 'customerconnectionendpoint')
            #     except:
            #         flag_ccendpoint = True

            # elif len(trace) > 1:
            #     try:
            #         getattr(trace[1][0], 'customerconnectionendpoint')
            #     except:
            #         flag_ccendpoint = True
            # else:
            #     try:
            #         getattr(trace[0][-1], 'customerconnectionendpoint')
            #     except:
            #         try:
            #             getattr(item, 'customerconnectionendpoint')
            #         except:
            #             flag_ccendpoint = True

            if flag_ccendpoint:
                try:
                    if len(trace)>0:
                        for position in trace:
                            for positionItem in position:
                                if isinstance(positionItem, RearPort):
                                    dio_connected = {
                                        'position_id': positionItem.id,
                                        'position_name': positionItem.name,
                                        'device_id': positionItem.device.id,
                                        'dio_name': positionItem.device.name,
                                    }
                                    break
                            if dio_connected != None:
                                break
                except Exception as e:
                    print(f'Exception {e}')
                dataItem['device_id'] = item.device_id
                dataItem['device_name'] = item.device.name
                dataItem['position_id'] = item.id
                dataItem['position_name'] = item.name
                dataItem['dio_connected'] = dio_connected
                data.append(dataItem)


        return Response(data)


    @action(detail=False, methods=['GET'])
    def getInterfacesFromDevice(self, request, **kwargs):
        device_id = request.GET.get('device_id', False)
        if not device_id:
            return HttpResponseBadRequest("Informar IX e/ou PIX")

        qs = self.filter_queryset(self.get_queryset())
        qs = qs.filter(custom_field_data__InterfaceRole='Participant')
        data = []
        for item in qs:

            dataItem = {
                'id': item.id,
                'name': item.name,
                'type': item.type,
                'description': item.description,
                'device': None,
                'device_port': None,
                'device_role': None,
                'ccId': None,
                'ccName': None,
                'asn__number': None,
                'tags': {},
            }

            trace = item.trace()
            if(len(trace) > 2):
                try:
                    dataItem['device'] = trace[-1][-1].device.id
                    dataItem['device_port'] = trace[-1][-1].name
                    dataItem['device_name'] = trace[-1][-1].device.name
                    dataItem['device_role'] = trace[-1][-1].device.device_role.slug
                except:
                    pass
            elif len(trace) > 1:
                try:
                    dataItem['device'] = trace[1][0].device.id
                    dataItem['device_port'] = trace[1][0].name
                    dataItem['device_name'] = trace[1][0].device.name
                    dataItem['device_role'] = trace[1][0].device.device_role.slug
                    dataItem['ccId'] = trace[1][0].customerconnectionendpoint.customer_connection.id
                    dataItem['ccName'] = trace[1][0].customerconnectionendpoint.customer_connection.name
                    dataItem['asn__number'] = trace[1][0].customerconnectionendpoint.customer_connection.asn.number

                    for customerservice in trace[1][0].customerconnectionendpoint.customer_connection.customerservice.iterator():
                        try:
                            if customerservice.asn.number not in list(dataItem['tags'].keys()):
                                dataItem['tags'][customerservice.asn.number] = [customerservice.tag_or_outer.tag]
                            else:
                                dataItem['tags'][customerservice.asn.number].append(customerservice.tag_or_outer.tag)
                        except:
                            pass
                except:
                    pass
            else:
                try:
                    dataItem['device'] = trace[0][-1].device.id
                    dataItem['device_port'] = trace[0][-1].name
                    dataItem['device_name'] = trace[0][-1].device.name
                    dataItem['device_role'] = trace[0][-1].device.device_role.slug
                except:
                    try:
                        dataItem['ccId'] = item.customerconnectionendpoint.customer_connection.id
                        dataItem['ccName'] = item.customerconnectionendpoint.customer_connection.name
                        dataItem['asn__number'] = item.customerconnectionendpoint.customer_connection.asn.number

                        for customerservice in item.customerconnectionendpoint.customer_connection.customerservice.iterator():
                            try:
                                if customerservice.asn.number not in list(dataItem['tags'].keys()):
                                    dataItem['tags'][customerservice.asn.number] = [customerservice.tag_or_outer.tag]
                                else:
                                    dataItem['tags'][customerservice.asn.number].append(customerservice.tag_or_outer.tag)
                            except:
                                pass
                    except:
                        pass

            data.append(dataItem)

        return Response(data)


class InterfaceFViewSet(ReadOnlyViewSet):
    queryset = Interface.objects.prefetch_related('device').filter(customerconnectionendpoint__isnull=True)
    serializer_class = InterfaceSerializer
    filter_fields = ['device_id']

class FrontPortViewSet(ReadOnlyViewSet):
    queryset = FrontPort.objects.prefetch_related('device').filter(customerconnectionendpoint__isnull=True)
    serializer_class = FrontPortSerializer
    filter_fields = ['device_id']

class RearPortViewSet(ReadOnlyViewSet):
    queryset = RearPort.objects.prefetch_related('device').filter(customerconnectionendpoint__isnull=True)
    serializer_class = RearPortSerializer
    filter_fields = ['device_id']


class RearPortDViewSet(ReadOnlyViewSet):
    queryset = RearPort.objects.all()
    serializer_class = RearPortSerializer
    filter_fields = ['device_id', 'mark_connected']


    @action(detail=False, methods=['GET'])
    def getRearPortsFromDevice(self, request, **kwargs):
        device_id = request.GET.get('device_id', False)
        if not device_id:
            return HttpResponseBadRequest("Informar IX e/ou PIX")

        qs = self.filter_queryset(self.get_queryset())

        data = []

        for item in qs:
            dataItem = {
                'position_id': item.id,
                'position_name': item.name,
                'dio_name': item.device.name,
                'label': item.label,
                'device_id': item.device_id,
                'destination_id': None,
                'device_ip': None,
                'device_port': None,
                'device_name': None,
                'description': item.description,
            }
            cablepaths = CablePath.objects.filter(path__contains=item).prefetch_related('origin', 'destination')
            if cablepaths.count()>0:
                try:
                    if cablepaths[0].origin.custom_field_data['InterfaceRole'].lower() != 'participant':
                        continue
                    dataItem['device_port'] = cablepaths[0].origin.name
                    dataItem['device_ip'] = str(cablepaths[0].origin.device.primary_ip4.address)
                    dataItem['destination_id'] = cablepaths[0].origin.device.id
                    dataItem['device_name'] = cablepaths[0].origin.device.name
                except:
                    pass
            data.append(dataItem)

        return Response(data)


class InterfaceBViewSet(ReadOnlyViewSet):
    queryset = Interface.objects.prefetch_related('device').filter(customerconnectionendpoint__interface__isnull=False)
    serializer_class = InterfaceSerializer
    filter_fields = ['device_id']


# define nova heranca porque authviewset usa os parametros de queryset e serializer
class InterfaceFrontPortRearPortViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    
    serializer_class = InterfaceSerializer
    queryset = Interface.objects.prefetch_related('device').filter(customerconnectionendpoint__isnull=True)
    filter_fields = ['device_id']

    model_serializers_filters = {
        '0' : [Interface, InterfaceSerializer],
        '1' : [FrontPort, FrontPortSerializer],
        '2' : [RearPort, RearPortSerializer]
    }
    

    def get_queryset(self):          
        try:
           option = self.request.query_params.get("option") 
           model = self.model_serializers_filters.get(option)[0]
           return model.objects.prefetch_related('device').filter(customerconnectionendpoint__isnull=True)
        except Exception as e:
            print(e)
            return Interface.objects.prefetch_related('device').filter(customerconnectionendpoint__isnull=True)
    

    def get_serializer_class(self):
        try:
            option = self.request.query_params.get("option") 
            return self.model_serializers_filters.get(option)[1]
        except Exception as e:
            print(e)
            return InterfaceSerializer



class FreeCustomerConnectionViewSet(ReadOnlyViewSet):
    serializer_class = CustomerConnectionSerializer
    queryset = (CustomerConnection.objects.filter(customerconnectionendpoint__isnull=True, is_lag=False) \
                | CustomerConnection.objects.filter(customerconnectionendpoint__interface__isnull=True, is_lag=False) \
                    | CustomerConnection.objects.filter(is_lag=True)).distinct()
    filter_fields = ['asn', 'is_lag', 'customerconnectionendpoint__interface', 'customerconnectionendpoint__interface__device__site']

class BusyCustomerConnectionViewSet(ReadOnlyViewSet):
    serializer_class = CustomerConnectionSerializer
    queryset = CustomerConnection.objects.filter(customerconnectionendpoint__interface__isnull=False).distinct()
    filter_fields = ['asn', 'is_lag', 'customerconnectionendpoint__interface']
   

# PROTECTED VIEWS
class CustomerServiceProtectedViewSet(PermissionRequiredViewSet):

    permission_required = ('ixservices.view_customerservice', 'ixservices.change_customerservice', 'ixservices.add_customerservice')
    serializer_class = CustomerServiceSerializer
    queryset = CustomerService.objects.all()
    lookup_field = 'id'


class CustomerConnectionProtectedViewSet(PermissionRequiredViewSet):

    permission_required = ('ixservices.view_customerconnection', 'ixservices.change_customerconnection', 'ixservices.add_customerconnection')
    serializer_class = CustomerConnectionSerializer
    queryset = CustomerConnection.objects.all()
    lookup_field = 'id'
    
