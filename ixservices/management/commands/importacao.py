from django.core.management.base import BaseCommand, CommandError
from services.models import IX, ASN, Tag, IPv4Address, IPv6Address, MACAddress, Service, ServiceType, CustomerService, CustomerConnection, CustomerConnectionEndpoint
import requests
import sys
import json
import random
import string

class Command(BaseCommand):
    help = 'Importacao dos dados do Hercules'
    
    '''
    def add_arguments(self, parser):
        parser.add_argument('poll_ids', nargs='+', type=int)
    '''

    def request_netbox_api(self, ip):
        '''
           Acesso a API de testes do Netbox, exemplo:
           curl -X GET "http://10.0.129.43:8000/api/ipam/ip-addresses/?address=192.168.9.141" -H  
           "accept: application/json" -H  "Authorization: Token 0123456789abcdef0123456789abcdef01234567"
        '''
        
        api_endpoint = "http://10.0.129.43:8000/api/"
        api_token = "fc9bdf7f0af85a679d84b5f267d694591fd81613"

        headers = {
            'Content-Type':'application/json',
            'Authorization': 'Token {}'.format(api_token)
        }

        params = { 'address': ip }

        # busca device pelo IP
        apiurl = "{}ipam/ip-addresses/".format(api_endpoint)
        response = requests.get(apiurl, params=params, headers=headers)
        rJSON = response.json()
        return rJSON

    def handle(self, *args, **options):

        self.stdout.write(self.style.SUCCESS('Executando script de importacao'))
        errors = []

        # acesso a API de testes do Hercules
        # api = "http://http://meulocal.ix.br:8000/api/v1/"
        api = "http://hercules-homolog.in.ix.br:8000/api/v1/"


        

        
        
        # IX: importa dados das localidades
        response = requests.get(api + 'import-data')
        rJSON = response.json()
        for data in rJSON:
            print(data)
            try:
                data['create_tags'] = False
                data['create_ips'] = False
                IX.objects.get_or_create(**data)
            except Exception as e:
                # print('Error: ' + str(e))
                errors.append('IX: ' + str(e))

        # ASN: importa dados dos ASN
        response = requests.get(api + 'import-data/get_asn')
        rJSON = response.json()
        for data in rJSON:
            print(data)
            del data['description']
            del data['last_ticket']
            try:
                ASN.objects.get_or_create(**data)
            except Exception as e:
                # print('Error: ' + str(e))
                errors.append('ASN: ' + str(e))


        # IPV4: importa dados dos IPs
        
        response = requests.get(api + 'import-data/get_ipv4')
        rJSON = response.json()
        for data in rJSON:
            print(data)
            del data['in_lg']
            del data['description']
            del data['last_ticket']
            # del data['ix']
            try:
                data['ix'] = IX.objects.get(pk=data['ix'])         
                ip = IPv4Address.objects.get_or_create(**data)
                # ip.ix = ix
                # ip.save()
            except Exception as e:
                # print('Error: ' + str(e))
                errors.append('IPV4: ' + str(e))

        # IPV6: importa dados dos IPs
        response = requests.get(api + 'import-data/get_ipv6')
        rJSON = response.json()
        for data in rJSON:
            print(data)
            del data['in_lg']
            del data['description']
            del data['last_ticket']
            # del data['ix']
            try:
                data['ix'] = IX.objects.get(pk=data['ix'])         
                ip = IPv6Address.objects.get_or_create(**data)
                # ip.ix = ix
                # ip.save()
            except Exception as e:
                # print('Error: ' + str(e))
                errors.append('IPV6: ' + str(e))
        


        # MACAddress: importa dados dos Macaddress
        response = requests.get(api + 'import-data/get_mac')
        rJSON = response.json()
        for data in rJSON:
            print(data)
            del data['description']
            del data['last_ticket']
            # del data['ix']
            try:
                MACAddress.objects.get_or_create(**data)
            except Exception as e:
                # print('Error: ' + str(e))
                errors.append('MACAddress: ' + str(e))
        
        

        # Service Types: (ATMv4, ATMv6, VLAN)
        try:
            service_types = [
                ServiceType(name="ATMv4", num_clients=1),
                ServiceType(name="ATMv6", num_clients=1),
                ServiceType(name="Bilateral", num_clients=1) 
            ]
            ServiceType.objects.bulk_create(service_types)
        except Exception as e:
            # print('Error: ' + str(e))
            errors.append('Service Types: ' + str(e))

        # Services
        try:
            ixs = IX.objects.all()
            services = []
            atmv4 = ServiceType.objects.get(name="ATMv4")
            atmv6 = ServiceType.objects.get(name="ATMv6")
            bilateral = ServiceType.objects.get(name="Bilateral")
            # label = TODO: verificar o campo label ??
            for ix in ixs:
                services.append(Service(name="{0}-{1}".format(atmv4.name, ix.code),label='',service_type=atmv4,ix=ix))
                services.append(Service(name="{0}-{1}".format(atmv6.name, ix.code),label='',service_type=atmv6,ix=ix))
                services.append(Service(name="{0}-{1}".format(bilateral.name, ix.code),label='',service_type=bilateral,ix=ix))

            Service.objects.bulk_create(services)
        except Exception as e:
            # print('Error: ' + str(e))
            errors.append('Services: ' + str(e))

        

        # TAGs TODO: api nao esta retornando o status da TAG
        response = requests.get(api + 'import-data/get_tags')
        rJSON = response.json()
        for data in rJSON:
            print(data)
            # del data['ix']
            try:
                data['ix'] = IX.objects.get(pk=data['ix'])    
                Tag.objects.get_or_create(**data)
            except Exception as e:
                # print('Error: ' + str(e))
                errors.append('Tag: ' + str(e))
                       
        

        # MLPAv4: importa dados dos Servicos ATMv4               
        response = requests.get(api + 'import-data/get_mlpav4')
        rJSON = response.json()
        atmv4 = ServiceType.objects.get(name="ATMv4")
        for data in rJSON:
            print(data)
            del data['description']
            # del data['ix']
            try:
                ix = IX.objects.get(pk=data['tag']['ix'])
                asn = ASN.objects.get(pk=data['asn'])
                asn_owner =  ASN.objects.get(pk=data["customer_channel"]["asn"])
                service = Service.objects.filter(service_type=atmv4, ix=ix).first()
                v4_address = IPv4Address.objects.get(address=data["mlpav4_address"])
                macs = MACAddress.objects.filter(address__in=data['mac_addresses'])
                name = "{0}-{1}-{2}".format(asn_owner.number, ix.code, data["customer_channel"]["name"])              
                # checa se ja exista ou create connection
                connection = CustomerConnection.objects.filter(asn=asn_owner, name=name).first()
                if not connection:                
                    connection = CustomerConnection.objects.create(
                        name=name,
                        is_lag=data["customer_channel"]["is_lag"],
                        asn=asn_owner,
                        ticket=data["last_ticket"],
                        # configured_capacity= TODO: obter dado da porta pelo channelport na APi do Hercules
                    )

                ports = data["ports"]
                for port in ports:
                    connection_ept = CustomerConnectionEndpoint.objects.filter(
                        customer_connection=connection, port_name=port["name"], switch_ip=port["switch"]).first()
                    if not connection_ept:
                        CustomerConnectionEndpoint.objects.create(
                            customer_connection=connection,
                            port_name=port["name"],
                            switch_ip=port["switch"]
                        )

                # vincular TAG
                tag = Tag.objects.filter(tag=data["tag"]["tag"],ix=ix).first()
                
                c_service = CustomerService.objects.create(
                    asn=asn,
                    service=service,
                    mlpav4_address=v4_address,
                    tag_or_outer=tag,
                    # mac_address=macs,
                    connection=connection
                )
                c_service.mac_address.add(*macs)   
            
            except Exception as e:
                # print('Error: ' + str(e))
                print(data)
                errors.append('MLPAv4 Service: {0} -- {1}'.format(str(e), name))

        
                

        # MLPAv6: importa dados dos Servicos ATMv6               
        response = requests.get(api + 'import-data/get_mlpav6')
        rJSON = response.json()
        atmv6 = ServiceType.objects.get(name="ATMv6")
        for data in rJSON:
            print(data)
            del data['description']
            # del data['ix']
            try:
                ix = IX.objects.get(pk=data['tag']['ix'])
                asn = ASN.objects.get(pk=data['asn'])
                asn_owner =  ASN.objects.get(pk=data["customer_channel"]["asn"])
                service = Service.objects.filter(service_type=atmv6, ix=ix).first()
                v6_address = IPv6Address.objects.get(address=data["mlpav6_address"])
                macs = MACAddress.objects.filter(address__in=data['mac_addresses'])
                name = "{0}-{1}-{2}".format(asn_owner.number, ix.code, data["customer_channel"]["name"])               
                # checa se ja exista ou create connection
                connection = CustomerConnection.objects.filter(asn=asn_owner, name=name).first()
                if not connection:                
                    connection = CustomerConnection.objects.create(
                        name=name,
                        is_lag=data["customer_channel"]["is_lag"],
                        asn=asn_owner,
                        ticket=data["last_ticket"],
                        # configured_capacity= TODO: obter dado da porta pelo channelport na APi do Hercules (pode ser mais de 1 porta na interface)
                    )

                ports = data["ports"]
                for port in ports:
                    connection_ept = CustomerConnectionEndpoint.objects.filter(
                        customer_connection=connection, port_name=port["name"], switch_ip=port["switch"]).first()
                    if not connection_ept:
                        CustomerConnectionEndpoint.objects.create(
                            customer_connection=connection,
                            port_name=port["name"],
                            switch_ip=port["switch"]
                        )

                # vincular TAG
                tag = Tag.objects.filter(tag=data["tag"]["tag"],ix=ix).first()
                
                c_service = CustomerService.objects.create(
                    asn=asn,
                    service=service,
                    mlpav6_address=v6_address,
                    tag_or_outer=tag,
                    # mac_address=macs,
                    connection=connection
                )
                c_service.mac_address.add(*macs)   

            except Exception as e:
                # print('Error: ' + str(e))
                print(data)
                errors.append('MLPAv6 Service: {0} -- {1}'.format(str(e), name))    

        

        # Bilateral: importa dados das Bilaterais
        response = requests.get(api + 'import-data/get_bilateral')
        rJSON = response.json()
        bilateral = ServiceType.objects.get(name="Bilateral")
        for data in rJSON:
            print(data)
            del data['description']
            # del data['ix']
            try:
                ix = IX.objects.get(pk=data['tag']['ix'])
                asn = ASN.objects.get(pk=data['asn'])
                asn_owner =  ASN.objects.get(pk=data["customer_channel"]["asn"])
                service = Service.objects.filter(service_type=bilateral, ix=ix).first()
                macs = MACAddress.objects.filter(address__in=data['mac_addresses'])
                name = "{0}-{1}-{2}".format(asn_owner.number, ix.code, data["customer_channel"]["name"])   
                # checa se ja exista ou create connection
                connection = CustomerConnection.objects.filter(asn=asn_owner, name=name).first()
                if not connection:  
                    # errors.append("CustomerConnection para VLAN nao encontrada -- " + str(name))              
                    connection = CustomerConnection.objects.create(
                        name=name,
                        is_lag=data["customer_channel"]["is_lag"],
                        asn=asn_owner,
                        ticket=data["last_ticket"],
                        # configured_capacity= TODO: obter dado da porta pelo channelport na APi do Hercules (pode ser mais de 1 porta na interface)
                    )

                ports = data["ports"]
                for port in ports:
                    connection_ept = CustomerConnectionEndpoint.objects.filter(
                        customer_connection=connection, port_name=port["name"], switch_ip=port["switch"]).first()
                    if not connection_ept:
                        CustomerConnectionEndpoint.objects.create(
                            customer_connection=connection,
                            port_name=port["name"],
                            switch_ip=port["switch"]
                        )

                # vincular TAG
                tag = Tag.objects.filter(tag=data["tag"]["tag"],ix=ix).first()
                
                c_service = CustomerService.objects.create(
                    asn=asn,
                    service=service,
                    tag_or_outer=tag,
                    # mac_address=macs,
                    connection=connection
                )
                c_service.mac_address.add(*macs)   
            
            except Exception as e:
                # print('Error: ' + str(e))
                print(data)
                errors.append('Bilateral: {0} -- {1}'.format(str(e), name))     


        
        # importar dados dos demais IXs com prefixos 
        # read file
        print(sys.path)
        with open(sys.path[0] + '/get_contacts.json.php.json', 'r') as f:
            data=f.read()

        # parse file
        obj = json.loads(data)
        for item in obj['ix']:            
            try:
                ix_data = {}
                # ix_data['code'] = obj['ix'][item]['code']
                # code = ''.join(random.choice(string.ascii_letters).lower() for x in range(3))
                ix_data['code'] = item
                ix_data['shortname'] = obj['ix'][item]['cidade'].lower() + '.' + obj['ix'][item]['estado'].lower()
                ix_data['fullname'] =  obj['ix'][item]['cidade'] + ' - ' +  obj['ix'][item]['estado']
                ix_data['ipv4_prefix'] = obj['ix'][item]['ipv4_prefix']
                ix_data['ipv6_prefix'] = obj['ix'][item]['ipv6_prefix']
                # ix_data['management_prefix'] = obj['ix'][item]['management_prefix']
                ix_data['management_prefix'] = '192.168.9.0/24'
                ix_data['tags_policy'] = 'ix_managed'
                # ix_data['create_tags'] = False
                # ix_data['create_ips'] = False
                print(ix_data)
                IX.objects.get_or_create(**ix_data)
                # ix = IX.objects.get(pk=code)
                # ix.delete()

            except Exception as e:
                # print('Error: ' + str(e))
                errors.append('IX: ' + str(e))

         

        
        if errors:
            self.stdout.write(self.style.ERROR('Erros na importacao'))
            for item in errors:
                print(item)
        else:
            self.stdout.write(self.style.SUCCESS('Os dados foram importados com sucesso'))
        self.stdout.write(self.style.SUCCESS('Fim do script de importacao'))
