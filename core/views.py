from django.conf import settings
from django.shortcuts import render
from django.views.generic import View
from django.contrib.contenttypes.models import ContentType

from rest_framework.routers import APIRootView
from rest_framework import mixins, viewsets

from netbox.forms import SearchForm
from extras.models import ObjectChange, JobResult
from extras.tables import ObjectChangeTable
from extras.choices import JobResultStatusChoices
from extras.views import ObjectChangeLogView
from extras.api.views import CustomFieldModelViewSet

from ixservices.api  import serializers
from ixservices.core import filtersets
from ixservices.ixservices.models import (IX, AS, ServiceTagDomain, ServiceTag, IPv4Address, IPv6Address, MACAddress, 
                                          IXService, ServiceType, CustomerConnection, CustomerConnectionType)


from dcim.models import Device, Interface
from dcim.api.serializers import InterfaceSerializer

class HomeView(View):

    template_name = 'ixservices/generic/home.html'
    context_data  = {}
    
    def get(self, request):
        if settings.LOGIN_REQUIRED and not request.user.is_authenticated:
            return redirect("login")
            
        # Report Results
        report_content_type = ContentType.objects.get(app_label='extras', model='report')
        report_results = JobResult.objects.filter(
            obj_type=report_content_type,
            status__in=JobResultStatusChoices.TERMINAL_STATE_CHOICES
        ).defer('data')[:10]
        report_results = report_results

        # Compile changelog table
        changelog = ObjectChange.objects.restrict(request.user, 'view').prefetch_related(
            'user', 'changed_object_type'
        )[:10]
        changelog_table = ObjectChangeTable(changelog)

        self.context_data = {           
            'stats': [],
            'search_form': SearchForm(),
            'report_results': report_results,
            'changelog_table': changelog_table,
        }        

        return render(request, self.template_name, self.context_data)



class ObjectChangeLogView(ObjectChangeLogView):
    """
    Present a history of changes made to a particular object.

    base_template: The name of the template to extend. If not provided, "<app>/<model>.html" will be used.
    """


class RootView(APIRootView):
    """
       Select list API root view
    """
    def get_view_name(self):
        return 'api-list'


class IXSelectViewSet(CustomFieldModelViewSet):
    queryset = IX.objects.all()
    serializer_class = serializers.IXSerializer
    filterset_class = filtersets.IXFilterSet

class ASSelectViewSet(CustomFieldModelViewSet):
    queryset = AS.objects.all()
    serializer_class = serializers.ASSerializer
    filterset_class = filtersets.ASFilterSet

class ServiceTagSelectViewSet(CustomFieldModelViewSet):
    queryset = ServiceTag.objects.all()
    serializer_class = serializers.ServiceTagSerializer
    filterset_class = filtersets.TagFilterSet

class ServiceTagDomainSelectViewSet(CustomFieldModelViewSet):
    queryset = ServiceTagDomain.objects.all()
    serializer_class = serializers.ServiceTagDomainSerializer
    filterset_class = filtersets.ServiceTagDomainFilterSet

class IPv4AddressSelectViewSet(CustomFieldModelViewSet):
    queryset = IPv4Address.objects.all()
    serializer_class = serializers.IPv4AddressSerializer
    filterset_class = filtersets.IPv4AddressFilterSet

class IPv6AddressSelectViewSet(CustomFieldModelViewSet):
    queryset = IPv6Address.objects.all()
    serializer_class = serializers.IPv6AddressSerializer
    filterset_class = filtersets.IPv6AddressFilterSet

class MACAddressSelectViewSet(CustomFieldModelViewSet):
    queryset = MACAddress.objects.all()
    serializer_class = serializers.MACAddressSerializer
    filterset_class = filtersets.MACAddressFilterSet

class ServiceSelectViewSet(CustomFieldModelViewSet):
    queryset = IXService.objects.all()
    serializer_class = serializers.IXServiceSerializer
    filterset_class = filtersets.ServiceFilterSet

class ServiceTypeSelectViewSet(CustomFieldModelViewSet):
    queryset = ServiceType.objects.all()
    serializer_class = serializers.ServiceTypeSerializer
    filterset_class = filtersets.ServiceTypeFilterSet

class CustomerConnectionSelectViewSet(CustomFieldModelViewSet):
    queryset = CustomerConnection.objects.all()
    serializer_class = serializers.CustomerConnectionSerializer
    filterset_class = filtersets.CustomerConnectionFilterSet


class CustomerConnectionTypeSelectViewSet(CustomFieldModelViewSet):
    queryset = CustomerConnectionType.objects.all()
    serializer_class = serializers.CustomerConnectionType
    filterset_class = filtersets.CustomerConnectionTypeFilterSet

class CustomerConnectionNameSelectViewSet(viewsets.ModelViewSet):
    queryset = AS.objects.all()
    serializer_class = serializers.CustomerConnectionNameSerializer
    # filterset_class = filtersets.CustomerConnectionTypeFilterSet

class InterfaceLagSelectViewSet(viewsets.ModelViewSet):
    queryset = Interface.objects.filter(type="lag")
    serializer_class = InterfaceSerializer
    # filterset_class = filtersets.CustomerConnectionTypeFilterSet
