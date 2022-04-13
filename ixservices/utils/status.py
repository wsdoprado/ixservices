# from utilities.choices import ChoiceSet


class TagStatusChoices(object):

    def __init__(self):

        self.STATUS_AVAILABLE = 'AVAILABLE'
        self.STATUS_ALLOCATED = 'ALLOCATED'
        self.STATUS_PRODUCTION = 'PRODUCTION'

        self.CHOICES = (
            (self.STATUS_AVAILABLE, 'available'),
            (self.STATUS_ALLOCATED, 'allocated'),
            (self.STATUS_PRODUCTION, 'production'),
        )

        self.CSS_CLASSES = {
            self.STATUS_AVAILABLE: 'info',
            self.STATUS_ALLOCATED: 'primary',
            self.STATUS_PRODUCTION: 'success',
            # STATUS_DECOMMISSIONING: 'warning',
            # STATUS_RETIRED: 'danger',
        }


class IPStatusChoices(object):

    def __init__(self):

        self.STATUS_FREE = 'FREE'
        self.STATUS_ALLOCATED = 'ALLOCATED'
    
        self.CHOICES = (
            (self.STATUS_FREE, 'free'),
            (self.STATUS_ALLOCATED, 'allocated'),
        )

        self.CSS_CLASSES = {
            self.STATUS_FREE: 'success',
            self.STATUS_ALLOCATED: 'primary',
        }



class ActiveStatusChoices(object):

    def __init__(self):

        self.STATUS_ACTIVE = 'ACTIVE'
        self.STATUS_ACTIVATING = 'ACTIVATING'
        self.STATUS_DISABELD = 'DISABLED'

        self.CHOICES = (
            (self.STATUS_ACTIVE, 'active'),
            (self.STATUS_ACTIVATING, 'activating'),
            (self.STATUS_DISABELD, 'disabled'),
        )

        self.CSS_CLASSES = {
            self.STATUS_ACTIVE: 'success',
            self.STATUS_ACTIVATING: 'primary',
            self.STATUS_DISABELD: 'warning',
        }




class TagDomainChoices(object):

    def __init__(self):

        self.IX_DOMAIN = 'IX-DOMAIN'
        self.DEVICE_DOMAIN = 'DEVICE-DOMAIN'
        self.PORTCHANNEL_DOMAIN = 'PORT-CHANNEL'

        self.CHOICES = (
            (self.IX_DOMAIN, 'IX'),
            (self.DEVICE_DOMAIN, 'Device'),
            (self.PORTCHANNEL_DOMAIN, 'Port Channel'),
        )

        self.CSS_CLASSES = {
            self.IX_DOMAIN: 'success',
            self.DEVICE_DOMAIN: 'primary',
            self.PORTCHANNEL_DOMAIN: 'warning',
        }
