import ipaddress
import re
import sys

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, URLValidator
from django.utils.translation import gettext as _

from ixservices.ixservices.utils.regex import Regex

regex = Regex()

# ------- Messages -------
INVALID_ASN = _('Enter a valid AS number.')
INVALID_CNPJ = _('Enter a valid CNPJ number.')
INVALID_IPV4_NETWORK = _('Enter a valid IPv4 network.')
INVALID_IPV6_NETWORK = _('Enter a valid IPv6 network.')
INVALID_IPV46_NETWORK = _('Enter a valid IPv4 or IPv6 network.')
INVALID_SWITCH_MODEL = _(
    'SwitchModel.model format not compatible with SwitchModel.vendor.')
ONLY_LOWERCASE = _('Allowed only ASCII lowercase characters.')
USUAL_IX_CODE = _('Allowed only two-four alphabetic lowercase characters')
USUAL_IX_FULLNAME = _(
    'Allowed only Name of city followed by the state '
    'abbreviation separated by -')
USUAL_IX_SHORTNAME = (
    'Allowed only two groups of 3-13 and 2-2 alphabetic lowercase characters '
    'separated by dot')
USUAL_MAC_ADDRESS = _(
    'Allowed only one of these: '
    '1) Six groups of two hexadecimal digits. '
    '2) Three groups of four hexadecimal digits. '
    '3) Twelve hexadecimal digits. '
    '(1) left zeros could be omitted. '
    '(1) and (2) could be separated by colons, dots or hyphens.')
USUAL_PIX_CODE = _('Allowed only three-max_field_length characters '
                   'with first uppercase')
INVALID_DOWNLINK_NAME = _(
    'DownlinkChannel name doesn\'t match with switch model.')
INVALID_UPLINK_NAME = _(
    'UplinkChannel name doesn\'t match with switch model.')
INVALID_CORE_NAME = _(
    'CoreChannel name doesn\'t match with switch model.')
INVALID_CUSTOMER_NAME = _(
    'CustomerChannel name doesn\'t match with switch model.')
UNRECOGNIZED_CHANNEL_TYPE_VENDOR = _('Unrecognized channel_type/vendor values')
INVALID_CHANNEL_TYPE_OR_VENDOR = _('Invalid value of channel_type or vendor')
RESERVED_IP = _('The IP {} is reserved')
# ------- Regex -------
CNPJ = re.compile(r'^{0}$'.format(regex.cnpj))
IX_CODE = re.compile(r'^{0}$'.format(regex.ix_code))
IX_FULLNAME = re.compile(regex.ix_fullname)
IX_SHORTNAME = re.compile(regex.ix_shortname)
LOWERCASE = re.compile(r'^[a-z]+$')
PIX_CODE = re.compile(regex.pix_code)
EXTREME_MODELS = re.compile(r'^{0}$'.format(regex.extreme))
CISCO_MODELS = re.compile(r'^{0}$'.format(regex.cisco))
BROCADE_MODELS = re.compile(r'^{0}$'.format(regex.brocade))
JUNIPER_MODELS = re.compile(r'^{0}$'.format(regex.juniper))
HUAWEI_MODELS = re.compile(r'^{0}$'.format(regex.huawei))
DOWNLINK_BROCADE = re.compile(r'^dl-{0}$'.format(regex.channel_name_brocade))
DOWNLINK_CISCO = re.compile(r'^dl-{0}$'.format(regex.channel_name_cisco))
DOWNLINK_EXTREME = re.compile(r'^dl-{0}$'.format(regex.channel_name_extreme))
DOWNLINK_JUNIPER = re.compile(r'^dl-{0}$'.format(regex.channel_name_juniper))
DOWNLINK_HUAWEI = re.compile(r'^dl-{0}$'.format(regex.channel_name_huawei))
MAC_ADDRESS = re.compile(
    '{}{}{}'.format(r'^(', '|'.join(regex._MAC_PATTERN_JOIN), r')$'))
UPLINK_BROCADE = re.compile(r'^ul-{0}$'.format(regex.channel_name_brocade))
UPLINK_CISCO = re.compile(r'^ul-{0}$'.format(regex.channel_name_cisco))
UPLINK_EXTREME = re.compile(r'^ul-{0}$'.format(regex.channel_name_extreme))
UPLINK_JUNIPER = re.compile(r'^ul-{0}$'.format(regex.channel_name_juniper))
UPLINK_HUAWEI = re.compile(r'^ul-{0}$'.format(regex.channel_name_huawei))
CORE_BROCADE = re.compile(r'^cc-{0}$'.format(regex.channel_name_brocade))
CORE_CISCO = re.compile(r'^cc-{0}$'.format(regex.channel_name_cisco))
CORE_EXTREME = re.compile(r'^cc-{0}$'.format(regex.channel_name_extreme))
CORE_JUNIPER = re.compile(r'^cc-{0}$'.format(regex.channel_name_juniper))
CORE_HUAWEI = re.compile(r'^cc-{0}$'.format(regex.channel_name_huawei))
CUSTOMER_BROCADE = re.compile(r'^ct-{0}$'.format(regex.channel_name_brocade))
CUSTOMER_CISCO = re.compile(r'^ct-{0}$'.format(regex.channel_name_cisco))
CUSTOMER_EXTREME = re.compile(r'^ct-{0}$'.format(regex.channel_name_extreme))
CUSTOMER_JUNIPER = re.compile(r'^ct-{0}$'.format(regex.channel_name_juniper))
CUSTOMER_HUAWEI = re.compile(r'^ct-{0}$'.format(regex.channel_name_huawei))

# ------- Validation Dicts -------
CHANNEL_DICT = {
    'CustomerChannel': {
        'BROCADE': RegexValidator(CUSTOMER_BROCADE, INVALID_CUSTOMER_NAME),
        'CISCO': RegexValidator(CUSTOMER_CISCO, INVALID_CUSTOMER_NAME),
        'EXTREME': RegexValidator(CUSTOMER_EXTREME, INVALID_CUSTOMER_NAME),
        'JUNIPER': RegexValidator(CUSTOMER_JUNIPER, INVALID_CUSTOMER_NAME),
        'HUAWEI': RegexValidator(CUSTOMER_HUAWEI, INVALID_CUSTOMER_NAME)
    },
    'CoreChannel': {
        'BROCADE': RegexValidator(CORE_BROCADE, INVALID_CORE_NAME),
        'CISCO': RegexValidator(CORE_CISCO, INVALID_CORE_NAME),
        'EXTREME': RegexValidator(CORE_EXTREME, INVALID_CORE_NAME),
        'JUNIPER': RegexValidator(CORE_JUNIPER, INVALID_CORE_NAME),
        'HUAWEI': RegexValidator(CORE_HUAWEI, INVALID_CORE_NAME)
    },
    'DownlinkChannel': {
        'BROCADE': RegexValidator(DOWNLINK_BROCADE, INVALID_DOWNLINK_NAME),
        'CISCO': RegexValidator(DOWNLINK_CISCO, INVALID_DOWNLINK_NAME),
        'EXTREME': RegexValidator(DOWNLINK_EXTREME, INVALID_DOWNLINK_NAME),
        'JUNIPER': RegexValidator(DOWNLINK_JUNIPER, INVALID_DOWNLINK_NAME),
        'HUAWEI': RegexValidator(DOWNLINK_HUAWEI, INVALID_DOWNLINK_NAME)
    },
    'UplinkChannel': {
        'BROCADE': RegexValidator(UPLINK_BROCADE, INVALID_UPLINK_NAME),
        'CISCO': RegexValidator(UPLINK_CISCO, INVALID_UPLINK_NAME),
        'EXTREME': RegexValidator(UPLINK_EXTREME, INVALID_UPLINK_NAME),
        'JUNIPER': RegexValidator(UPLINK_JUNIPER, INVALID_UPLINK_NAME),
        'HUAWEI': RegexValidator(UPLINK_HUAWEI, INVALID_UPLINK_NAME)
    },
    'TranslationChannel': {
        'BROCADE': NotImplemented,
        'CISCO': NotImplemented,
        'EXTREME': NotImplemented,
        'JUNIPER': NotImplemented,
        'HUAWEI': NotImplemented
    }
}


# ------- Validation Functions -------
def validate_as_number(number):
    """ASN validator."""

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


def validate_cnpj(value):
    validator = RegexValidator(
        regex=CNPJ,
        message=INVALID_CNPJ,
        code='invalid')

    validator(value)


def validate_ipv4_network(value):
    try:
        ipaddress.IPv4Network(value, False)
    except (ipaddress.AddressValueError,
            ipaddress.NetmaskValueError,
            ValueError):
        raise ValidationError(INVALID_IPV4_NETWORK, code='invalid')


def validate_ipv46_network(value):
    try:
        ipaddress.ip_network(value, False)
    except (ipaddress.AddressValueError,
            ipaddress.NetmaskValueError,
            ValueError):
        raise ValidationError(INVALID_IPV46_NETWORK, code='invalid')


def validate_ipv6_network(value):
    try:
        ipaddress.IPv6Network(value, False)
    except (ipaddress.AddressValueError,
            ipaddress.NetmaskValueError,
            ValueError):
        raise ValidationError(INVALID_IPV6_NETWORK, code='invalid')


def validate_ix_code(value):
    validator = RegexValidator(IX_CODE, USUAL_IX_CODE)
    validator(value)


def validate_ix_fullname(value):
    validator = RegexValidator(IX_FULLNAME, USUAL_IX_FULLNAME)
    validator(value)


def validate_ix_shortname(value):
    validator = RegexValidator(IX_SHORTNAME, USUAL_IX_SHORTNAME)
    validator(value)


def validate_mac_address(value):
    """Usual lowercase MAC address validator."""
    validator = RegexValidator(MAC_ADDRESS, USUAL_MAC_ADDRESS)
    validator(value)


def validate_name_format(value):
    if value.count('{') > 1 or value.count('}') > 1:
        raise ValidationError(
            ('there is more than one { or } on name_format'))
    if value.count('{0}') == 0:
        raise ValidationError(_('name_format must contain \{0\}'))
    if value.format(12) != value.replace('{0}', '12'):
        raise ValidationError(_('name_format must contain \{0\}'))


def validate_only_lowercase(value):
    """Only lowercase validator."""
    validator = RegexValidator(LOWERCASE, ONLY_LOWERCASE)
    validator(value)


def validate_pix_code(value):
    valitador = RegexValidator(PIX_CODE, USUAL_PIX_CODE)
    valitador(value)


def validate_url_format(value):
    validator = URLValidator()
    validator(value)


def validate_switch_model(switch):
    if switch.vendor == 'EXTREME':
        validator = RegexValidator(EXTREME_MODELS, INVALID_SWITCH_MODEL)
        validator(switch.model)
    elif switch.vendor == 'CISCO':
        validator = RegexValidator(CISCO_MODELS, INVALID_SWITCH_MODEL)
        validator(switch.model)
    elif switch.vendor == 'JUNIPER':
        validator = RegexValidator(JUNIPER_MODELS, INVALID_SWITCH_MODEL)
        validator(switch.model)
    elif switch.vendor == 'BROCADE':
        validator = RegexValidator(BROCADE_MODELS, INVALID_SWITCH_MODEL)
        validator(switch.model)
    elif switch.vendor == 'HUAWEI':
        validator = RegexValidator(HUAWEI_MODELS, INVALID_SWITCH_MODEL)
        validator(switch.model)
    else:
        raise ValidationError(_('unrecognized switch model'))


def validate_channel_name(channel):
    channel_type = channel.__class__.__name__
    vendor = channel.channel_port.port_set.first().switch.model.vendor
    if (vendor and channel_type and
            channel_type in CHANNEL_DICT and
            vendor in CHANNEL_DICT[channel_type]):
        validator = CHANNEL_DICT[channel_type][vendor]
        if validator:
            validator(channel.name)
        else:
            raise ValidationError(UNRECOGNIZED_CHANNEL_TYPE_VENDOR)
    else:
        raise ValidationError(INVALID_CHANNEL_TYPE_OR_VENDOR)



def trace_print_exception():
    exception_type, exception_object, exception_traceback = sys.exc_info()
    filename = exception_traceback.tb_frame.f_code.co_filename
    line_number = exception_traceback.tb_lineno
    print("Exception type: "+ str(exception_type))
    print("File name:  "+ str(filename))
    print("Line number: "+ str(line_number))
    return "Exception type: "+ str(exception_type), "File name:  "+ str(filename), "Line number: "+ str(line_number)
