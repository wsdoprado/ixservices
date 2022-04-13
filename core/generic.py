from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from django.urls import reverse

from netbox.views import generic
from utilities.tables import paginate_table
from utilities.permissions import get_permission_for_model


from utilities.views import GetReturnURLMixin, ObjectPermissionRequiredMixin
from django.views.generic import View

from extras.plugins import PluginMenuButton
from utilities.choices import ButtonColorChoices


def get_buttom_reverse_url(model, func, title, perm, collor_choices=None, kwargs={}):
    '''
    kwargs={'pk': instance.pk}
    param_string=f'{url}?{param_string}'
    PluginMenuButton(
                link=url,
                title=title,
                icon_class="fa fa-plus",
                color=ButtonColorChoices.GREEN,
                permissions=[perm]
            )
    '''
    url = reverse("plugins:ixservices:{}_{}".format(model, func), kwargs=kwargs),
    url = "plugins:ixservices:{}_{}".format(model, func)
    # return PluginMenuButton(link=url, title=title, permissions=perm, icon_class="fa fa-plus",color=collor_choices)
    return { 'link': url, 'title': title, 'permissions': perm, 'kwargs': kwargs }


def get_changelog_reverse_url(model, kwargs={}):
    '''
       url: plugins/ixservices/<model>/<:pk>/changelog
    '''
    url = reverse("plugins:ixservices:{}_changelog".format(model), kwargs=kwargs),
    url = "plugins:ixservices:{}_changelog".format(model)
    return url


# fix problesm for plugin visualization and inheritance
class BaseObjectView(ObjectPermissionRequiredMixin, View):

    queryset = None
    template_name = None
    
    def get_required_permission(self):
        return get_permission_for_model(self.queryset.model, 'view')

# class ObjectListView(generic.ObjectListView):
class ObjectListView(BaseObjectView):
    """
    List a series of objects.

    queryset: The queryset of objects to display. Note: Prefetching related objects is not necessary, as the
      table will prefetch objects as needed depending on the columns being displayed.
    filter: A django-filter FilterSet that is applied to the queryset
    filter_form: The form used to render filter options
    table: The django-tables2 Table used to render the objects list
    template_name: The name of the template
    """
    filterset = None
    filterset_form = None
    table = None
    template_name = 'ixservices/generic/object_list.html'
    action_buttons = ('add', 'import', 'export')

    '''

    # Handle QuerySet restriction of parent object if needed
        if hasattr(model.objects, 'restrict'):
            obj = get_object_or_404(model.objects.restrict(request.user, 'view'), **kwargs)
        else:
            obj = get_object_or_404(model, **kwargs)'''

        
    # TODO  Reimplemented from NEtbox
    def get(self, request):

        # super().get(request)
  
        model = self.queryset.model
        content_type = ContentType.objects.get_for_model(model)

        if self.filterset:
            self.queryset = self.filterset(request.GET, self.queryset).qs

        permissions = {}
        for action in ('add', 'change', 'delete', 'view'):
            perm_name = get_permission_for_model(model, action)
            permissions[action] = request.user.has_perm(perm_name)


        # Construct the objects table
        table = self.table(self.queryset, user=request.user)
        if 'pk' in table.base_columns and (permissions['change'] or permissions['delete']):
            table.columns.show('pk')

        # Paginate the objects table
        paginate_table(table, request)

        model_name = model._meta.verbose_name.title().lower()
        
        # action buttons reversing model endpoints
        buttons=(
            get_buttom_reverse_url(model_name, 'add', 'Add', ['add']),
            # get_buttom_reverse_url(model_name, 'import', 'Import', ['import']),
            # get_buttom_reverse_url(model_name, 'bulk_edit', 'Edit Selected', ['edit']),
            # get_buttom_reverse_url(model_name, 'bulk_delete', 'Delete Selected', ['delete'])
        )

        context = {
            'content_type': content_type,
            'table': table,
            'permissions': permissions,
            'action_buttons': self.action_buttons,
            'filter_form': self.filterset_form(request.GET, label_suffix='') if self.filterset_form else None,
            'buttons': buttons
        }        

        return render(request, self.template_name, context)


# class ObjectEditView(generic.ObjectEditView):
class ObjectEditView(generic.ObjectEditView):
     """
    Create or edit a single object.

    queryset: The base queryset for the object being modified
    model_form: The form used to create or edit the object
    template_name: The name of the template
    """

class ObjectDeleteView(generic.ObjectDeleteView):
     """
    Delete a single object.

    queryset: The base queryset for the object being deleted
    template_name: The name of the template
    """


# class ObjectView(ObjectPermissionRequiredMixin, View):
class ObjectView(BaseObjectView):
    """
    Retrieve a single object for display.

    queryset: The base queryset for retrieving the object
    template_name: Name of the template to use
    """
    def get_template_name(self):
        """
        Return self.template_name if set. Otherwise, resolve the template path by model app_label and name.
        """
        if self.template_name is not None:
            return self.template_name
        model_opts = self.queryset.model._meta
        return f'{model_opts.app_label}/{model_opts.model_name}.html'

    def get_extra_context(self, request, instance):
        """
        Return any additional context data for the template.

        request: The current request
        instance: The object being viewed
        """

        model_name = self.queryset.model._meta.verbose_name.title().lower()
        # action buttons reversing model endpoints
        def get_action_btn(action, label, has_args=True):
            kwargs = {'pk': instance.pk} if has_args else {}            
            return get_buttom_reverse_url(model_name, action, label, [action], kwargs=kwargs)

        buttons=(get_action_btn('edit', 'Edit'), get_action_btn('delete', 'Delete'))       

        # get changelog reverse url
        def get_changelog_url():
            kwargs={'pk': instance.pk}
            return get_changelog_reverse_url(model_name, kwargs=kwargs)

        return { 'buttons': buttons, 'changelog_url': get_changelog_url() }
        
    def get(self, request, *args, **kwargs):
        """
        Generic GET handler for accessing an object by PK or slug
        """
        instance = get_object_or_404(self.queryset, **kwargs)

        return render(request, self.get_template_name(), {
            'object': instance,
            **self.get_extra_context(request, instance),
        })

    