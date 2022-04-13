import re
from subprocess import PIPE, CalledProcessError, run

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from .validators import INVALID_ASN, validate_as_number

INEXISTENT_ASN = _('ASN Does not exist.')


def get_whois(asn):
    try:
        validate_as_number(asn)
        data = run(['whois', "AS" + str(asn)], stdout=PIPE)
        data.check_returncode()
        return data.stdout
    except (TypeError, ValidationError) as e:
        raise ValidationError(INVALID_ASN)
    except CalledProcessError as e:
        txt = data.stdout
        # verif b'Unknown AS number or IP network'
        if txt.startswith(b'Unknown AS number'):
            raise ValidationError(INEXISTENT_ASN)


def decode_line(line):
    try:
        return line.decode("utf-8")
    except:
        return line.decode("latin1")


def parse_whois(whois_content):
    if whois_content is None:
        raise ValidationError(INEXISTENT_ASN)

    final_list = list()
    line_break = False

    for line in whois_content.split(b'\n'):
        decoded_line = decode_line(line)

        # If it's a blank line or a comment
        if final_list and re.match(r'^\s*(?:%.*)?$', decoded_line):
            line_break = True

        # Tuple (field, value) with format field: value % possible comment
        match_content = re.match(r'^\s*\b([\w\d-]*):\s*((?:(?! %.*$).)*)',
                                 decoded_line)
        if match_content:
            if line_break:
                final_list.append(('', ''))
                line_break = False
            final_list.append(match_content.groups())

    if not final_list:
        raise ValidationError(INEXISTENT_ASN)

    return final_list


def get_parsed_whois(asn):
    return parse_whois(get_whois(asn))
