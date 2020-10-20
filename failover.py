import requests, json, time
import meraki
import re

# Meraki credentials are placed below
meraki_config = {
	'api_key': "",
	'org_name': "",
	'tag_placeholder_network': "tag-placeholder",
	'tag_prefix': "vwan-"
}

# Function to authenticate against Meraki SDK with the API key
def get_api_auth():
    meraki_config['api_auth'] = meraki.DashboardAPI(
        meraki_config['api_key']
        )

# Function to obtain organization ID
def get_org_id():
    # obtaining all orgs with corresponding API key
    result_org_id = meraki_config['api_auth'].organizations.getOrganizations()
    # iterating through list of orgs to match specified org_name
    for orgs in result_org_id:
        if orgs['name'] == meraki_config['org_name']:
            meraki_config['org_id'] = orgs['id']

# function to obtain a list of all vpn stats for a network
def get_vpn_stats(list_of_networks):

    get_vpn_stats.response = meraki_config['api_auth'].appliance.getOrganizationApplianceVpnStatuses(
        meraki_config['org_id'], total_pages='all', networkIds=list_of_networks
    )

# this function iterates through a list of networks obtained via an org wide call
def get_meraki_networks_by_tag():

    # creating a list of network IDs with specified tag
    get_meraki_networks_by_tag.list_of_network_ids = []

    # obtaining complete list of networks within org
    meraki_network_list = meraki_config['api_auth'].organizations.getOrganizationNetworks(
        meraki_config['org_id']
        )

    # looping through list of networks with anything matching a specific tag
    for network in meraki_network_list:
        # filtering for networks tagged with vWAN- and skipping over network Tag-Placeholder
        if network['tags'] and network['name'] != 'Tag-Placeholder' and \
            str(meraki_config['tag_prefix']) in str(network['tags']):
                # appending network ID to list
                get_meraki_networks_by_tag.list_of_network_ids.append(str(network['id'])) 
    
    print(get_meraki_networks_by_tag.list_of_network_ids)

# this function swaps the network tag if the vpn peer is detected as down
def swap_tag(network_id):

    # Performing GET to obtain all networks w/ tags in organization
    meraki_network_info = meraki_config['api_auth'].organizations.getOrganizationNetworks(
    meraki_config['org_id'], tagsFilterType = 'withAnyTags'
    )

    # iterating through networks to match our network ID
    for meraki_networks in meraki_network_info:
        if meraki_networks['id'] == str(network_id):
            network_tags = meraki_networks['tags']
            print(network_tags)

            # regex to match the tags for primary and secondary tunnel availability tags
            primary_tag_regex = f"(?i)^{meraki_config['tag_prefix']}([a-zA-Z0-9_-]+)-[0-9]+$"
            secondary_tag_regex = f"(?i)^{meraki_config['tag_prefix']}([a-zA-Z0-9_-]+)-[0-9]+-sec$"

            # Get specific vwan tag from the list
            for tag in range(0, len(network_tags)):
                if re.match(primary_tag_regex, network_tags[tag]):
                    # creating new tag to append to the list
                    specific_tag = str(network_tags[tag]) + "-sec"
                    network_tags[tag] = specific_tag
                elif re.match(secondary_tag_regex, network_tags[tag]):
                    # removing -sec from the tag value
                    specific_tag = str(network_tags[tag])[-4]
                    network_tags[tag] = specific_tag

            print(network_tags)

            # updating Meraki networks with new tag list network_tags

            update_net = meraki_config['api_auth'].networks.updateNetwork(
                network_id, 
                tags=network_tags
            )

            print(update_net)


# Obtaining auth to the Meraki SDK (returning variable to later call when using SDK)
get_api_auth()

# executing function to obtain Organization ID
get_org_id()

# executing function to obtain list of networks by tag
get_meraki_networks_by_tag()

# executing function to get a complete list of VPN stats
get_vpn_stats(get_meraki_networks_by_tag.list_of_network_ids)

# filtering out all NoneType elements from list so we can iterate through
new_list = [x for x in get_vpn_stats.response if x != None]

# iterating through list of vpn stats obtained via get_vpn_stats function
for networks in new_list:
    if networks['thirdPartyVpnPeers'][0]['reachability'] == 'unreachable':
        print("VPN peer detected as unreachable, swapping tags")

        # executing function to swap tags for the network
        swap_tag(networks['networkId'])

        time.sleep(5)
        
