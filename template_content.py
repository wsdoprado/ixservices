from extras.plugins import PluginTemplateExtension
from django.core.exceptions import ObjectDoesNotExist
# from ixservices.ixservices.models import CustomerConnection

class BasePluginExtensionView(PluginTemplateExtension):

    def right_page(self):        
        try:
            ref_object = self.context["object"]            
            connectionendpoint = ref_object.customerconnectionendpoint
            customerconnection = ref_object.customerconnectionendpoint.customer_connection
            customerservice_count = customerconnection.customerservice_count
        except ObjectDoesNotExist:
            customerconnection = None
            connectionendpoint = None
            customerservice_count = None

        return self.render('ixservices/customerconnection/interfacecustomerconnection.html', extra_context={
            'customerservice_count': customerservice_count,
            'customerconnection' : customerconnection,
            'customerconnectionendpoint': connectionendpoint
        })


class InterfaceCustomerConnectionView(BasePluginExtensionView):
    model = 'dcim.interface'

class RearportCustomerConnectionView(BasePluginExtensionView):
    model = 'dcim.rearport'

class FrontportCustomerConnectionView(BasePluginExtensionView):
    model = 'dcim.frontport'


template_extensions = [InterfaceCustomerConnectionView, RearportCustomerConnectionView, FrontportCustomerConnectionView]


