from django.db import models
# from django_extensions.db.models import TimeStampedModel
from django.utils.translation import gettext as _
from django.dispatch import receiver
from django.urls import reverse
from django.db.models.signals import post_delete, post_save, pre_save
from django.db.models import Q, UniqueConstraint

# import do modelo do netbox
from netbox.models import ChangeLoggedModel
from netbox.models import NestedGroupModel, PrimaryModel
from dcim.models import Device, Interface, FrontPort, RearPort, CablePath
from utilities.querysets import RestrictedQuerySet

# importar validacoes
import ipaddress
from django.core.exceptions import ValidationError
from django.core.validators import (MaxLengthValidator, MaxValueValidator,
                                    MinLengthValidator, MinValueValidator)
from .utils.validators import (validate_as_number,
                         validate_ipv4_network, validate_ipv6_network,
                         validate_ix_code, validate_ix_fullname,
                         validate_ix_shortname, validate_mac_address,
                         validate_url_format, trace_print_exception)

from .utils.constants import (MAX_TAG_NUMBER, MIN_TAG_NUMBER)
from .utils.status import TagStatusChoices, ActiveStatusChoices


from extras.utils import extras_features

@extras_features('custom_fields', 'custom_links', 'export_templates')
class ChangeLoggingMixin(PrimaryModel):
    """
    Provides change logging support from netbox
    """
    description = models.CharField(
        max_length=200,
        blank=True
    )
    def _get_absolute_url(self, model_name):
        return reverse("plugins:ixservices:{}".format(model_name), kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):

        # Call clean validations before save.
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        abstract = True




class ActiveResourceModel(ChangeLoggingMixin):
   
    # define status for resources that need activation date 
    active_status = ActiveStatusChoices().CHOICES
    defaut_stattus = ActiveStatusChoices().STATUS_ACTIVATING
    active_status = models.CharField(choices=active_status, max_length=15, default=defaut_stattus)
    active_date = models.DateField(
        default=None,
        blank=True,
        null=True
    )

    def get_active_class(self):
        return ActiveStatusChoices().CSS_CLASSES.get(self.status)

    
    @property
    def is_active(self):
        return self.active_status == ActiveStatusChoices().STATUS_ACTIVE
    
    class Meta:
        abstract = True
    

class IX(ChangeLoggingMixin):
    """Internet Exchange (IX) site representation."""

    # netbox models
    objects = RestrictedQuerySet.as_manager()

    # create reference to Region
    region = models.ForeignKey(
        to='dcim.Region',
        on_delete=models.SET_NULL,
        verbose_name='NetBox Region',
        related_name='ix',
        blank=True,
        null=True
    )

    uuid = None
    code = models.CharField(
        max_length=4, unique=True,
        validators=[MinLengthValidator(2), MaxLengthValidator(4), validate_ix_code]
    )
    shortname = models.CharField(
        max_length=16, unique=True, 
        validators=[validate_ix_shortname]
    )
    fullname = models.CharField(
        max_length=48, 
        validators=[validate_ix_fullname]
    )
    ipv4_prefix = models.CharField(
        max_length=18, unique=True, 
        validators=[validate_ipv4_network]
    )
    ipv6_prefix = models.CharField(
        max_length=43, unique=True, 
        validators=[validate_ipv6_network]
    )

    # campos adicionados do hercules
    management_prefix = models.CharField(max_length=18, validators=[validate_ipv4_network], null=True)
    description = models.CharField(max_length=50, null=True, blank=True)
    TAGS_POLICIES = (('ix_managed', "IX_managed"), ('distributed', "Distributed"),)
    tags_policy = models.CharField(max_length=32, choices=TAGS_POLICIES, default='ix_managed')
    create_ips = models.BooleanField(default=True)
    create_tags = models.BooleanField(default=True)


    # permite a atualizaco dos prefixos
    prefix_update = False

    class Meta:
        ordering = ('code',)
        verbose_name = _('IX')
        verbose_name_plural = _('IXs')

    def __str__(self):
        return str(self.code)  
    
    def get_absolute_url(self):
        return self._get_absolute_url('ix')

    # ============== Prefixo de IPs ==================================================
    # rotinas para validacao, criacao e atualizacao dos prefixos importadas do Hercules
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_ipv4_prefix = self.ipv4_prefix
        self._original_ipv6_prefix = self.ipv6_prefix   

    def clean(self):
        # self.block_update_pk()
        self.validate_mgmt_network()
        self.validate_ip_network_intersect()
    
    # validacao do prefixo de gerencia do IX
    def validate_mgmt_network(self):
        if isinstance(ipaddress.ip_network(self.management_prefix),
                      ipaddress.IPv4Network):
            if not ipaddress.ip_network(self.management_prefix).is_private:
                raise ValidationError(_("{} is not a private network".
                                        format(self.management_prefix)))
        else:
            raise ValidationError(_("{} is not a IPv4 network".
                                    format(self.management_prefix)))
    
    # validacao da faixa de IPs entram em conflito com outros IX
    def validate_ip_network_intersect(self):
        current_v4 = ipaddress.ip_network(self.ipv4_prefix)
        current_v6 = ipaddress.ip_network(self.ipv6_prefix)
        for ix in IX.objects.all():
            if ix.code == self.code:
                continue
            other_v4 = ipaddress.ip_network(ix.ipv4_prefix)
            other_v6 = ipaddress.ip_network(ix.ipv6_prefix)
            if current_v4.overlaps(other_v4):
                raise ValidationError(_("{} overlaps with {} from IX: {}".
                                        format(current_v4, other_v4, ix)))
            if current_v6.overlaps(other_v6):
                raise ValidationError(_("{} overlaps with {} from IX: {}".
                                        format(current_v6, other_v6, ix)))

    def get_ipv4_network(self):
        return ipaddress.ip_network(self.ipv4_prefix)

    def get_ipv6_network(self):
        return ipaddress.ip_network(self.ipv6_prefix)

    def get_atmv4_services(self):
        return CustomerService.objects.filter(mlpav4_address__ix=self)

    def get_atmv6_services(self):
        return CustomerService.objects.filter(mlpav6_address__ix=self)

    
    # criar os IPs a aprtir do prefixo
    def create_ipv4(self, old_addresses=[]):
        """
        Create all IPv4Addresses that belong to this IX IPv4 prefix.
        Raises ValueError if one of those IPs already exist and is assigned
        to another IX.

        """
        prefix = self.get_ipv4_network()
        old_prefix = ipaddress.ip_network(self._original_ipv4_prefix)
        # verifica se a expansao do prefixo
        if prefix.overlaps(old_prefix) and prefix < old_prefix:
            new_addresses = (ip for ip in prefix.hosts()
                             if ip not in old_prefix.hosts())

            for address in new_addresses:
                IPv4Address.objects.create(address=str(address), ix=self)
        else:
            difference = int(prefix.network_address) - int(old_prefix.network_address)
            for address in old_addresses:
                ip_address = ipaddress.ip_address(address.address)
                IPv4Address.objects.create(address=str(ip_address + difference), ix=self, reverse_dns=address.reverse_dns)
            # If the new prefix is bigger, create the remaining addresses
            remaining = list(prefix.hosts())[len(old_addresses):]
            for address in remaining:
                IPv4Address.objects.create(address=str(address), ix=self)

    def map_new_address_ipv4(self, *services):
        """
        Change address of services to match new prefix. If the new prefix
        contains the old one, no alteration is made. Else, the new address of a
        given service is calculated by keeping the same offset from the old
        prefix.

        """
        prefix = self.get_ipv4_network()
        old_prefix = ipaddress.ip_network(self._original_ipv4_prefix)
        # verifica se a expansao do prefixo
        if prefix.overlaps(old_prefix) and prefix < old_prefix:
            return
        else:
            for service in services:
                service_address = ipaddress.ip_address(
                    service.get_address().address)
                offset = int(service_address) - int(old_prefix.network_address)
                new_address = prefix.network_address + offset
                service.set_address(
                    IPv4Address.objects.get(address=str(new_address)))
                service.save()


    def update_ips(self):
        """
        Called after an IX has one of its prefixes changed.
        Create new IP objects and change the address of its services
        for the new prefix. They are not changed if the new prefix contains the
        old one (expansion)

        """
        prefix = self.get_ipv4_network()
        old_prefix = ipaddress.ip_network(self._original_ipv4_prefix)
        if prefix != old_prefix:
            # libera validacoes para criacao dos novos ips
            self.prefix_update = True         
            #  If it's an expansion, just create new addresses without changing services address
            if prefix.overlaps(old_prefix) and prefix < old_prefix:
                self.create_ipv4()
            else:
                mlpa_v4_services = self.get_atmv4_services()
                # monitor_services = Monitorv4.objects.filter(monitor_address__ix=self)  --  modelo nao tuilizado no hercules
                old_addresses = list(IPv4Address.objects.filter(ix=self))
                self.create_ipv4(old_addresses)
                self.map_new_address_ipv4(*mlpa_v4_services)                
                # retorna validation error se os ips estiverem reservados
                for old_address in old_addresses:
                    old_address.delete()
            
            ### TODO cria os IPv6s 
            create_all_ips(self, True)

        prefix = self.get_ipv6_network()
        old_prefix = ipaddress.ip_network(self._original_ipv6_prefix)
        if prefix != old_prefix:
            mlpa_v6_services = self.get_atmv6_services()
            self.map_new_address_ipv4(*mlpa_v6_services)

        self.prefix_update = False


    



class AS(ChangeLoggingMixin):

    """Autonomous System (AS) Number representation."""
    uuid = None
    number = models.BigIntegerField(
        unique=True, 
        validators=[validate_as_number]
    )

    is_exempt = models.BooleanField(verbose_name='Is Exempt', default=False)

    # netbox models
    objects = RestrictedQuerySet.as_manager()
    
    class Meta:
        ordering = ('number',)
        verbose_name = _('AS')
        verbose_name_plural = _('ASs')

    def __str__(self):
        return str(self.number) 
    
    # ------- Validation Functions -------
    def validate_as_number(self,number):
        """AS validator."""
        # 16-bit range list
        s_bit_reserved_range = list(range(64496, 64512))
        s_bit_reserved_range.extend(list(range(64513, 65536)))
        # 32-bit range list
        t_bit_reserved_range = list(range(65536, 65551))
        if number < 1 or \
                number in s_bit_reserved_range or \
                number in t_bit_reserved_range or \
                number >= 4200000000:
            raise ValidationError(INVALID_ASN)

    
    def get_absolute_url(self):
        return self._get_absolute_url('as')


class ServiceTagDomain(ChangeLoggingMixin):

    ix = models.ForeignKey('IX',
        related_name="servicetagdomains",
        on_delete=models.PROTECT,
        # blank=True,
        # null=True
    )

    DOMAINS = (('IX-DOMAIN', 'IX'), ('DEVICE-DOMAIN', 'Device'), ('PORT-CHANNEL', 'Port Channel or Port'),)

    domain_type = models.CharField(choices=DOMAINS, max_length=15, default='IX-DOMAIN')

    device = models.ForeignKey(
        to='dcim.Device',
        on_delete=models.SET_NULL,
        verbose_name='NetbBox Device',
        related_name='servicetagdomains',
        blank=True,
        default=None,
        null=True
    )

    interface = models.OneToOneField(
        to='dcim.Interface',
        on_delete=models.SET_NULL,
        verbose_name='NetbBox Interface',
        related_name='servicetagdomains',
        blank=True,
        default=None,
        null=True
    )

    # fields to catalog ranges used exclusively for atm or bilateral
    vlan_range_atm = models.PositiveIntegerField(
        validators=[MinValueValidator(MIN_TAG_NUMBER), MaxValueValidator(MAX_TAG_NUMBER)],
        blank=True,
        null=True
    )

    vlan_range_bilateral = models.PositiveIntegerField(
        validators=[MinValueValidator(MIN_TAG_NUMBER), MaxValueValidator(MAX_TAG_NUMBER)],
        blank=True,
        null=True
    )
    

    # netbox models
    objects = RestrictedQuerySet.as_manager()

    class Meta:
        '''
        constraints = [
            UniqueConstraint(fields=['ix', 'device', 'interface'], name='%(app_label)s_%(class)s_unique_ix_device_interface'),
            UniqueConstraint(fields=['ix', 'device'], condition=Q(interface__isnull=True), name='%(app_label)s_%(class)s_unique_ix_device'),
            UniqueConstraint(fields=['ix'], condition=Q(device=None) & Q(interface=None), name='%(app_label)s_%(class)s_unique_ix')            
        ]'''
        unique_together = (('ix', 'device', 'interface'),)
        ordering = ('domain_type', 'ix', 'device', )
        verbose_name = ('ServiceTagDomain')
        verbose_name_plural = ('ServiceTagDomains')

    def __str__(self):
        return "%s - %s %s" % (
            self.ix.code,
            self.domain_type,
            "[%s %s]" % (self.device or '', self.interface or '') if self.device else ""
        )

    def get_absolute_url(self):
        return self._get_absolute_url('servicetagdomain')

    
    def validate_unique_ix(self):
        if ServiceTagDomain.objects.filter(Q(domain_type="IX-DOMAIN") & Q(ix=self.ix) & Q(device__isnull=True) & Q(interface__isnull=True)).exclude(pk=self.pk):
            raise ValidationError("ServiceTagDomain with this Ix already exists.")

    def validate_unique_ix_device(self):
        if ServiceTagDomain.objects.filter(Q(domain_type="DEVICE-DOMAIN") & Q(ix=self.ix) & Q(device=self.device) & Q(interface__isnull=True)).exclude(pk=self.pk):
            raise ValidationError("ServiceTagDomain with this Ix and NetbBox Device already exists.")
    
    def validate_unique_ix_device_interface(self):
        if ServiceTagDomain.objects.filter(Q(domain_type="PORT-CHANNEL") & Q(ix=self.ix) & Q(device=self.device) & Q(interface=self.interface)).exclude(pk=self.pk):
            raise ValidationError("ServiceTagDomain with this Ix, NetbBox Device and NetbBox Interface already exists.")
    
    @property
    def servicetags_count(self):
        return self.servicetags.count()
    
    def clean(self):       
        if self.device and self.interface:
            self.validate_unique_ix_device_interface()
        elif self.device:
            self.validate_unique_ix_device()
        else:
            self.validate_unique_ix()


    

class ServiceTag(ChangeLoggingMixin):

    tag = models.PositiveIntegerField(
        validators=[MinValueValidator(MIN_TAG_NUMBER), MaxValueValidator(MAX_TAG_NUMBER)]
    )
    # TODO: remover vinculo pois vai existir na tabela de dominios
    ix = models.ForeignKey('IX', models.PROTECT, null=True, blank=True)

    # tag_domain = models.CharField(max_length=50, verbose_name='Tag Domain', null=True, blank=True)
    tag_domain = models.ForeignKey('ServiceTagDomain', models.PROTECT, null=True, blank=True, related_name="servicetags")

    STATUSES = (('AVAILABLE', 'available'), ('ALLOCATED', 'allocated/reserved'), ('PRODUCTION', 'production'),)
    status = models.CharField(choices=STATUSES, max_length=10, default='AVAILABLE')

    # netbox models
    objects = RestrictedQuerySet.as_manager()

    # # related connection to determine type of tag_domains reserved to cix
    # connection = models.ForeignKey('CustomerConnection', 
    #     on_delete=models.SET_NULL, 
    #     related_name='servicetags',
    #     blank=True,
    #     null=True
    # )

    class Meta:
        # unique_together = (('tag', 'tag_domain'), )
        # unique_together = (('tag', 'ix',),)
        ordering = ('ix', 'tag', )
        verbose_name = ('ServiceTag')
        verbose_name_plural = ('ServiceTags')

    def __str__(self):
        return "[%s - %s (%s)]" % (
            self.tag,            
            self.status,
            self.tag_domain or ''
        )

    def get_absolute_url(self):
        return self._get_absolute_url('servicetag')

    def get_status_class(self):
        return TagStatusChoices().CSS_CLASSES.get(self.status)
    
    @property
    def customer_innertag_count(self):
        return self.customerservice.filter(inner_tag__isnull=False).count()

    @property
    def customerservice_count(self):
        return self.customerservice.count()

    

class CustomerConnectionType(ChangeLoggingMixin):
    '''
        Representa os tipos de CIX
    '''

    connection_name = models.CharField(blank=False, verbose_name='Connection Type', max_length=50)    
    connection_type = models.IntegerField(null=False, default=0, verbose_name='CIX Type')

    # netbox models
    objects = RestrictedQuerySet.as_manager()

    def __str__(self):
        return self.connection_name.__str__()   
    
    class Meta:
        ordering = ['connection_type']
        verbose_name = ('CustomerConnectionType')
        verbose_name_plural = ('CustomerConnectionTypes')

    def get_absolute_url(self):
        return self._get_absolute_url('customerconnectiontype')


class CustomerConnection(ActiveResourceModel):
    '''
        Representa ligacao fisica do AS ao IX
    '''

    STATUSES = (
        ('DEACTIVATION', 'Connection in deactivation'),
        ('ACTIVATION', 'Connection in activation'),
        ('QUARANTINE', 'Connection in test/quarantine'),
        ('PRODUCTION', 'Connection in production'),
        ('MIGRATION', 'Connection in migration'),
    )


    name = models.CharField(max_length=50)
    
    is_lag = models.BooleanField(verbose_name='Is a LAG', default=False, help_text='LAG')    

    asn = models.ForeignKey('AS', models.PROTECT, verbose_name=AS._meta.verbose_name)

    ticket = models.IntegerField(blank=True, null=True, verbose_name='Ticket')

    # vlan_domain = models.CharField(max_length=50, verbose_name='VLAN Domain')
    # configured_capacity = models.IntegerField(null=True, verbose_name='Capacidade', default=0)
    # interface = models.IntegerField(null=True, verbose_name='Interface no NetbBox')

    connection_type = models.ForeignKey('CustomerConnectionType',on_delete=models.PROTECT, related_name='customerconnection')

    tag_domain = models.ForeignKey('ServiceTagDomain', models.PROTECT, null=True, blank=True, related_name="customerconnections")

    status = models.CharField(choices=STATUSES, max_length=15, default='PRODUCTION')

    # netbox models
    objects = RestrictedQuerySet.as_manager()

    class Meta:
        ordering = ['asn','name']
        verbose_name = ('CustomerConnection')
        verbose_name_plural = ('CustomerConnections')
        unique_together = (('asn', 'name',),)

    def __str__(self):
        # lag = ' (LAG)' if self.is_lag else ''
        return "[AS%s] [%s]" % (self.asn.number, self.name) #, lag)
    
    '''
    def clean(self):
        self.customerconnectionendpoint.filter(
                Q(interface__isnull=False) | Q(rearport__isnull=False) | Q(frontport__isnull=False)
            ).first()
        raise ValidationError(_("{} master port has nos association with him".
                               format(self.name)))
    '''   

    @property
    def full_name(self):
        lag = '(LAG)' if self.is_lag else ''
        obj, device = self._get_device_connected()
        name = 'NOT CONNECTED' if not device else device
        return "[AS%s] [%s] [%s]" % (self.asn.number, self.name, name)

    @property
    def _name(self):
        return self.__str__()

    def _get_device_connected(self):
        try:
            cc_endpoints = self.customerconnectionendpoint.filter(
                Q(interface__isnull=False) | Q(rearport__isnull=False) | Q(frontport__isnull=False)
            )          
            conditions = Q()
            for ept in cc_endpoints:
                obj = ept.rearport or ept.frontport or ept.interface
                if isinstance(obj, Interface):
                    return obj, obj.device
                conditions |= Q(path__contains=obj)
            if cc_endpoints: 
                # define objetos conectados ao mesmo site               
                _obj = self.customerconnectionendpoint.first()
                _obj = _obj.rearport or ept.frontport or ept.interface
                # objetos connectados aos dios ou interface
                _connected =  CablePath.objects.filter(conditions)
                # origem dos cabos a partir de interfaces
                _interfaces_ids = _connected.filter(origin_type=5).values_list("origin_id", flat=True)
                # interfaces no mesmo site dos dios
                interface_connected = Interface.objects.filter(pk__in=_interfaces_ids, device__site=_obj.device.site).first()
                return _obj, interface_connected.device if interface_connected else None
            else:
                return (None,None)
        except Exception as e:
            return (None,None)


    def _get_device_origin_and_destination(self):
        try:
            _connected = self._get_device_connected()

            return {
                "pix_id": _connected[1].site.id if _connected[1] else _connected[0].device.site.id,
                "pix": _connected[1].site.name if _connected[1] else _connected[0].device.site.name,
                "device_id_origin": _connected[0].device.id,
                "device_name_origin": _connected[0].device.name,
                "device_slug_origin": _connected[0].device.device_role.slug,
                ####
                "device_id_destination": _connected[1].id if _connected[1] else None,
                "device_name_destination": _connected[1].name if _connected[1] else None,
                "device_ip_destination": str(_connected[1].primary_ip4.address) if _connected[1] else None,
                "device_slug_destination": _connected[1].device_role.slug if _connected[1] else None,
            }

            # cc_endpoints = self.customerconnectionendpoint.filter(
            #     Q(interface__isnull=False) | Q(rearport__isnull=False) | Q(frontport__isnull=False)
            # )
            # conditions = Q()
            # for ept in cc_endpoints:
            #     obj = ept.rearport or ept.frontport or ept.interface
            #     if isinstance(obj, Interface):
            #         return {
            #             "pix_id": obj.device.site.id,
            #             "pix": obj.device.site.name,
            #             "device_id": obj.device.id,
            #             "device_name": obj.device.name,
            #             "device_ip": str(obj.device.primary_ip4.address),
            #             "device_slug": obj.device.device_role.slug
            #         }
            #         # return obj.device
            #     conditions |= Q(path__contains=obj)
            # if cc_endpoints:
            #     _connected =  CablePath.objects.filter(conditions).first()
            #     return {
            #         "pix_id": _connected.origin.device.site.id if _connected else obj.device.site.id,
            #         "pix": _connected.origin.device.site.name if _connected else obj.device.site.name,
            #         "device_id_origin": obj.device.id,
            #         "device_name_origin": obj.device.name,
            #         "device_slug_origin": obj.device.device_role.slug,
            #         ####
            #         "device_id_destination": _connected.origin.device.id if _connected else None,
            #         "device_name_destination": _connected.origin.device.name if _connected else None,
            #         "device_ip_destination": str(_connected.origin.device.primary_ip4.address) if _connected else None,
            #         "device_slug_destination": _connected.origin.device.device_role.slug if _connected else None,
            #     }
            #     # return _connected.origin.device if _connected else None
            # else:
            #     return
        except Exception as e:
            return


    def _get_interface_connected(self):
        try:
            endpoints = []

            cc_endpoints = self.customerconnectionendpoint.filter(
                Q(interface__isnull=False) | Q(rearport__isnull=False) | Q(frontport__isnull=False)
            ).order_by('id')

            for ept in cc_endpoints:
                obj = ept.rearport or ept.frontport or ept.interface
                if isinstance(obj, Interface):
                    endpoints.append({
                        "ccendpointId": ept.id,
                        "configured_capacity": ept.configured_capacity,
                        "port_id": obj.id,
                        "port_name": obj.name,
                        "port_type": obj.type,
                        "device_id": obj.device.id,
                        "device_name": obj.device.name,
                        "device_slug": obj.device.device_role.slug,
                        "status": ept.status,
                    })
                    continue
                else:
                  _connected =  CablePath.objects.filter(path__contains=obj).first()
                  endpoints.append({
                    "ccendpointId": ept.id,
                    "configured_capacity": ept.configured_capacity,
                    "port_id_origin": obj.id,
                    "port_name_origin": obj.name,
                    "port_type_origin": obj.type,
                    "port_id_destination": _connected.origin.id if _connected else None,
                    "port_name_destination": _connected.origin.name if _connected else None,
                    "port_type_destination": _connected.origin.type if _connected else None,
                    "device_id_origin": obj.device.id,
                    "device_name_origin": obj.device.name,
                    "device_slug_origin": obj.device.device_role.slug,
                    "device_id_destination": _connected.origin.device.id if _connected else None,
                    "device_name_destination": _connected.origin.device.name if _connected else None,
                    "device_slug_destination": _connected.origin.device.device_role.slug if _connected else None,
                    "status": ept.status,
                  })

            return endpoints if len(endpoints)>0 else None

        except Exception as e:
            return None


    def _get_connected_endpoint(self, instance):
        try:
            if isinstance(instance, Interface):
                return instance.device
            elif isinstance(instance, RearPort) or isinstance(instance, FrontPort):
                return CablePath.objects.filter(path__contains=instance).first().origin.device
        except Exception as e:
            return None



    @property
    def connected_device(self):
        obj, _connected = self._get_device_connected()
        return _connected

    @property
    def connected_device_info(self):
        device = self._get_device_origin_and_destination()
        return device if device else None

    @property
    def connected_interfaces(self):
        interface = self._get_interface_connected()
        return interface if interface else None

    @property
    def connected_device_id(self):
        obj, device = self._get_device_connected()
        return device.id if device else None

    @property
    def connected_device_id(self):
        obj, device = self._get_device_connected() 
        return device.pk if device else None

    @property
    def destination_device_info(self):
        obj, device = self._get_device_connected()
        return {
            "id": device.id,
            "name": device.name,
            "pix_id": device.site.id,
            "pix": device.site.name,
        } if device else None

    @property
    def device_id_by_interface(self):
        device = self.connected_device_by_interface()
        return device.id if device else None
    
    def connected_device_by_interface(self):
        try:
            device_id = self.customerconnectionendpoint.order_by().values_list("interface__device", flat=True).distinct().first()
            return Device.objects.get(pk=device_id) if device_id else None
        except Exception as e:
            # raise ValidationError(f"{str(e)}")
            return 

    @property
    def customerconnectionendpoint_count(self):
        return self.customerconnectionendpoint.count()

    @property
    def customerservice_count(self):
        return self.customerservice.count()

    @property
    def tagdomain(self):
        return {
            'id': self.tag_domain.id,
            'domain_type': self.tag_domain.domain_type,
        }

    # @property
    # def tag_domain(self):        
    #     try:
    #         device = self._get_device_connected()
    #         if device:
    #             # verifica se existe um dominio exclusivo por IX
    #             ix = device.site.region.ix.first()
    #             ix_domain = ix.servicetagdomains.filter(domain_type="IX-DOMAIN").first()
    #             if ix and ix_domain:
    #                 return ix_domain
    #             elif device.device_role.name == "PE":
    #                 return self.servicetagdomains.filter(domain_type="PORT-CHANNEL").first()
    #             elif device.device_role.name == "Layer2":
    #                 return self.servicetagdomains.filter(domain_type="PORT-CHANNEL").first()
    #     except Exception:
    #         return

    def _get_tagdomain_by_device(self):

        try:
            device = self.connected_device_by_interface()
            if device:
                ix = device.site.region.ix.first()
                ix_domain = ix.servicetagdomains.filter(domain_type="IX-DOMAIN").first()
                # verifica se a conexao direta no PE
                if device.device_role.name == "PE":
                    pe_ports = self.customerconnectionendpoint.order_by().values_list("interface", flat=True)
                    tag_domain = ServiceTagDomain.objects.filter(domain_type="PORT-CHANNEL", device=device, interface__pk__in=pe_ports).first()
                    return tag_domain or ix_domain

                elif device.device_role.name == "Layer2":
                    l2_uplinks = device.interfaces.filter(custom_field_data__InterfaceRole="Uplink")
                    if l2_uplinks:
                        l2_uplinks = l2_uplinks.values_list("_link_peer_id", flat=True)
                        # filtra portas de uplink do PE no mesmo PIX
                        pe_uplinks = Interface.objects.filter(
                            pk__in=l2_uplinks, 
                            device__site=device.site, 
                            device__device_role__name="PE"
                        )
                        pe = pe_uplinks.order_by().values_list("device", flat=True).distinct().first()
                        if pe and pe_uplinks:
                            tag_domain = ServiceTagDomain.objects.filter(domain_type="PORT-CHANNEL", device__pk=pe, interface__pk__in=pe_uplinks).first()
                            return tag_domain or ix_domain
                    else:
                        
                        device_domain = ServiceTagDomain.objects.filter(domain_type="DEVICE", device=device, interface__isnull=True).first()
                        if not device_domain:
                            l2_ports = self.customerconnectionendpoint.order_by().values_list("interface", flat=True)
                            tag_domain = ServiceTagDomain.objects.filter(domain_type="PORT-CHANNEL", device=device, interface__pk__in=l2_ports).first()
                            return tag_domain or ix_domain                        
                        return  device_domain or ix_domain

        except Exception as e:
            raise ValidationError(f"{str(e)}")
            # a, b, c = trace_print_exception()
            # raise ValidationError(f"{a}\n{b}\n{c}")


    def get_absolute_url(self):
        return self._get_absolute_url('customerconnection') 


class CustomerConnectionEndpoint(ActiveResourceModel):

    STATUSES = (
        ('DEACTIVATION', 'Connection in deactivation'),
        ('ACTIVATION', 'Connection in activation'),
        ('QUARANTINE', 'Connection in test/quarantine'),
        ('PRODUCTION', 'Connection in production'),
        ('MIGRATION', 'Connection in migration'),
    )


    customer_connection = models.ForeignKey(
        to='CustomerConnection',
        on_delete=models.CASCADE,
        related_name='customerconnectionendpoint',
        blank=True,
        null=True
    )

    # interface = models.IntegerField(null=True, verbose_name='Interface no NetbBox')
    interface = models.OneToOneField(
        to='dcim.Interface',
        on_delete=models.SET_NULL,
        verbose_name='NetbBox Interface',
        related_name='customerconnectionendpoint',
        blank=True,
        null=True
    )

    # frontport modelo que faz vinculo com device
    frontport = models.OneToOneField(
        to='dcim.FrontPort',
        on_delete=models.SET_NULL,
        verbose_name='NetbBox FrontPort',
        related_name='customerconnectionendpoint',
        blank=True,
        null=True
    )

     # rearport modelo que faz vinculo com device
    rearport = models.OneToOneField(
        to='dcim.RearPort',
        on_delete=models.SET_NULL,
        verbose_name='NetbBox RearPort',
        related_name='customerconnectionendpoint',
        blank=True,
        null=True
    )

    # campos para importacao
    port_name = models.CharField(max_length=255, blank=True, null=True)
    switch_ip = models.GenericIPAddressField('Switch IP', blank=True, null=True)
    dio_position = models.CharField(max_length=255, blank=True, null=True)
    dio_pix = models.CharField(max_length=255, blank=True, null=True)

    configured_capacity = models.IntegerField(null=True, verbose_name='Capacidade', default=0)

    status = models.CharField(choices=STATUSES, max_length=15, default='PRODUCTION')

    # netbox models
    objects = RestrictedQuerySet.as_manager()

    class Meta:
        ### TODO: remover esse indice switch_ip e add para rearport-device, frontport-device
        unique_together = (('switch_ip', 'port_name',),
                           ('customer_connection', 'interface',))
        # ordering = ('switch_ip',)
        verbose_name = ('CustomerConnectionEndpoint')
        verbose_name_plural = ('CustomerConnectionEndpoints')


    def __str__(self):
        try:
            return self.customer_connection.__str__()
        except Exception as e:
            return "[NO CUSTOMERCONNECTION ASSOCIATED]"
        

    @property
    def device(self):
        try:
            device = (self.rearport or self.frontport or self.interface).device
        except Exception as e:
            device = None
        return device
    
    @property
    def connected_device(self):
        return self._get_device_connected() 
    
    def _get_device_connected(self):
        try:
            obj = self.rearport or self.frontport or self.interface
            if isinstance(obj, Interface):
                return self.interface
            elif isinstance(obj, RearPort) or isinstance(obj, FrontPort):
                return CablePath.objects.filter(path__contains=obj).first().origin.device
        except Exception as e:
            return None

    def _get_connected_endpoint(self, instance):
        try:
            if isinstance(instance, Interface):
                return instance.device
            elif isinstance(instance, RearPort) or isinstance(instance, FrontPort):
                return CablePath.objects.filter(path__contains=instance).first().origin.device
        except Exception as e:
            return None

    def get_absolute_url(self):
        return self._get_absolute_url('customerconnectionendpoint')



class ServiceType(ChangeLoggingMixin):
    '''
        Representa os tipos de servicos (MPLAv4, MPLAv6 e VLANs)
    '''

    name = models.CharField(blank=False, verbose_name='Service Type', unique=True, max_length=50)
    num_clients = models.IntegerField(null=True, verbose_name='Number of clients allowed')

    # netbox models
    objects = RestrictedQuerySet.as_manager()

    def __str__(self):
        return self.name    
    
    class Meta:
        ordering = ['name', 'num_clients']
        verbose_name = ('ServiceType')
        verbose_name_plural = ('ServiceTypes')

    def get_absolute_url(self):
        return self._get_absolute_url('servicetype')
            


class IXService(ChangeLoggingMixin):
    '''
        Representa os servicos (MPLAv4, MPLAv6 e VLANs)
    '''

    service_type = models.ForeignKey('ServiceType',on_delete=models.PROTECT, related_name='service')
    name = models.CharField(blank=False, verbose_name='Service Name', unique=True, max_length=50)
    label = models.CharField(blank=False, verbose_name='Service Label', null=True, max_length=50)
    ix = models.ForeignKey('IX', models.PROTECT, related_name='service')

    # netbox models
    objects = RestrictedQuerySet.as_manager()

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['service_type', 'name']
        verbose_name = ('IXService')
        verbose_name_plural = ('IXServices')

    def get_absolute_url(self):
        return self._get_absolute_url('ixservice')


class MACAddress(ChangeLoggingMixin):
    """MAC address related to a service."""
    uuid = None
    address = models.CharField(
        unique=True, max_length=17, 
        # validators=[validate_mac_address]
    )

    # netbox models
    objects = RestrictedQuerySet.as_manager()

    class Meta:
        ordering = ('address',)
        verbose_name = _('MACAddress')
        verbose_name_plural = _('MACAddresses')

    def __str__(self):
        return "[%s]" % (self.address,)

    def get_absolute_url(self):
        return self._get_absolute_url('macaddress')


class IPv4Address(ChangeLoggingMixin):
    """Global IPv4 address to be used in IX' services."""
    uuid = None
    ix = models.ForeignKey('IX', models.PROTECT, related_name='ipv4address')
    address = models.GenericIPAddressField(
        'IPv4', unique=True, validators=[validate_ipv4_network]
    )
    reverse_dns = models.CharField(
        max_length=255, blank=True, validators=[validate_url_format]
    )

    # netbox models
    objects = RestrictedQuerySet.as_manager()

    class Meta:
        ordering = ('address',)
        verbose_name = _('IPv4Address')
        verbose_name_plural = _('IPv4Addresses')

    def __str__(self):
        return "[%s]" % (self.address)

    def get_absolute_url(self):
        return self._get_absolute_url('ipv4address')

    @property
    def status(self):
        return self.get_status()

    @property
    def is_allocated(self):
        return self.get_allocated()
    
    def get_allocated(self):
        return CustomerService.objects.filter(mlpav4_address=self, mlpav4_address__ix=self.ix).count() > 0

    def get_status(self):
        return 'ALLOCATED' if self.get_allocated() else 'FREE'


class IPv6Address(ChangeLoggingMixin):
    """Global IPv6 address to be used in IX' services."""
    uuid = None
    ix = models.ForeignKey('IX', models.PROTECT, related_name='ipv6address')
    address = models.GenericIPAddressField(
        'IPv6', unique=True, validators=[validate_ipv6_network]
    )
    reverse_dns = models.CharField(
        max_length=255, blank=True, validators=[validate_url_format]
    )

    # netbox models
    objects = RestrictedQuerySet.as_manager()
   
    class Meta:
        ordering = ('address',)
        verbose_name = _('IPv6Address')
        verbose_name_plural = _('IPv6Addresses')

    def __str__(self):
        return "[%s]" % (self.address)

    def get_absolute_url(self):
        return self._get_absolute_url('ipv6address')

    @property
    def status(self):
        return self.get_status()

    @property
    def is_allocated(self):
        return self.get_allocated()
    
    def get_allocated(self):
        return CustomerService.objects.filter(mlpav6_address=self, mlpav6_address__ix=self.ix).count() > 0

    def get_status(self):
        return 'ALLOCATED' if self.get_allocated() else 'FREE'
    

class CustomerService(ActiveResourceModel):

    service = models.ForeignKey('IXService', on_delete=models.CASCADE, null=True, blank=True, related_name='customerservice')
    asn = models.ForeignKey('AS', on_delete=models.CASCADE, related_name='customerservice')
    
    connection = models.ForeignKey('CustomerConnection', on_delete=models.PROTECT, related_name='customerservice')
    mac_address = models.ManyToManyField('MACAddress', related_name='customerservice', null=True, blank=True)
    
    # campos de tags
    inner_tag = models.IntegerField(null=True,blank=True, validators=[MinValueValidator(MIN_TAG_NUMBER), MaxValueValidator(MAX_TAG_NUMBER)])  
    tag_or_outer = models.ForeignKey('ServiceTag', models.PROTECT, null=True, blank=True, related_name='customerservice')
    
    # campos de IPS
    mlpav4_address = models.OneToOneField('IPv4Address', models.PROTECT, null=True, blank=True)
    mlpav6_address = models.OneToOneField('IPv6Address', models.PROTECT, null=True, blank=True)  
    
    # add campo de ticket
    ticket = models.IntegerField(null=True, verbose_name='Ticket')

    # netbox models
    objects = RestrictedQuerySet.as_manager()
    
    class Meta:
        ordering = ['asn', 'service', 'connection', 'tag_or_outer','inner_tag']
        verbose_name = ('CustomerService')
        verbose_name_plural = ('CustomerServices')
        unique_together = (('connection', 'tag_or_outer', 'inner_tag',),)
        

    def __str__(self):
        return str(self.asn) + " - " + self.service.__str__()

    def get_address(self):
        try:
            if self.service.service_type == ServiceType.objects.get(name="ATMv4"):
               return self.mlpav4_address
            if self.service.service_type == ServiceType.objects.get(name="ATMv6"):
               return self.mlpav6_address
        except:
            raise ValidationError(_("Not a valid IPAddress for CustomerService"))

    def set_address(self, address):
        try:
            if self.service.service_type == ServiceType.objects.get(name="ATMv4"):
               self.mlpav4_address = address

            if self.service.service_type == ServiceType.objects.get(name="ATMv6"):
               self.mlpav6_address = address
        except:
            raise ValidationError(_("Not a valid IPAddress for CustomerService"))
    
    def get_mac_address(self):
        return self.mac_address.all() if self.mac_address.all().count() > 0 else None


    def get_absolute_url(self):
        return self._get_absolute_url('customerservice')
    
    @property
    def service_tag(self):
        inner = ' : ' + str(self.inner_tag) if self.inner_tag else ''
        return str(self.tag_or_outer.tag) + inner

    @property
    def tag_domain_id(self):
        return self.tag_or_outer.tag_domain.pk if self.tag_or_outer else None

    def _validate_v4_v6_service_and_tag(self):
        if not self.pk:
            if self.tag_or_outer.status in ["ALLOCATED", "PRODUCTION"]:
                if not self.inner_tag:
                    raise ValidationError("*** ServiceTag status is not AVAILABLE ****")
                elif self.tag_or_outer.status in ["ALLOCATED", "PRODUCTION"] and self.tag_or_outer.customerservice.exclude(asn=self.asn).first():
                    raise ValidationError("*** ServiceTag is not ASSOCIATED with CustomerService ****")
                elif self.tag_or_outer.customerservice.filter(inner_tag=self.inner_tag).first():
                    raise ValidationError("*** InnerTag is already ASSOCIATED with CustomerService ****")
        else:
            if self.tag_or_outer.status in ["ALLOCATED", "PRODUCTION"]:
                if not self.tag_or_outer.customerservice.filter(pk=self.pk).first():
                    raise ValidationError("*** ServiceTag is not ASSOCIATED with CustomerService ****")
                elif self.tag_or_outer.customerservice.exclude(asn__number=self.asn.number).first():
                    raise ValidationError("*** ServiceTag is not ASSOCIATED with CustomerService ****")
                elif self.inner_tag and self.tag_or_outer.customerservice.exclude(pk=self.pk).filter(inner_tag=self.inner_tag).first():
                    raise ValidationError("*** InnerTag is already ASSOCIATED with CustomerService ****")

    
    def _validate_bilateral_service_and_tag(self):
        if not self.pk:
            if self.tag_or_outer.status in ["ALLOCATED", "PRODUCTION"]:
                if not self.tag_or_outer.customerservice.filter(service=self.service).first():
                    raise ValidationError("*** ServiceTag is not ASSOCIATED with CustomerService ****")
                if self.inner_tag and self.service.customerservice.filter(inner_tag=self.inner_tag).first():
                    raise ValidationError("*** InnerTag is already ASSOCIATED with CustomerService ****")
        else:
            if self.tag_or_outer.status in ["ALLOCATED", "PRODUCTION"]:
                if not self.tag_or_outer.customerservice.filter(pk=self.pk).first():
                    raise ValidationError("*** ServiceTag is not ASSOCIATED with CustomerService ****")
                if self.inner_tag and self.service.customerservice.exclude(pk=self.pk).filter(inner_tag=self.inner_tag).first():
                    raise ValidationError("*** InnerTag is already ASSOCIATED with CustomerService ****")

            


    
    ''''
    def get_instance_tag(ix, tag, customer_connection):
        free_tags = get_free_tags(customer_connection=customer_connection, ix=ix).filter(tag=tag)
        if len(free_tags) == 0:
            return instantiate_tag(customer_connection=customer_connection, ix=ix, tag_number=tag)
        return free_tags.first()
    '''

    
    







###############################################################################
###############################################################################
########################## BUSINESS RULES FUNCTIONS ###########################
###############################################################################
###############################################################################


def create_all_ips(instance, IPv6Only=False):
    # Get the first subnetwork /24 in the ipv4_prefix field
    first_sub_network_v4 = list(ipaddress.ip_network(instance.ipv4_prefix).subnets(new_prefix=24))[0]
    ip_v6 = None

    for ip in ipaddress.ip_network(instance.ipv4_prefix).hosts():
        # For each IPv4 in ipv4_prefix create the respective IP.
        ### TODO adicionada a flag para apenas IPv6
        if not IPv6Only:
            IPv4Address.objects.create(ix=instance, address=str(ip))

        # For each IPv4 create a respective IPv6 with the same final visual
        # number. (IPv4 v.w.y.x IPv6 final ::0.x)
        ip_v6 = ipaddress.ip_network(instance.ipv6_prefix)[0] + int(str(ip).split('.')[-1], 16)
        # If IPv4 is in the first block /24 create IPv6
        # with final ::y.x IPv4 v.w.y.x
        if ip not in first_sub_network_v4:
            ip_v6 += 65536*int(str(ip).split('.')[-2], 16)
        
        ### TODO adicionada a flag para apenas IPv6
        if not IPv6Only:
            IPv6Address.objects.create(ix=instance, address=str(ip_v6))
        else:
            try:
                IPv6Address.objects.create(ix=instance, address=str(ip_v6))
            except ValidationError:
                continue
                # IPv6Address.objects.filter(pk=str(ip_v6)).update(
                #    address=str(ip_v6))


def create_all_tags_by_ix(instance, limit):
     # validate ServicetagDomain for IX
    try:
        ix_domain = ServiceTagDomain.objects.create(
            domain_type = 'IX-DOMAIN',
            ix = instance
        )

        for n_tag in range(0, limit):
            if n_tag == 0 or n_tag == 1:
                status = 'ALLOCATED'
            else:
                status = ServiceTag._meta.get_field('status').get_default()       

            ServiceTag.objects.create(tag=n_tag, ix=instance, status=status, tag_domain=ix_domain)

    except Exception as e:
        print(e)
        pass
    


# This post_save for the IX model, call a method for
# create all ips (v4 and v6) following some rules.
@receiver(post_save, sender=IX)
def create_ips(sender, instance, **kwargs):
    if kwargs['created'] and not kwargs['raw']:
        if instance.create_ips:
            create_all_ips(instance)


# This post_save for the IX model, call a method for
# update ips following some rules.
@receiver(post_save, sender=IX)
def update_ips(sender, instance, update_fields, **kwargs):
    if not kwargs['created'] and not kwargs['raw']:
        if instance and instance.create_ips:
            instance.update_ips()


# This post_save for the IX model, call a method for
# create all tags possible (0 - 4095).
@receiver(post_save, sender=IX)
def create_tags_ix(sender, instance, **kwargs):
    if kwargs['created'] and not kwargs['raw']:
        if instance.create_tags and instance.tags_policy == 'ix_managed':
            create_all_tags_by_ix(instance,
                                  MAX_TAG_NUMBER-MIN_TAG_NUMBER+1)



## reveicers to mark interface, rearport or frontport connected
@receiver(post_save, sender=CustomerConnectionEndpoint)
def mark_connected(sender, instance, **kwargs):
    if kwargs['created']:
        if instance.rearport or instance.frontport or instance.interface:
            obj_connected = instance.rearport or instance.frontport or instance.interface
            obj_connected.mark_connected = True
            obj_connected.save()

## reveicers to mark interface, rearport or frontport discconnected
@receiver(post_delete, sender=CustomerConnectionEndpoint)
def mark_disconnected(sender, instance, **kwargs):
    if instance.rearport or instance.frontport or instance.interface:
        obj_connected = instance.rearport or instance.frontport or instance.interface
        obj_connected.mark_connected = False
        obj_connected.save()



## receivers to associate Tag from domain to service

## receivers to validate tag (free tag or tag associated with service), 
# tag_domain (associated with ix, device or portchannel)
@receiver(pre_save, sender=CustomerService)
def get_or_create_tag_by_domain_pre(sender, instance, **kwargs):

    if instance.tag_or_outer:
        tag_or_outer = instance.tag_or_outer
        ix = instance.service.ix
        # verifica se a localidade e dominio dos servicos sao iguais
        if tag_or_outer.tag_domain.ix != ix:
            raise ValidationError("*** IX for Service and ServiceTagDomain dont match ***")
        
        #TODO: validar innertags v4,v6 e bilateral
        if instance.service and instance.service.service_type.name.lower() == "bilateral":
            # valida criacao do service do tipo bilateral
            customer_services = tag_or_outer.customerservice.filter(service__service_type=instance.service.service_type)
            if customer_services.count() == 2:
                if not instance.pk and not instance.inner_tag:
                    raise ValidationError("*** ServiceTag not available for ServiceType requested ***")
                if customer_services.exclude(asn=instance.asn).count() == 2:
                    raise ValidationError("*** ServiceTag not available for ServiceType requested ***")
            if not instance.pk:
                customer_services = instance.service.customerservice  
                if customer_services.count() == 0 or customer_services.exclude(asn=instance.asn).count() == 1:
                    service = instance.service
                    peer_asn = customer_services.exclude(asn=instance.asn).first() or ''
                    peer_asn = f'{peer_asn.asn.number}-as' if peer_asn else ''
                    try:
                        # cria o service utilizando o nome da origin e peer dos asn
                        service_name = f'{tag_or_outer.tag_domain.ix.code}-as{peer_asn}{instance.asn.number}'
                        service.name = service_name
                        service.save()
                    except:
                        # verifica bilaterais para o mesmo as duplicadas no name
                        ixservices_count = IXService.objects.filter(name__startswith=service_name).count()
                        service_name = f'{tag_or_outer.tag_domain.ix.code}-as{peer_asn}{instance.asn.number}-{ixservices_count}'
                        service.name = service_name
                        service.save()
                # instance.service = service
            # validacao das tag e inner tags
            instance._validate_bilateral_service_and_tag()
        else:
            instance._validate_v4_v6_service_and_tag()
     

# ## receivers to validate change tag status after tag is associated wiht service
@receiver(post_save, sender=CustomerService)
def get_or_create_tag_by_domain_post(sender, instance, **kwargs):
    if kwargs['created'] and instance.service.service_type.name.lower() == "bilateral":
        IXService.objects.get_or_create(
            name = f'Bilateral-{instance.tag_or_outer.tag_domain.ix.code}',
            service_type = instance.service.service_type,
            ix = instance.tag_or_outer.tag_domain.ix,
            label = 'Bilateral'
        )
    if instance.tag_or_outer and instance.tag_or_outer.status == "AVAILABLE":
        tag_or_outer = instance.tag_or_outer
        tag_or_outer.status = "PRODUCTION"
        tag_or_outer.save()



## reveicers to change status from production tags
@receiver(post_delete, sender=CustomerService)
def change_tag_status_post_delete(sender, instance, **kwargs):
    if instance.tag_or_outer and instance.tag_or_outer.status == "PRODUCTION":
        tag_or_outer = instance.tag_or_outer
        if tag_or_outer.customerservice.all().count() == 0:
            tag_or_outer.status = "AVAILABLE"
            tag_or_outer.save()




@receiver(pre_save, sender=CustomerConnection)
def get_or_create_tag_domain_pre(sender, instance, **kwargs):
    if instance.pk:
        instance.tag_domain = instance._get_tagdomain_by_device()

@receiver(post_save, sender=CustomerConnection)
def get_or_create_tag_domain_post(sender, instance, **kwargs):

    if not instance.tag_domain:
        # validar a criacao de dominio quando n existir
        pass

                
        
            
                
                


 