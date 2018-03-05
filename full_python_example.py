import os
import traceback
import azure
import sys
import time 
from datetime import datetime

from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.storage import StorageManagementClient 
from azure.mgmt.compute.models import DiskCreateOption
from azure.mgmt.compute.models import DiskCreateOption
from msrestazure.azure_exceptions import CloudError
from haikunator import Haikunator
import json 
haikunator = Haikunator()


with open("credentials.json", 'r') as f:
    data2 = json.loads(f.read())
    AZURE_TENANT_ID = data2["azurecred"]["AZURE_TENANT_ID"]
    AZURE_CLIENT_ID= data2["azurecred"]["AZURE_CLIENT_ID"]
    AZURE_CLIENT_SECRET= data2["azurecred"]["AZURE_CLIENT_SECRET"]
    AZURE_SUBSCRIPTION_ID=data2["azurecred"]["AZURE_SUBSCRIPTION_ID"]
    LOCATION = data2["DC_LOCATION"]
    GROUP_NAME = data2["GROUP_NAME"]
    USERNAME = data2["VM_details"]["USERNAME"]
    PASSWORD = data2["VM_details"]["PASSWORD"]
    VM_NAME_ROOT = data2["VM_details"]["VM_NAME_ROOT"]
    VNET_NAME = data2["VNET_details"]["VNET_NAME"]
    NUMBER_OF_SUBNET =  data2["VNET_details"]["SUBNET_NUMBER"]
    SUBNET_NAME_ROOT = data2["VNET_details"]["SUBNET_NAME_ROOT"]
    VNET_ADDRESS_RANGE = data2["VNET_details"]["VNET_ADDRESS_RANGE"]
    SUBNET_NET_ADDRESS_ROOT_RANGE = data2["VNET_details"]["SUBNET_NET_ADDRESS_ROOT_RANGE"]
    NIC_NAME_ROOT = data2["VNET_details"]["NIC_NAME_ROOT"]
    IP_CONFIG_NAME_ROOT = data2["VNET_details"]["IP_CONFIG_NAME_ROOT"]
    #VM_REFERENCE_LINUX = data2["VNET_details"]["VM_LINUX"]
    #VM_REFERENCE_WINDOWS = data2["VNET_details"]["VM_MS"]
    DATADISK_NAME_ROOT = data2["STORAGE"]["DATADISK_NAME_ROOT"]
    VM_PUBLISHER = data2["VM_details"]["VM_LINUX"]["VM_PUBLISHER"]
    VM_OFFER = data2["VM_details"]["VM_LINUX"]["VM_OFFER"]
    VM_SKU = data2["VM_details"]["VM_LINUX"]["VM_SKU"]
    VM_VERSION = data2["VM_details"]["VM_LINUX"]["VM_VERSION"]
    DATADISK_NAME_ROOT = data2["STORAGE"]["DATADISK_NAME_ROOT"]
    LB_FRONT_NAME = data2["LBs"]["LB_FRONT_NAME"]
    LB_PUBLIC_IP_NAME = data2["LBs"]["LB_PUBLIC_IP_NAME"]
    LB_FRONT_PUBLIC_IP_POOL_NAME = data2["LBs"]["LB_FRONT_PUBLIC_IP_POOL_NAME"]
    LB_FRONT_PUBLIC_DNS_NAME = data2["LBs"]["LB_FRONT_PUBLIC_DNS_NAME"]
    LB_FRONT_PROBE_ROOT_NAME = data2["LBs"]["LB_FRONT_PROBE_ROOT_NAME"]
    LB_FRONT_RULE_ROOT_NAME = data2["LBs"]["LB_FRONT_RULE_ROOT_NAME"]
    LB_FRONT_ADDRESS_POOL_NAME = data2["LBs"]["LB_FRONT_ADDRESS_POOL_NAME"]
    PORT_TO_PROBE = data2["LBs"]["LB_FRONT_RULE_PROB_PORT_1_FRONT"]
    LB_FRONT_PUBLIC_DNS_NAME = data2["LBs"]["LB_FRONT_PUBLIC_DNS_NAME"]
    AVAILABILITY_SET_NAME = data2["HA_details"]["FRONT_AVAILABILITY_SET_NAME"]
    URL_CUSTOM_SCRIPT_FRONT = data2["VM_details"]["URL_CUSTOM_SCRIPT_FRONT"]
    URL_CUSTOM_SCRIPT_FRONT = data2["VM_details"]["URL_CUSTOM_SCRIPT_FRONT"]
    URL_CUSTOM_SCRIPT_MIDDLE = data2["VM_details"]["URL_CUSTOM_SCRIPT_MIDDLE"]
    URL_CUSTOM_SCRIPT_DB = data2["VM_details"]["URL_CUSTOM_SCRIPT_DB"]
    CMD_CUSTOM_SCRIPT_FRONT = data2["VM_details"]["CMD_CUSTOM_SCRIPT_FRONT"]
    CMD_CUSTOM_SCRIPT_MIDDLE = data2["VM_details"]["CMD_CUSTOM_SCRIPT_MIDDLE"]
    CMD_CUSTOM_SCRIPT_DB = data2["VM_details"]["CMD_CUSTOM_SCRIPT_DB"]

f.close()

LOGGING_DATE_ROOT = datetime.now()
LOGGING_DATE = LOGGING_DATE_ROOT.strftime('%Y/%m/%d %H:%M:%S')
OS_DISK_NAME = 'azure-sample-osdisk'
STORAGE_ACCOUNT_NAME = haikunator.haikunate(delimiter='')
NUMBER_OF_VM_PER_SUBNET = 0
def get_credentials():
    AZURE_SUBSCRIPTION_ID_STR=str(AZURE_SUBSCRIPTION_ID)
    subscription_id = AZURE_SUBSCRIPTION_ID_STR
    credentials = ServicePrincipalCredentials(
        client_id=AZURE_CLIENT_ID,
        secret=AZURE_CLIENT_SECRET,
        tenant=AZURE_TENANT_ID
    )
    return credentials, subscription_id
#
# Create all clients with an Application (service principal) token provider
#
print ' *********************************** DEBUG *** %s CREATE CLIENTS   ' % (LOGGING_DATE)
credentials, subscription_id = get_credentials()
resource_client = ResourceManagementClient(credentials, subscription_id)
print ' *********************************** DEBUG *** %s CREATED resource_client   '  % (LOGGING_DATE)
compute_client = ComputeManagementClient(credentials, subscription_id)
print ' *********************************** DEBUG *** %s CREATED compute_client   ' % (LOGGING_DATE)
network_client = NetworkManagementClient(credentials, subscription_id)
print ' *********************************** DEBUG *** %s CREATED network_client   '  % (LOGGING_DATE)
storage_client = StorageManagementClient(credentials, subscription_id)
print ' *********************************** DEBUG *** %s CREATED storage_client   '  % (LOGGING_DATE)

def create_ressource_group(resource_client,GROUP_NAME,LOCATION):
    # Create Resource group
    print('\nCreate Resource Group...\n')
    resource_client.resource_groups.create_or_update(GROUP_NAME, {'location': LOCATION})

def create_vnet(network_client,GROUP_NAME,VNET_NAME,LOCATION,VNET_ADDRESS_RANGE):
    # Create VNet
    print('\nCreate Vnet...\n')
    async_vnet_creation = network_client.virtual_networks.create_or_update(
        GROUP_NAME,
        VNET_NAME,
        {
            'location': LOCATION,
            'address_space': {
                'address_prefixes': [VNET_ADDRESS_RANGE]
            }
        }
    )
    async_vnet_creation.wait()
    print ' *********************************** DEBUG *** %s CREATE VNET \n %s   ' % (LOGGING_DATE,VNET_ADDRESS_RANGE) 
    #print async_vnet_creation.result()
    return async_vnet_creation.result()

def create_public_IP (network_client,LOCATION,GROUP_NAME,LB_FRONT_PUBLIC_DNS_NAME,LB_PUBLIC_IP_NAME):
    # Create PublicIP
    print('\nCreate Public IP...\n')
    global public_ip_info
    public_ip_parameters = {
        'location': LOCATION,
        'public_ip_allocation_method': 'static',
        'dns_settings': {
            'domain_name_label': LB_FRONT_PUBLIC_DNS_NAME
            },
        'idle_timeout_in_minutes': 4
        }
    async_publicip_creation = network_client.public_ip_addresses.create_or_update(
        GROUP_NAME,
        LB_PUBLIC_IP_NAME,
        public_ip_parameters
        )
    public_ip_info = async_publicip_creation.result()
    print ' *********************************** DEBUG *** %s PUBLIC IP INFO IS \n %s   ' % (LOGGING_DATE,public_ip_info)
    #print public_ip_info
    return public_ip_info

def construct_fip_id(subscription_id):
    """Build the future FrontEndId based on components name.
    """
    return ('/subscriptions/{}'
            '/resourceGroups/{}'
            '/providers/Microsoft.Network'
            '/loadBalancers/{}'
            '/frontendIPConfigurations/{}').format(subscription_id, GROUP_NAME, LB_FRONT_NAME, LB_FRONT_PUBLIC_IP_POOL_NAME)

def construct_bap_id(subscription_id):
    """Build the future BackEndId based on components name.
    """
    return ('/subscriptions/{}'
            '/resourceGroups/{}'
            '/providers/Microsoft.Network'
            '/loadBalancers/{}'
            '/backendAddressPools/{}').format(subscription_id, GROUP_NAME, LB_FRONT_NAME, LB_FRONT_ADDRESS_POOL_NAME)

def construct_probe_id(subscription_id):
    """Build the future ProbeId based on components name.
    """
    return ('/subscriptions/{}'
            '/resourceGroups/{}'
            '/providers/Microsoft.Network'
            '/loadBalancers/{}'
            '/probes/{}').format(
                subscription_id, GROUP_NAME, LB_FRONT_NAME, "PROBE_NAME_1_PORT_80")

def create_LB_front ():
    global load_balancing_rules
    global probes
    global backend_address_pools
    global inbound_nat_rules
    global lb_async_creation                
    global lb_info
    # Building a FrontEndIpPool
    print('\nCreate FrontEndIpPool configuration... \n')
    frontend_ip_configurations = [{
        'name': LB_FRONT_PUBLIC_IP_POOL_NAME,
        'private_ip_allocation_method': 'Dynamic',
        'public_ip_address': {
            'id': public_ip_info.id
        }
    }]
    print ' *********************************** DEBUG *** %s frontend_ip_configurations IS \n %s   \n' % (LOGGING_DATE,frontend_ip_configurations)
    # Building a BackEnd address pool
    print('\nCreate BackEndAddressPool configuration... \n')
    backend_address_pools = [{
        'name': LB_FRONT_ADDRESS_POOL_NAME
    }]
    print ' *********************************** DEBUG *** %s backend_address_pools IS \n %s   \n' % (LOGGING_DATE,backend_address_pools)
    # Building a HealthProbe
    print('\nCreate HealthProbe configuration... \n')
    probes = [{
        'name': "PROBE_NAME_1_PORT_80",
        'protocol': 'Http',
        'port': 80,
        'interval_in_seconds': 15,
        'number_of_probes': 4,
        'request_path': 'healthprobe.aspx'
    }]
    print ' *********************************** DEBUG *** %s probes IS \n %s   \n' % (LOGGING_DATE,probes)
    # Building a LoadBalancer rule
    print('\nCreate LoadBalancerRule configuration... \n')
    load_balancing_rules = [{
        'name': "LB_RULE_NAME_PORT_80_TO_80",
        'protocol': 'tcp',
        'frontend_port': 80,
        'backend_port': 80,
        'idle_timeout_in_minutes': 4,
        'enable_floating_ip': False,
        'load_distribution': 'Default',
        'frontend_ip_configuration': {
            'id': construct_fip_id(subscription_id)
        },
        'backend_address_pool': {
            'id': construct_bap_id(subscription_id)
        },
        'probe': {
            'id': construct_probe_id(subscription_id)
        }
    }]
    print ' *********************************** DEBUG *** %s load_balancing_rules IS \n %s   \n' % (LOGGING_DATE,load_balancing_rules)
    # Building InboundNATRule1
    print('\nCreate InboundNATRule1 configuration... \n')
    inbound_nat_rules = [{
        'name': "NAT_RULE_FRONT_22_TO_22",
        'protocol': 'tcp',
        'frontend_port': 22,
        'backend_port': 22,
        'enable_floating_ip': False,
        'idle_timeout_in_minutes': 4,
        'frontend_ip_configuration': {
            'id': construct_fip_id(subscription_id)
        }
    }]
    print ' *********************************** DEBUG *** %s inbound_nat_rules IS \n %s   \n' % (LOGGING_DATE,inbound_nat_rules)
    # Building InboundNATRule2
    print('\nCreate InboundNATRule2 configuration... \n')
    inbound_nat_rules.append({
        'name': "NAT_RULE_FRONT_21_TO_21",
        'protocol': 'tcp',
        'frontend_port': 21,
        'backend_port': 21,
        'enable_floating_ip': False,
        'idle_timeout_in_minutes': 4,
        'frontend_ip_configuration': {
            'id': construct_fip_id(subscription_id)
        }
    })
    print ' *********************************** DEBUG *** %s inbound_nat_rules IS \n %s   \n' % (LOGGING_DATE,inbound_nat_rules)
    # Creating Load Balancer
    print('\nCreating Load Balancer... \n')
    lb_async_creation = network_client.load_balancers.create_or_update(
        GROUP_NAME,
        LB_FRONT_NAME,
        {
            'location': LOCATION,
            'frontend_ip_configurations': frontend_ip_configurations,
            'backend_address_pools': backend_address_pools,
            'probes': probes,
            'load_balancing_rules': load_balancing_rules,
            'inbound_nat_rules' :inbound_nat_rules
        }
    )
    print ' *********************************** DEBUG *** %s lb_async_creation IS \n %s   \n' % (LOGGING_DATE,lb_async_creation)
    lb_info = lb_async_creation.result()
    return load_balancing_rules , probes , backend_address_pools , inbound_nat_rules , lb_async_creation , lb_info

SUBNET_LIST = []
SUBNET_LIST_IDs = []

def create_subent(network_client,GROUP_NAME,VNET_NAME,SUBNET_NAME_ROOT,SUBNET_NET_ADDRESS_ROOT_RANGE,NUMBER_OF_SUBNET_INC):
    # Create Subnet
    global subnet_info
    print('\nCreate Subnet...\n')
    SUBNET_NAME = "%s%s%s" % (VNET_NAME,SUBNET_NAME_ROOT,NUMBER_OF_SUBNET_INC)
    print " *********************************** DEBUG *** %s SUBNET_NAME is \n %s   \n " % (LOGGING_DATE, SUBNET_NAME)
    VNET_ADDRESS_PREFIX = "%s%s.0/24" % (SUBNET_NET_ADDRESS_ROOT_RANGE,NUMBER_OF_SUBNET_INC)
    print " *********************************** DEBUG *** %s VNET_ADDRESS_PREFIX is \n %s   \n" % (LOGGING_DATE, VNET_ADDRESS_PREFIX)
    async_subnet_creation = network_client.subnets.create_or_update(
        GROUP_NAME,
        VNET_NAME,
        SUBNET_NAME,
        {'address_prefix': VNET_ADDRESS_PREFIX}
    )
    print ' *********************************** DEBUG *** %s CREATED SUBNET \n %s   \n' % (LOGGING_DATE, VNET_ADDRESS_PREFIX) 
    subnet_info = async_subnet_creation.result()
    SUBNET_ID = subnet_info.id 
    #print subnet_info
    SUBNET_LIST.append(SUBNET_NAME)
    print ' *********************************** DEBUG *** %s SUBNET LIST IS COMPOSED OF \n %s   \n' % (LOGGING_DATE, SUBNET_LIST)    
    SUBNET_LIST_IDs.append(SUBNET_ID)
    print ' *********************************** DEBUG *** %s SUBNET LIST IS COMPOSED OF \n %s   \n ' % (LOGGING_DATE, SUBNET_LIST_IDs)  

NIC_LIST = []

def create_nic_internal(network_client,SUBNET_NAME,NIC_NAME_ROOT,NIC_NAME_ROOT_INC,GROUP_NAME,LOCATION,IP_CONFIG_NAME_ROOT,IP_CONFIG_NAME_ROOT_INC,SUBNET_ID,ADDRESS_POOL_ID_FOR_NIC):
    # Create NIC
    print('\nCreate NIC...\n')
    NIC_NAME = "%s%s%s" % (SUBNET_NAME,NIC_NAME_ROOT,NIC_NAME_ROOT_INC)
    print " *********************************** DEBUG *** %s NIC_NAME is \n %s   \n " % (LOGGING_DATE, NIC_NAME)
    IP_CONFIG_NAME = "%s%s%s" % (NIC_NAME,IP_CONFIG_NAME_ROOT,IP_CONFIG_NAME_ROOT_INC)
    print " *********************************** DEBUG *** %s IP_CONFIG_NAME is \n %s   \n" % (LOGGING_DATE, IP_CONFIG_NAME)
    print " *********************************** DEBUG *** %s SUBNET_NAME TO BE INJECTED is \n %s   \n" % (LOGGING_DATE, SUBNET_NAME)
    print " *********************************** DEBUG *** %s SUBNET_ID TO BE INJECTED is \n %s   \n " % (LOGGING_DATE, SUBNET_ID)
    async_nic_creation = network_client.network_interfaces.create_or_update(
        GROUP_NAME,
        NIC_NAME,
        {
            'location': LOCATION,
            'ip_configurations': [{
                'name': IP_CONFIG_NAME,
                'subnet': {
                    'id': SUBNET_ID
                },
                'load_balancer_backend_address_pools': [{
                    'id': ADDRESS_POOL_ID_FOR_NIC
                }]
            }]
        }
    )
    print ' *********************************** DEBUG *** %s CREATED NIC   ' % (LOGGING_DATE)
    #print async_nic_creation.result()
    NIC_LIST.append(NIC_NAME)
    print ' *********************************** DEBUG *** %s SUBNET LIST IS COMPOSED OF \n %s   \n ' % (LOGGING_DATE,NIC_LIST)
    return async_nic_creation.result()

DATADISK_LIST = [] 
def create_disks(GROUP_NAME,DATADISK_NAME_ROOT,DATADISK_NAME_ROOT_INC,LOCATION):
    # Create managed data disk
    print('\nCreate (empty) managed Data Disk...\n')
    DATADISK_NAME = "%s%s%s" % (DATADISK_NAME_ROOT,DATADISK_NAME_ROOT_INC)
    async_disk_creation = compute_client.disks.create_or_update(
        GROUP_NAME,
        DATADISK_NAME,
        {
            'location': LOCATION,
            'disk_size_gb': 1,
            'creation_data': {
                'create_option': DiskCreateOption.empty
            }
        }
    )
    data_disk = async_disk_creation.result()

def create_vm_parameters(LOCATION,VM_NAME,USERNAME,PASSWORD,VM_PUBLISHER,VM_OFFER,VM_SKU,VM_VERSION,VM_NIC_ID,AVAILSET_ID):
    #Create the VM parameters structure
    return {
        'location': LOCATION,
        'os_profile': {
            'computer_name': VM_NAME,
            'admin_username': USERNAME,
            'admin_password': PASSWORD
        },
        'hardware_profile': {
            'vm_size': 'Standard_DS1_v2'
        },
        'storage_profile': {
            'image_reference': {
                'publisher': VM_PUBLISHER,
                'offer': VM_OFFER,
                'sku': VM_SKU,
                'version': VM_VERSION
            },
        },
        'network_profile': {
            'network_interfaces': [{
                'id': VM_NIC_ID,
            }]
        },
        'availability_set': {
            'id': AVAILSET_ID
            }
    }

def availability_set(GROUP_NAME,LOCATION,AVAILABILITY_SET_NAME,FAULT_DOMAIN_COUNT):
    # Create availability set
    global availability_set_info
    global availability_set_info_id
    print('Create availability set')
    availability_set_info = compute_client.availability_sets.create_or_update(
        GROUP_NAME,
        AVAILABILITY_SET_NAME,
        {'location': LOCATION,
         'sku': { 'name': 'Aligned' },
         'platform_fault_domain_count': FAULT_DOMAIN_COUNT
         }
        )
    availability_set_info_id = availability_set_info.id
    return availability_set_info_id , availability_set_info

VM_LIST=[]
def create_vm(LOCATION,TIER,VM_NAME_ROOT,VM_NAME_ROOT_INC,USERNAME,PASSWORD,VM_PUBLISHER,VM_OFFER,VM_SKU,VM_VERSION,VM_NIC_ID,AVAILSET_ID):
    # Create Linux VM
    TIER_NAME=TIER
    VM_NAME = "%s%s%s"%(VM_NAME_ROOT,TIER_NAME,VM_NAME_ROOT_INC)
    print('\nCreating Linux Virtual Machine...\n')
    vm_parameters = create_vm_parameters(LOCATION,VM_NAME,USERNAME,PASSWORD,VM_PUBLISHER,VM_OFFER,VM_SKU,VM_VERSION,VM_NIC_ID,AVAILSET_ID)
    print ' *********************************** DEBUG *** %s VM PARAM ARE \n %s   \n ' % (LOGGING_DATE,vm_parameters)
    async_vm_creation = compute_client.virtual_machines.create_or_update(GROUP_NAME, VM_NAME, vm_parameters)
    print ' *********************************** DEBUG *** %s VM CREATION OF \n %s   \n ' % (LOGGING_DATE,VM_NAME)    
    VM_LIST.append(VM_NAME)
    print ' *********************************** DEBUG *** %s VM LIST IS MADE OF \n %s   \n ' % (LOGGING_DATE,VM_LIST)
    
def create_param_extension_for_VMs(LOCATION,VM_TO_UPDATE,SCRIPT_URL,COMMAND_TO_APPLY):
#def create_param_extension_for_VMs(LOCATION,VM_TO_UPDATE):
    global params_create
    params_create = azure.mgmt.compute.models.VirtualMachineExtension(
        location="eastus",
        #name='MyCustomScriptExtension',
        publisher='Microsoft.Compute',
        #extension_type='CustomScriptExtension',
        virtual_machine_extension_type='CustomScriptExtension',
        type_handler_version='1.7',
        auto_upgrade_minor_version=True,
        settings={
            "fileUris": [
                SCRIPT_URL
                ]
            },
        protected_settings={
            "commandToExecute": COMMAND_TO_APPLY,
            },
        )
    
    result_create = compute_client.virtual_machine_extensions.create_or_update(
        GROUP_NAME,
        VM_TO_UPDATE,
        "VARIABLE_THAT_I_DO_NOT_UNDERSTAND",
        params_create,
        )

#create RG
create_ressource_group(resource_client,GROUP_NAME,LOCATION)

#create create_public_IP
create_public_IP (network_client,LOCATION,GROUP_NAME,LB_FRONT_PUBLIC_DNS_NAME,LB_PUBLIC_IP_NAME)
construct_fip_id(subscription_id)

#create LB Front 
create_LB_front ()

#create VNET
create_vnet(network_client,GROUP_NAME,VNET_NAME,LOCATION,VNET_ADDRESS_RANGE)

#create SUBNET
NUMBER_OF_SUBNET_INC = 1
NUMBER_OF_SUBNET_CORRECTED = NUMBER_OF_SUBNET+1
for NUMBER_OF_SUBNET_INC in range(1,NUMBER_OF_SUBNET_CORRECTED):
    print NUMBER_OF_SUBNET_INC
    create_subent(network_client,GROUP_NAME,VNET_NAME,SUBNET_NAME_ROOT,SUBNET_NET_ADDRESS_ROOT_RANGE,NUMBER_OF_SUBNET_INC)
    NUMBER_OF_SUBNET_INC+=1

##############################################################
# From here, we create the FIRST TIER: VMs and NICs          #
##############################################################
#Reading data from Json
with open("credentials.json", 'r') as f:
    data2 = json.loads(f.read())
    VM_PUBLISHER = data2["VM_details"]["VM_LINUX"]["VM_PUBLISHER"]
    VM_OFFER = data2["VM_details"]["VM_LINUX"]["VM_OFFER"]
    VM_SKU = data2["VM_details"]["VM_LINUX"]["VM_SKU"]
    VM_VERSION = data2["VM_details"]["VM_LINUX"]["VM_VERSION"]
    DATADISK_NAME_ROOT = data2["STORAGE"]["DATADISK_NAME_ROOT"]
    AVAILABILITY_SET_NAME = data2["HA_details"]["FRONT_AVAILABILITY_SET_NAME"]
f.close()

#create NIC and VM's of First tier 
#Collecting backend pools to of First tier for the first tier NICs 
ADDRESS_POOL_ID_FOR_NIC = lb_info.backend_address_pools[0].id
print ' *********************************** DEBUG *** %s ADDRESS_POOL_ID_FOR_NIC is \n %s   \n ' % (LOGGING_DATE,ADDRESS_POOL_ID_FOR_NIC)
NUMBER_OF_VM_PER_SUBNET = 3
NUMBER_OF_VM_PER_SUBNET_CORRECTED = NUMBER_OF_VM_PER_SUBNET+1
TEMP_INC_FOR_SUBNET_IN_LIST = 1
SUBNET_NAME_TIER_1=SUBNET_LIST[0]
print ' *********************************** DEBUG *** %s CREATION OF NIC IN SUBNET TIER is \n %s   \n ' % (LOGGING_DATE,SUBNET_NAME_TIER_1)
#starting NIC CREATION IN SUBNET SUBNET_NAME_TIER_1
SUBNET_ID=SUBNET_LIST_IDs[0]
print ' *********************************** DEBUG *** %s CREATION OF NIC IN SUBNET ID is \n %s   \n ' % (LOGGING_DATE,SUBNET_ID)
SUBNET_NAME = SUBNET_NAME_TIER_1
#temp value for NIC and VMs incremental creation
NIC_NAME_ROOT_INC = 1
IP_CONFIG_NAME_ROOT_INC=1
VM_NAME_ROOT_INC = 1
#Set fault domaine in Availset = the number of VM in the subnet 
FAULT_DOMAIN_COUNT = NUMBER_OF_VM_PER_SUBNET
availability_set(GROUP_NAME,LOCATION,AVAILABILITY_SET_NAME,FAULT_DOMAIN_COUNT)
print ' *********************************** DEBUG *** %s CREATION OF AVAILSET DONE ID is \n %s   \n ' % (LOGGING_DATE,availability_set_info_id)
TIER="front-"
for NUMBER_OF_VM_PER_SUBNET_COUNT in range(1,NUMBER_OF_VM_PER_SUBNET_CORRECTED):
    print ' *********************************** DEBUG *** %s START CREATION OF NIC %s IN SUBNET %s ' % (LOGGING_DATE,NUMBER_OF_VM_PER_SUBNET_COUNT,SUBNET_NAME)
    NIC = create_nic_internal(network_client,SUBNET_NAME,NIC_NAME_ROOT,NIC_NAME_ROOT_INC,GROUP_NAME,LOCATION,IP_CONFIG_NAME_ROOT,IP_CONFIG_NAME_ROOT_INC,SUBNET_ID,ADDRESS_POOL_ID_FOR_NIC)
    # NIC_ID is returned 
    print "--------------------------------------------------------", NIC.id
    VM_NIC_ID = NIC.id
    create_vm(LOCATION,TIER,VM_NAME_ROOT,VM_NAME_ROOT_INC,USERNAME,PASSWORD,VM_PUBLISHER,VM_OFFER,VM_SKU,VM_VERSION,VM_NIC_ID,availability_set_info_id)
    VM_TO_UPDATE="%s%s%s" % (VM_NAME_ROOT,TIER,VM_NAME_ROOT_INC) 
    SCRIPT_URL = URL_CUSTOM_SCRIPT_FRONT
    COMMAND_TO_APPLY = CMD_CUSTOM_SCRIPT_FRONT
    create_param_extension_for_VMs(LOCATION,VM_TO_UPDATE,SCRIPT_URL,COMMAND_TO_APPLY)
    #create_param_extension_for_VMs(LOCATION,VM_TO_UPDATE)
    IP_CONFIG_NAME_ROOT_INC+=1
    NIC_NAME_ROOT_INC+=1
    VM_NAME_ROOT_INC+=1
TEMP_INC_FOR_SUBNET_IN_LIST+=1
print ' *********************************** DEBUG *** %s GO TO SUBNET ID \n %s   \n ' % (LOGGING_DATE,TEMP_INC_FOR_SUBNET_IN_LIST)
