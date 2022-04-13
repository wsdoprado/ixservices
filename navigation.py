# navigation.py
from extras.plugins import PluginMenuButton, PluginMenuItem
from utilities.choices import ButtonColorChoices


menu_items = (
    PluginMenuItem(
        link="plugins:ixservices:home",
        link_text="Home",
        buttons=(),
    ),
    PluginMenuItem(
        link="plugins:ixservices:as_list",
        link_text="ASs",
        buttons=(
            PluginMenuButton(
                link="plugins:ixservices:as_add",
                title="Add",
                icon_class="fa fa-plus",
                color=ButtonColorChoices.GREEN,
            ),
        ),
    ),
    PluginMenuItem(
        link="plugins:ixservices:ix_list",
        link_text="IXs",
        buttons=(
            PluginMenuButton(
                link="plugins:ixservices:ix_add",
                title="Add",
                icon_class="fa fa-plus",
                color=ButtonColorChoices.GREEN,
            ),
        ),
    ),
    PluginMenuItem(
        link="plugins:ixservices:customerservice_list",
        link_text="CustomerServices",
        buttons=(
            PluginMenuButton(
                link="plugins:ixservices:customerservice_add",
                title="Add",
                icon_class="fa fa-plus",
                color=ButtonColorChoices.GREEN,
            ),
        ),
    ),
    PluginMenuItem(
        link="plugins:ixservices:customerconnection_list",
        link_text="CustomerConnections",
        buttons=(
            PluginMenuButton(
                link="plugins:ixservices:customerconnection_add",
                title="Add",
                icon_class="fa fa-plus",
                color=ButtonColorChoices.GREEN,
            ),
        ),
    ),
)