
ENDPOINT_BUTTONS = """
{% if perms.ipam.add_ipaddress %}
    <a href="{% url 'ipam:ipaddress_add' %}?interface={{ record.pk }}&return_url={% url 'dcim:device_interfaces' pk=object.pk %}" class="btn btn-sm btn-success" title="Add IP address">
        <i class="mdi mdi-plus-thick" aria-hidden="true"></i>
    </a>
{% endif %}
{% if record.cable %}
    <a href="{% url 'dcim:interface_trace' pk=record.pk %}" class="btn btn-primary btn-sm" title="Trace"><i class="mdi mdi-transit-connection-variant"></i></a>
    {% include 'dcim/inc/cable_toggle_buttons.html' with cable=record.cable %}
    {% if perms.dcim.delete_cable %}
        <a href="{% url 'dcim:cable_delete' pk=record.cable.pk %}?return_url={% url 'dcim:device_interfaces' pk=object.pk %}" title="Remove cable" class="btn btn-danger btn-sm">
            <i class="mdi mdi-ethernet-cable-off" aria-hidden="true"></i>
        </a>
    {% endif %}
{% elif record.is_connectable and perms.dcim.add_cable %}
    <a href="#" class="btn btn-outline-dark btn-sm disabled"><i class="mdi mdi-transit-connection-variant" aria-hidden="true"></i></a>
    <a href="#" class="btn btn-outline-dark btn-sm disabled"><i class="mdi mdi-lan-connect" aria-hidden="true"></i></a>
    {% if not record.mark_connected %}
    <span class="dropdown">
        <button type="button" class="btn btn-success btn-sm dropdown-toggle" data-bs-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
            <span class="mdi mdi-ethernet-cable" aria-hidden="true"></span>
        </button>
        <ul class="dropdown-menu dropdown-menu-end">
            <li><a class="dropdown-item" href="{% url 'dcim:interface_connect' termination_a_id=record.pk termination_b_type='interface' %}?return_url={% url 'dcim:device_interfaces' pk=object.pk %}">Interface</a></li>
            <li><a class="dropdown-item" href="{% url 'dcim:interface_connect' termination_a_id=record.pk termination_b_type='front-port' %}?return_url={% url 'dcim:device_interfaces' pk=object.pk %}">Front Port</a></li>
            <li><a class="dropdown-item" href="{% url 'dcim:interface_connect' termination_a_id=record.pk termination_b_type='rear-port' %}?return_url={% url 'dcim:device_interfaces' pk=object.pk %}">Rear Port</a></li>
            <li><a class="dropdown-item" href="{% url 'dcim:interface_connect' termination_a_id=record.pk termination_b_type='circuit-termination' %}?return_url={% url 'dcim:device_interfaces' pk=object.pk %}">Circuit Termination</a></li>
        </ul>
    </span>
    {% else %}
        <a href="#" class="btn btn-outline-dark btn-sm disabled"><i class="mdi mdi-ethernet-cable" aria-hidden="true"></i></a>
    {% endif %}
{% endif %}
"""

CONNECTION_BUTTONS =  """
{% if perms.ixservices.add_customerservice %}
    <a href="{% url 'plugins:ixservices:customerservice_add' %}?connection={{ record.pk }}&return_url={% url 'plugins:ixservices:customerconnection_list' %}" class="btn btn-sm btn-success" title="Add CustomerService">
        <i class="mdi mdi-plus-thick" aria-hidden="true"></i>
    </a>
{% endif %}
{% if perms.ixservices.add_customerconnectionendpoint %}
    {% if not record.connected_device or record.is_lag %}
    <span class="dropdown">
        <button type="button" class="btn btn-success btn-sm dropdown-toggle" data-bs-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
            <span class="mdi mdi-ethernet-cable" aria-hidden="true"></span>
        </button>
        <ul class="dropdown-menu dropdown-menu-end">
            <li><a class="dropdown-item" href="{% url 'plugins:ixservices:customerconnection_connect' customer_connection_id=record.pk termination_type='interface' %}?return_url={% url 'plugins:ixservices:customerconnection_customerconnectionendpoint' pk=record.pk %}">Interface</a></li>
            <li><a class="dropdown-item" href="{% url 'plugins:ixservices:customerconnection_connect' customer_connection_id=record.pk termination_type='frontport' %}?return_url={% url 'plugins:ixservices:customerconnection_customerconnectionendpoint' pk=record.pk %}">Front Port</a></li>
            <li><a class="dropdown-item" href="{% url 'plugins:ixservices:customerconnection_connect' customer_connection_id=record.pk termination_type='rearport' %}?return_url={% url 'plugins:ixservices:customerconnection_customerconnectionendpoint' pk=record.pk %}">Rear Port</a></li>
        </ul>
    </span>
    {% else %}
        <a href="#" class="btn btn-outline-dark btn-sm disabled"><i class="mdi mdi-ethernet-cable" aria-hidden="true"></i></a>
    {% endif %}
{% endif %}
"""

CONNECTIONENDPOINT_BUTTONS = """
{% if record.interface and record.interface.mark_connected and record.connected_device %}
    <a href="{% url 'dcim:interface_trace' pk=record.interface.pk %}" class="btn btn-primary btn-sm" title="Trace"><i class="mdi mdi-transit-connection-variant"></i></a>
{% endif %}
{% if record.rearport and record.rearport.mark_connected and record.connected_device %}
    <a href="{% url 'dcim:rearport_trace' pk=record.rearport.pk %}" class="btn btn-primary btn-sm" title="Trace"><i class="mdi mdi-transit-connection-variant"></i></a>
{% endif %}
{% if record.frontport and record.frontport.mark_connected and record.connected_device %}
    <a href="{% url 'dcim:frontport_trace' pk=record.frontport.pk %}" class="btn btn-primary btn-sm" title="Trace"><i class="mdi mdi-transit-connection-variant"></i></a>
{% endif %}
"""