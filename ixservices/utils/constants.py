PORT_TYPE_CONNECTOR_TYPE = {
    'SFP': ('BD', 'EX', 'LX', 'SX', 'UTP', 'ZX'),
    'SFP+': ('BD', 'ER', 'EX', 'LR', 'LX', 'SR', 'SX', 'UTP', 'ZR', 'ZX'),
    'XFP': ('ER', 'EX', 'LR', 'LX', 'SR', 'SX', 'ZR', 'ZX'),
    'CFP': ('ER4', 'LR4', 'SR4', 'SR10'),
    'QSFP+': ('ER4', 'LR4', 'SR4'),
    'QSFP28': ('10LR',),
    'CPAK': ()
}

PORT_CAPACITY_CONNECTOR_TYPE = {
    'SFP': (1000,),
    'SFP+': (1000, 10000),
    'XFP': (1000, 10000, 40000,),
    'CFP': (40000, 100000,),
    'QSFP+': (40000,),
    'QSFP28': (100000,),
    'UTP': (100, 1000,),
    'CPAK': ()
}

CAPACITIES_MAX = ((1000, '1G'), (10000, '10G'),
                  (40000, '40G'), (100000, '100G'), (400000, '400G'),)

CAPACITIES_CONF = ((100, '100M'),) + CAPACITIES_MAX

CONNECTOR_TYPES = (('SFP', 'SFP'),
                   ('SFP+', 'SFP+'),
                   ('XFP', 'XFP'),
                   ('CFP', 'CFP'),
                   ('CPAK', 'CPAK'),
                   ('QSFP28', 'QSFP28'),
                   ('UTP', 'UTP'),)

PORT_TYPES = (('SX', 'SX'),
              ('LX', 'LX'),
              ('ZX', 'ZX'),
              ('SR', 'SR'),
              ('LR', 'LR'),
              ('ER', 'ER'),
              ('ZR', 'ZR'),
              ('ER4', 'ER4'),
              ('LR4', 'LR4'),
              ('10LR', '10LR'),
              ('SR4', 'SR4'),
              ('ERlite', 'ERlite'),
              ('UTP', 'UTP'),
              ('BD', 'BD'),)

PHYSICAL_INTERFACE_PORT_CONNECTOR_TYPE = {
    'SFP': ('SFP', ),
    'SFP+': ('SFP', 'SFP+'),
    'XFP': ('XFP'),
    'CFP': ('CFP', ),
    'QSFP+': ('QSFP+', ),
    'QSFP28': ('QSFP28', ),
    'UTP': ('UTP', 'SFP'),
    'CPAK': ('CPAK', ),
}

SWITCH_MODEL_CHANNEL_PREFIX = {
    'BROCADE': 'PC',
    'CISCO': 'BE',
    'EXTREME': '',
    'JUNIPER': 'ae',
    'HUAWEI': 'Trunk',
}

MAX_TAG_NUMBER = 4095
MIN_TAG_NUMBER = 0

VENDORS = (('EXTREME', 'EXTREME'),
           ('BROCADE', 'BROCADE'),
           ('CISCO', 'CISCO'),
           ('JUNIPER', 'JUNIPER'),
           ('HUAWEI', 'HUAWEI'),)
