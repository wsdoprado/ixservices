

from django.db.models import Q
from django.utils.translation import gettext as _
from ixservices.ixservices.models import ServiceTag, ServiceTagDomain, CustomerConnection



def get_free_tags(**kwargs):
    """ gets the free TAGs to be allocated 
    """
    ix = kwargs.pop('ix')
    customer_connection = kwargs.pop('customer_connection')

    try:
        ix = IX.objects.get(pk=ix)
    except Exception:
        raise ValueError(_("IX doesn't exist"))

    if ix.tags_policy == 'ix_managed':
        tag_domain = ServiceTagDomain.filter(ix=ix, device__isnull=True, interface__isnull=True).first()
        if not tag_domain:
            raise ValueError(_("No ServiceTagDomain Associated with IX"))
        ## get free tags in ix domain
        free_tags = ServiceTag.objects.filter(
            ix=ix, status='AVAILABLE', tag_domain=tag_domain).order_by('tag')

    else:

        try:
            customer_connection = CustomerConnection.objects.get(pk=customer_connection)
        except Exception:
            raise ValueError(_("CustommerConnection doesn't exist"))
        
        device = customer_connection.connected_device

        if not device:
            raise ValueError(_("No Device Associated with CustommerConnection"))
         
        ## filter tagdommain by device
        ## TODO: Domains by Interface???
        tag_domain = ServiceTagDomain.filter(ix=ix, device=device).first()

        free_tags = ServiceTag.objects.filter(
            ix=ix,
            tag_domain=tag_domain,
            status='AVAILABLE').order_by('tag')
            
        ''''
        if channel.channel_port.tags_type == 'Direct-Bundle-Ether':
            if len(free_tags) <= 1 and pe_channel:
                if(Tag.objects.filter(tag_domain=tag_domain).count() <=
                        MAX_TAG_NUMBER - MIN_TAG_NUMBER):
                    create_tag_by_channel_port(tag_domain, False, 2)
                    free_tags = get_free_tags(ix=ix, channel=channel)
        '''

    return free_tags