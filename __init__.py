from extras.plugins import PluginConfig

class ServicesConfig(PluginConfig):
    name = 'ixservices'
    verbose_name = 'Plugin Services'
    description = 'Modelo de servicos do IX.br'
    version = '0.1'
    author = 'Helio'
    author_email = 'helio@nic.br'
    base_url = 'ixservices'
    required_settings = []
    default_settings = {
        'ativo': True
    }

config = ServicesConfig