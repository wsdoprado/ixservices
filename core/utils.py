import django_filters
import django_tables2 as tables
from django import forms
from django.urls import reverse
from django.forms import BoundField
from utilities.forms.fields import DynamicModelChoiceMixin
from utilities.forms.widgets import APISelectMultiple
# from dcim.models import Interface, FrontPort, RearPort 
from dcim import models as dcim_models

class BDynamicModelChoiceMixin(DynamicModelChoiceMixin):
    """
    :param query_params: A dictionary of additional key/value pairs to attach to the API request
    :param initial_params: A dictionary of child field references to use for selecting a parent field's initial value
    :param null_option: The string used to represent a null selection (if any)
    :param disabled_indicator: The name of the field which, if populated, will disable selection of the
        choice (optional)
    :param str fetch_trigger: The event type which will cause the select element to
        fetch data from the API. Must be 'load', 'open', or 'collapse'. (optional)
    """

    ### TODO: override method from parent clalss
    def get_bound_field(self, form, field_name):
        bound_field = BoundField(form, self, field_name)

        # Set initial value based on prescribed child fields (if not already set)
        if not self.initial and self.initial_params:
            filter_kwargs = {}
            for kwarg, child_field in self.initial_params.items():
                value = form.initial.get(child_field.lstrip('$'))
                if value:
                    filter_kwargs[kwarg] = value
            if filter_kwargs:
                self.initial = self.queryset.filter(**filter_kwargs).first()

        # Modify the QuerySet of the field before we return it. Limit choices to any data already bound: Options
        # will be populated on-demand via the APISelect widget.
        data = bound_field.value()
        if data:
            field_name = getattr(self, 'to_field_name') or 'pk'
            filter = self.filter(field_name=field_name)
            try:
                self.queryset = filter.filter(self.queryset, data)
            except (TypeError, ValueError):
                # Catch any error caused by invalid initial data passed from the user
                self.queryset = self.queryset.none()
        else:
            self.queryset = self.queryset.none()

        # Set the data URL on the APISelect widget (if not already set)
        widget = bound_field.field.widget
        if not widget.attrs.get('data-url'):
            app_label = self.queryset.model._meta.app_label
            model_name = self.queryset.model._meta.model_name
            ## edited reverse url for plugins
            # if self.queryset.model in [Site, Region, Device, Interface, RearPort, FrontPort]:
            netbox_models = self.list_netbox_models()
            if self.queryset.model.__name__ in netbox_models:
                data_url = reverse('{}-api:{}-list'.format(app_label, model_name))
            else:
                data_url = reverse('plugins:{}:api-select:{}-list'.format(app_label, model_name))
            widget.attrs['data-url'] = data_url

        return bound_field

    
    def list_netbox_models(self):
        return dcim_models.sites.__all__ + dcim_models.devices.__all__ + dcim_models.device_components.__all__
               


class DynamicModelChoiceField(BDynamicModelChoiceMixin, forms.ModelChoiceField):
    """
    Override get_bound_field() to avoid pre-populating field choices with a SQL query. The field will be
    rendered only with choices set via bound data. Choices are populated on-demand via the APISelect widget.
    """

    def clean(self, value):
        """
        When null option is enabled and "None" is sent as part of a form to be submitted, it is sent as the
        string 'null'.  This will check for that condition and gracefully handle the conversion to a NoneType.
        """
        if self.null_option is not None and value == settings.FILTERS_NULL_CHOICE_VALUE:
            return None
        return super().clean(value)


class DynamicModelMultipleChoiceField(BDynamicModelChoiceMixin, forms.ModelMultipleChoiceField):
    """
    A multiple-choice version of DynamicModelChoiceField.
    """
    filter = django_filters.ModelMultipleChoiceFilter
    widget = APISelectMultiple

    def clean(self, value):
        """
        When null option is enabled and "None" is sent as part of a form to be submitted, it is sent as the
        string 'null'.  This will check for that condition and gracefully handle the conversion to a NoneType.
        """
        if self.null_option is not None and settings.FILTERS_NULL_CHOICE_VALUE in value:
            value = [v for v in value if v != settings.FILTERS_NULL_CHOICE_VALUE]
            return [None, *value]
        return super().clean(value)



class ButtonsColumn(tables.TemplateColumn):
    """
    Render edit, delete, and changelog buttons for an object.

    :param model: Model class to use for calculating URL view names
    :param prepend_content: Additional template content to render in the column (optional)
    :param return_url_extra: String to append to the return URL (e.g. for specifying a tab) (optional)
    """
    buttons = ('changelog', 'edit', 'delete')
    attrs = {'td': {'class': 'text-end text-nowrap noprint'}}
    # Note that braces are escaped to allow for string formatting prior to template rendering
    template_code = """
    {{% if "changelog" in buttons %}}
        <a href="{{% url 'plugins:{app_label}:{model_name}_changelog' pk=record.pk %}}" class="btn btn-outline-dark btn-sm" title="Change log">
            <i class="mdi mdi-history"></i>
        </a>
    {{% endif %}}
    {{% if "edit" in buttons and perms.{app_label}.change_{model_name} %}}
        <a href="{{% url 'plugins:{app_label}:{model_name}_edit' pk=record.pk %}}?return_url={{{{ request.path }}}}{{{{ return_url_extra }}}}" class="btn btn-sm btn-warning" title="Edit">
            <i class="mdi mdi-pencil"></i>
        </a>
    {{% endif %}}
    {{% if "delete" in buttons and perms.{app_label}.delete_{model_name} %}}
        <a href="{{% url 'plugins:{app_label}:{model_name}_delete' pk=record.pk %}}?return_url={{{{ request.path }}}}{{{{ return_url_extra }}}}" class="btn btn-sm btn-danger" title="Delete">
            <i class="mdi mdi-trash-can-outline"></i>
        </a>
    {{% endif %}}
    """

    def __init__(self, model, *args, buttons=None, prepend_template=None, return_url_extra='', **kwargs):
        if prepend_template:
            prepend_template = prepend_template.replace('{', '{{')
            prepend_template = prepend_template.replace('}', '}}')
            self.template_code = prepend_template + self.template_code

        template_code = self.template_code.format(
            app_label=model._meta.app_label,
            model_name=model._meta.model_name,
            buttons=buttons
        )

        super().__init__(template_code=template_code, *args, **kwargs)

        # Exclude from export by default
        if 'exclude_from_export' not in kwargs:
            self.exclude_from_export = True

        self.extra_context.update({
            'buttons': buttons or self.buttons,
            'return_url_extra': return_url_extra,
        })

    def header(self):
        return ''



