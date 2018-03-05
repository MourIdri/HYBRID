import subprocess
import time
import os
import json
import sys
import logging
import time
import datetime

def create_RG(RGROUP,location):
	# Create a resource group VVV
	cmd_rg_create='az group create'+' '+'--resource-group'+' '+RGROUP+' '+'--location'+' '+ location
	print cmd_rg_create
	os.system(cmd_rg_create)
def command_create_NSG (RGROUP,NSG_name_root,tier):	
	name_NSG = "%s-%s" % (NSG_name_root,tier)
	cmd_nsg='az network nsg create'+' '+'--resource-group'+' '+RGROUP+' '+'--name'+' '+ name_NSG
	print cmd_nsg
	os.system(cmd_nsg)
def command_create_NSG_rule (RGROUP,NSG_name_root,tier,port_to_process,direction_rule,priority):
	# Create a network security group rule for port 22.
	name_NSG = "%s-%s" % (NSG_name_root,tier)
	name_NSG_rule = "%s-rule-%s_%s" % (name_NSG,port_to_process,direction_rule)
	cmd_part_1 ='az network nsg rule create'+' '+'--resource-group'+' '+RGROUP+' '+'--nsg-name'+' '+ name_NSG
	cmd_part_2 ='--name'+' '+name_NSG_rule+' '+'--protocol tcp --direction'+' '+direction_rule
	cmd_part_3 ='--source-address-prefix'+' '+"'*'"+' '+'--source-port-range'+' '+"'*'"+' '+'--destination-address-prefix'+' '+"'*'"
	cmd_part_4 ='--destination-port-range'+' '+str(port_to_process)+' '+'--access allow --priority'+' '+ priority
	cmd_NSG_rule = cmd_part_1+' '+cmd_part_2+' '+cmd_part_3+' '+cmd_part_4
	print cmd_NSG_rule
	os.system(cmd_NSG_rule)
def create_list_NSG(list_of_port,direction_rule,priority_root):
	INC_NSG_RULES = 0
	for port_to_process in portlist_NSG_FRONT:
		priority="%s%s" % (priority_root,INC_NSG_RULES)
		command_create_NSG_rule (RGROUP,NSG_name_root,tier,port_to_process,direction_rule,priority)
		INC_NSG_RULES+=1
def create_vnet(RGROUP,location,vnet_general_name,vnet_general_IP_RANGE):
	# Create a virtual network VVV
	cmd_part_1 = 'az network vnet create'+' '+'--resource-group'+' '+RGROUP+' '+'--location'+' '+ location
	cmd_part_2 ='--name'+' '+vnet_general_name+' '+'--address-prefix'+' '+vnet_general_IP_RANGE
	cmd_vnet_create = cmd_part_1+' '+cmd_part_2
	print cmd_vnet_create
	os.system(cmd_vnet_create)
def create_subnet(subnet_level,tier,RGROUP,vnet_general_name,IP_RANGE):
	name_subnet = "%s-subnet-tier-%s" % (vnet_general_name,tier)
	name_NSG = "NGS-generic-linux-N-tier-%s" % (tier)
	cmd_part_1 ='az network vnet subnet create'+' '+'--address-prefix'+' '+IP_RANGE+' '+'--name'+' '+ name_subnet
	cmd_part_2 ='--resource-group'+' '+RGROUP+' '+'--vnet-name'+' '+vnet_general_name
	cmd_part_3 ='--network-security-group'+' '+name_NSG
	cmd_create_subnet = cmd_part_1+' '+cmd_part_2+' '+cmd_part_3
	print cmd_create_subnet
	os.system(cmd_create_subnet)
def create_public_IP (RGROUP,IP_PU_NAME,DNS_NAME):
	# Create a public IP address for the front end web app VVV
	cmd_part_1 = 'az network public-ip create --resource-group'+' '+RGROUP
	cmd_part_2 = ' '+'--name'+' '+IP_PU_NAME+' '+'--dns-name'+' '+DNS_NAME+' '+'--allocation-method Static'
	cmd_create_public_IP = cmd_part_1+' '+cmd_part_2
	print cmd_create_public_IP
	os.system(cmd_create_public_IP)
def create_public_LB(RGROUP,LB_NAME,IP_PU_NAME,LB_FRONT_POOL,LB_BACK_POOL):
	# Create an Azure Load Balancer.
	cmd_part_1 = 'az network lb create --resource-group'+' '+RGROUP+' '
	cmd_part_2 = ' '+'--name'+' '+LB_NAME+' '+'--public-ip-address'+' '+IP_PU_NAME+' '+'--frontend-ip-name'+' '+LB_FRONT_POOL
	cmd_part_3 = ' '+'--backend-pool-name'+' '+LB_BACK_POOL
	cmd_create_public_LB = cmd_part_1+' '+cmd_part_2+' '+cmd_part_3
	print cmd_create_public_LB
	os.system(cmd_create_public_LB)
def create_internal_LB(RGROUP,vnet_general_name,tier,LB_NAME,IP_INTER_NAME,LB_FRONT_POOL,LB_BACK_POOL):
	# create loadbalancer between subnet front and subnet backend 
	name_subnet = "%s-subnet-tier-%s" % (vnet_general_name,tier)
	cmd_part_1 = 'az network lb create --resource-group'+' '+RGROUP+' '
	cmd_part_2 = ' '+'--name'+' '+LB_NAME+' '+'--private-ip-address'+' '+IP_INTER_NAME+' '+'--subnet '+' '+name_subnet
	cmd_part_3 = ' '+'--vnet-name'+' '+vnet_general_name+' '+'--backend-pool-name'+' '+LB_BACK_POOL
	cmd_create_internal_LB = cmd_part_1+' '+cmd_part_2+' '+cmd_part_3
	print cmd_create_internal_LB
	os.system(cmd_create_internal_LB)
def create_LB_PROB(RGROUP,LB_NAME,tier, PORT):
	# Creates an LB probe on port 8080.
	prob_name = 'health-prob-%s-%s' % (tier,PORT)
	cmd_part_1 = 'az network lb probe create --resource-group'+' '+RGROUP+' '
	cmd_part_2 = '--lb-name'+' '+LB_NAME+' '+'--name'+' '+prob_name+' '+'--protocol tcp --port'+' '+str(PORT)
	cmd_create_LB_PROB = cmd_part_1+' '+cmd_part_2
	print cmd_create_LB_PROB
	os.system(cmd_create_LB_PROB)	
def create_list_LB_PROB(list_of_port,RGROUP,LB_NAME,tier):
	for PORT in list_of_port:
		create_LB_PROB(RGROUP,LB_NAME,tier, PORT)
def create_LB_RULE(RGROUP,LB_NAME,tier, PORT,LB_FRONT_POOL,LB_BACK_POOL,is_LB_front,is_LB_Front_Public):
	prob_name = 'health-prob-%s-%s' % (tier,PORT)
	rule_name = 'load-balancer-rule-%s-%s' % (tier,PORT)
	cmd_part_1 = 'az network lb rule create --resource-group'+' '+RGROUP
	cmd_part_2 =' '+ '--lb-name'+' '+LB_NAME+' '+'--name'+' '+rule_name+' '+'--protocol tcp --frontend-port'+' '+str(PORT)
	cmd_part_3 =' '+ '--backend-port'+' '+str(PORT)
	cmd_part_4 =' '+'--frontend-ip-name'+' '+LB_FRONT_POOL
	cmd_part_5 =' '+'--backend-pool-name'+' '+LB_BACK_POOL+' '+ '--probe-name '+' '+prob_name
	if is_LB_Front_Public is True :
		cmd_create_LB_RULE = cmd_part_1+' '+cmd_part_2+' '+cmd_part_3+' '+cmd_part_4+' '+cmd_part_5
	else :
		cmd_create_LB_RULE = cmd_part_1+' '+cmd_part_2+' '+cmd_part_3+' '+cmd_part_5
	print cmd_create_LB_RULE
	os.system(cmd_create_LB_RULE)	
def create_list_LB_RULE(list_of_port,RGROUP,LB_NAME,tier,LB_FRONT_POOL,LB_BACK_POOL,is_LB_front,is_LB_Front_Public):
	for PORT in list_of_port:
		create_LB_RULE(RGROUP,LB_NAME,tier, PORT,LB_FRONT_POOL,LB_BACK_POOL,is_LB_front,is_LB_Front_Public)
def create_nic_vm(RGROUP,vmname_var,tier,vnet_general_name,is_LB_front,LB_NAME,LB_BACK_POOL,number_of_Vm):
	name_subnet = "%s-subnet-tier-%s" % (vnet_general_name,tier)
	name_vm = '%s-vm-%s'%(vmname_var,number_of_Vm)
	nic_name = '%s-nic-1' %(name_vm)
	cmd_part_1='az network nic create --resource-group'+' '+RGROUP
	cmd_part_2=' '+'--name'+' '+nic_name
	cmd_part_3=' '+'--vnet-name'+' '+vnet_general_name+' '+'--subnet'+' '+name_subnet
	cmd_part_4=' '+'--lb-name'+' '+LB_NAME
	cmd_part_5=' '+'--lb-address-pools'+' '+LB_BACK_POOL
	if is_LB_front is True :
		cmd_create_nic_vm = cmd_part_1+' '+cmd_part_2+' '+cmd_part_3+' '+cmd_part_4+' '+cmd_part_5
	else :
		cmd_create_nic_vm = cmd_part_1+' '+cmd_part_2+' '+cmd_part_3+' '+cmd_part_4
	#cmd_create_nic_vm = cmd_part_1+' '+cmd_part_2+' '+cmd_part_3+' '+cmd_part_4+' '+cmd_part_5
	print cmd_create_nic_vm
	os.system(cmd_create_nic_vm)	
def create_av_set(RGROUP,tier,fault_domain_count,update_domain_count):
	name='Availability-Set-%s'%(tier)
	cmd_part_1= 'az vm availability-set create --resource-group'+' '+RGROUP
	cmd_part_2=' '+'--name'+' '+name+' '+'--platform-fault-domain-count'+' '+str(fault_domain_count)
	cmd_part_3=' '+'--platform-update-domain-count'+' '+str(update_domain_count)
	cmd_create_av_set = cmd_part_1+' '+cmd_part_2+' '+cmd_part_3
	print cmd_create_av_set
	os.system(cmd_create_av_set)	
def create_vms(RGROUP,vmname_var,tier,user_passwd,user_login,Image_type,number_of_Vm):
	name = '%s-vm-%s'%(vmname_var,number_of_Vm)
	nic_name = '%s-nic-1' %(name)
	name_av_set='Availability-Set-%s'%(tier)
	cmd_part_1 = 'az vm create --resource-group'+' '+RGROUP
	cmd_part_2 =' '+'--name'+' '+name+' '+'--admin-password'+' '+user_passwd
	cmd_part_3 =' '+'--admin-username'+' '+user_login+' '+'--availability-set'+' '+name_av_set
	cmd_part_4=' '+'--nics'+' '+nic_name+' '+'--image'+' '+Image_type+' '+'--size'+' '+Vm_size
	cmd_create_vm = cmd_part_1+' '+cmd_part_2+' '+cmd_part_3+' '+cmd_part_4
	print cmd_create_vm
	os.system(cmd_create_vm)	
def create_vm_extensions(vmname_var,number_of_Vm,RGROUP,extensions):
	extensions_quote = "'%s'" % (extensions)
	name = '%s-vm-%s'%(vmname_var,number_of_Vm)
	cmd_part_1 = 'az vm extension set --resource-group'+' '+RGROUP
	cmd_part_2 =' '+'--vm-name'+' '+name+' '+'--name customScript'
	cmd_part_3 =' '+'--publisher Microsoft.Azure.Extensions --settings '+' '+extensions_quote
	cmd_create_vm_extensions = cmd_part_1+' '+cmd_part_2+' '+cmd_part_3
	print cmd_create_vm_extensions
	os.system(cmd_create_vm_extensions)
def create_vms_list_ha(Number_Of_Vm_Per_Tier,LB_BACK_POOL):
	Number_Of_Vm_Per_Tier
	for inter in range(1,Number_Of_Vm_Per_Tier+1):
		str_inter=str(inter)
		create_nic_vm(RGROUP,vmname_var,tier,vnet_general_name,is_LB_front,LB_NAME,LB_BACK_POOL,str_inter)
		create_vms(RGROUP,vmname_var,tier,user_passwd,user_login,Image_type,str_inter)
def create_vm_extensions_list_ha(Number_Of_Vm_Per_Tier):
	Number_Of_Vm_Per_Tier
	for inter in range(1,Number_Of_Vm_Per_Tier+1):
		str_inter=str(inter)
		create_vm_extensions(vmname_var,str_inter,RGROUP,extensions)
def create_tier (is_Public_front,RGROUP,Tier,NSG_name_root,portlist_NSG_FRONT,subnet_level,IP_RANGE,LB_NAME,is_LB_Front_Public,fault_domain_count,update_domain_count,Image_type,Vm_size,user_passwd,user_login,number_of_nic,extensions,is_LB_front,Number_Of_Vm_Per_Tier):
	if is_Public_front is True :
		IP_PU_NAME ='loaded-balanced-front-web-public-ip' 
		DNS_NAME = 'demofrontweb'
		create_public_IP (RGROUP,IP_PU_NAME,DNS_NAME)
	else:
		pass
	command_create_NSG(RGROUP,NSG_name_root,tier)
	direction_rule ="inbound"
	priority_root="100"
	create_list_NSG(portlist_NSG_FRONT,direction_rule,priority_root)
	priority_root="200"
	create_list_NSG(portlist_NSG_FRONT,direction_rule,priority_root)
	create_subnet(subnet_level,tier,RGROUP,vnet_general_name,IP_RANGE)
	LB_FRONT_POOL = 'demo-front-tier-pool-%s' % (tier)
	LB_BACK_POOL = 'demo-front-from-tier-%s-to-backend-pool'% (tier)
	if is_LB_Front_Public is True :
		create_public_LB(RGROUP,LB_NAME,IP_PU_NAME,LB_FRONT_POOL,LB_BACK_POOL)
	else :
		create_internal_LB(RGROUP,vnet_general_name,tier,LB_NAME,IP_INTER_NAME,LB_FRONT_POOL,LB_BACK_POOL)
	create_list_LB_PROB(list_of_port_Load_abalanced_front,RGROUP,LB_NAME,tier)
	create_list_LB_RULE(list_of_port_Load_abalanced_front,RGROUP,LB_NAME,tier,LB_FRONT_POOL,LB_BACK_POOL,is_LB_front,is_LB_Front_Public)
	create_av_set(RGROUP,tier,fault_domain_count,update_domain_count)
	create_vms_list_ha(Number_Of_Vm_Per_Tier,LB_BACK_POOL)
	create_vm_extensions_list_ha(Number_Of_Vm_Per_Tier)
RGROUP="RGMOURAD_0"
#CREATE Ressources Goup
location= "eastus"
create_RG(RGROUP,location)
#CREATE General VNET
vnet_general_name = "vnet-root"
vnet_general_IP_RANGE = "10.100.0.0/14"
create_vnet(RGROUP,location,vnet_general_name,vnet_general_IP_RANGE)

print" ****************************************************************************** "
print" ** --------------------------- START FIRST TIER  --------------------------- * "
print" ****************************************************************************** "

#CREATE PUBLIC IP 
is_Public_front = True
tier="1"
NSG_name_root ="NGS-generic-linux-N-tier"
portlist_NSG_FRONT=[22,80,8080,3306]
subnet_level="primary"
IP_RANGE="10.100.1.0/24"
LB_NAME = 'load-balancer-front-end-web'
list_of_port_Load_abalanced_front=[22,80,8080,3306]
#Create VMS HA
fault_domain_count=3
update_domain_count=3
Image_type = 'UbuntuLTS'
Vm_size = 'Standard_DS2_v2'
vmname_var = 'ub-16-tier-%s' %(tier)
#Creation Vms and NIC for Front End Web
user_passwd ='M0nP@ssw0rd!'
user_login = 'demo'
number_of_nic = '1'
extensions ='{"fileUris": ["https://rgcloudmouradgeneralpurp.blob.core.windows.net/exchangecontainermourad/sh_bootstrap_pu.sh"],"commandToExecute": "./sh_bootstrap_pu.sh"}'
is_LB_front = True
is_LB_Front_Public =  True 
Number_Of_Vm_Per_Tier = 2
create_tier (is_Public_front,RGROUP,tier,NSG_name_root,portlist_NSG_FRONT,subnet_level,IP_RANGE,LB_NAME,is_LB_Front_Public,fault_domain_count,update_domain_count,Image_type,Vm_size,user_passwd,user_login,number_of_nic,extensions,is_LB_front,Number_Of_Vm_Per_Tier)
print" **************************************************************************** "
print" ** --------------------------- FIRST TIER DONE --------------------------- * "
print" **************************************************************************** "

#CREATE PUBLIC IP 
is_Public_front = False
tier="2"
NSG_name_root ="NGS-generic-linux-N-tier"
portlist_NSG_FRONT=[22,80,8080,3306]
subnet_level="secondary"
IP_RANGE="10.100.2.0/24"
IP_INTER_NAME="10.100.2.4"
LB_NAME = 'load-balancer-front-to-middle'
list_of_port_Load_abalanced_front=[22,80,8080,3306]
#Create VMS HA
fault_domain_count=3
update_domain_count=3
Image_type = 'UbuntuLTS'
Vm_size = 'Standard_DS2_v2'
vmname_var = 'ub-16-tier-%s' %(tier)
#Creation Vms and NIC for Front End Web
user_passwd ='M0nP@ssw0rd!'
user_login = 'demo'
number_of_nic = '1'
extensions ='{"fileUris": ["https://rgcloudmouradgeneralpurp.blob.core.windows.net/exchangecontainermourad/sh_bootstrap_app.sh"],"commandToExecute": "./sh_bootstrap_app.sh"}'
is_LB_front = True
is_LB_Front_Public =  False 
Number_Of_Vm_Per_Tier = 2
create_tier (is_Public_front,RGROUP,tier,NSG_name_root,portlist_NSG_FRONT,subnet_level,IP_RANGE,LB_NAME,is_LB_Front_Public,fault_domain_count,update_domain_count,Image_type,Vm_size,user_passwd,user_login,number_of_nic,extensions,is_LB_front,Number_Of_Vm_Per_Tier)
print" **************************************************************************** "
print" ** -------------------------- SECOND TIER DONE -------------------------- ** "
print" **************************************************************************** "


#CREATE PUBLIC IP 
is_Public_front = False
tier="3"
NSG_name_root ="NGS-generic-linux-N-tier"
portlist_NSG_FRONT=[22,80,8080,3306]
subnet_level="secondary"
IP_RANGE="10.100.3.0/24"
IP_INTER_NAME="10.100.3.4"
LB_NAME = 'load-balancer-middle-to-data'
list_of_port_Load_abalanced_front=[22,80,8080,3306]
#Create VMS HA
fault_domain_count=3
update_domain_count=3
Image_type = 'UbuntuLTS'
Vm_size = 'Standard_DS2_v2'
vmname_var = 'ub-16-tier-%s' %(tier)
#Creation Vms and NIC for Front End Web
user_passwd ='M0nP@ssw0rd!'
user_login = 'demo'
number_of_nic = '1'
extensions ='{"fileUris": ["https://rgcloudmouradgeneralpurp.blob.core.windows.net/exchangecontainermourad/sh_bootstrap_db.sh"],"commandToExecute": "./sh_bootstrap_db.sh"}'
is_LB_front = True
is_LB_Front_Public =  False 
Number_Of_Vm_Per_Tier = 1
create_tier (is_Public_front,RGROUP,tier,NSG_name_root,portlist_NSG_FRONT,subnet_level,IP_RANGE,LB_NAME,is_LB_Front_Public,fault_domain_count,update_domain_count,Image_type,Vm_size,user_passwd,user_login,number_of_nic,extensions,is_LB_front,Number_Of_Vm_Per_Tier)

print" **************************************************************************** "
print" ** -------------------------- THIRD TIER DONE --------------------------- ** "
print" **************************************************************************** "

