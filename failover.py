import requests, json, time
import meraki
import re
import datetime as dt
from datetime import datetime, timedelta

# Meraki credentials are placed below
meraki_config = {
	'api_key': "",
	'org_name': ""
}

# this function obtains the org ID by inputting org name and API key
mdashboard = meraki.DashboardAPI(meraki_config['api_key'])
result_org_id = mdashboard.organizations.getOrganizations()
for x in result_org_id:
    if x['name'] == meraki_config['org_name']:
        meraki_config['org_id'] = x['id']

# this function performs an org wide Meraki call for all sites VPN statuses
# not using the SDK for this call as it is currently unavailable for now..
def org_wide_vpn_status(list_of_meraki_ids):
    # defining the URL for the GET below
    org_vpn_url = 'https://api.meraki.com/api/v1/organizations/'\
        +meraki_config['org_id']+'/appliance/vpn/statuses?networkIds[]='\
            +str(list_of_meraki_ids[0]) # this is not the correct way to do this, but leaving for now
    # creating the header in order to authenticate the call
    header = {"X-Cisco-Meraki-API-Key": meraki_config['api_key'], "Content-Type": "application/json"}
    # performing API call to meraki dashboard
    vpn_statuses = requests.get(org_vpn_url, headers=header).content
    print(vpn_statuses)

# this function iterates through a list of networks obtained via an org wide call
def get_meraki_networks_by_tag():
    # creating a list of network IDs with specified tag
    get_meraki_networks_by_tag.list_of_network_ids = []
    # obtaining complete list of networks within org
    meraki_network_list = mdashboard.networks.getOrganizationNetworks(meraki_config['org_id'])
    # looping through list of networks with anything matching a specific tag
    for network in meraki_network_list:
        # filtering for networks tagged with vWAN- and skipping over network Tag-Placeholder
        if network['tags'] and network['name'] != 'Tag-Placeholder' and "vWAN-" in network['tags']:
            # obtaining network ID to later append to the list of network ids
            network_id = network['id']
            get_meraki_networks_by_tag.list_of_network_ids.append(network_id) # appending network ID to list

# this function swaps network tags if a failover is detected
def swap_network_tag(network_id):
    # API call to obtain current tag on network
    current_network_info = mdashboard.networks.getNetwork(network_id)
    current_network_tag = current_network_info['tags'] # parsing network info for tags
    print(current_network_tag)

# end of function list

get_meraki_networks_by_tag()
# below is the list of network IDs that are built with the get_meraki_networks_by_tag() function
print(get_meraki_networks_by_tag.list_of_network_ids)

org_wide_vpn_status(get_meraki_networks_by_tag.list_of_network_ids)
swap_network_tag(get_meraki_networks_by_tag.list_of_network_ids[0])
