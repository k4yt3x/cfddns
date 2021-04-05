#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: CF DDNS
Author: K4YT3X
Date Created: July 25, 2020
Last Modified: April 5, 2021

Licensed under the GNU General Public License Version 3 (GNU GPL v3),
    available at: https://www.gnu.org/licenses/gpl-3.0.txt
(C) 2020 - 2021 K4YT3X
"""

# built-in import
import argparse
import os
import pathlib
import sys
import time

# third-party import
import CloudFlare
import requests
import tldextract
import yaml

VERSION = '1.0.0'

sys.path.insert(0, os.path.abspath(".."))


def parse_arguments():
    """parse CLI arguments"""
    parser = argparse.ArgumentParser(
        prog="cfddns", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "-d", "--domain", help="domain name to synchronize", required=True
    )

    return parser.parse_args()


def get_external_ip() -> tuple:
    """get external IP address

    Returns:
        tuple: IP address and IP address type
    """

    # url = 'http://myip.dnsomatic.com'
    # url = 'http://www.trackip.net/ip'
    # url = 'http://myexternalip.com/raw'
    # url = "https://api.ipify.org"
    url = "https://ifconfig.co"

    try:
        ip_address = requests.get(
            url, headers={"User-Agent": "curl/7.72.0"}
        ).text.strip()
    except Exception:
        exit("{}: failed".format(url))
    if ip_address == "":
        exit("{}: failed".format(url))

    if ":" in ip_address:
        ip_address_type = "AAAA"
    else:
        ip_address_type = "A"

    return ip_address, ip_address_type


def do_dns_update(cf, zone_name, zone_id, dns_name, ip_address, ip_address_type):
    """Cloudflare API code"""

    try:
        params = {"name": dns_name, "match": "all", "type": ip_address_type}
        dns_records = cf.zones.dns_records.get(zone_id, params=params)
    except CloudFlare.exceptions.CloudFlareAPIError as e:
        exit("/zones/dns_records {} - {} {} - api call failed".format(dns_name, e, e))

    updated = False

    # update the record - unless it's already correct
    for dns_record in dns_records:
        old_ip_address = dns_record["content"]
        old_ip_address_type = dns_record["type"]

        if ip_address_type not in ["A", "AAAA"]:
            # we only deal with A / AAAA records
            continue

        if ip_address_type != old_ip_address_type:
            # only update the correct address type (A or AAAA)
            # we don't see this because of the search params above
            print(
                "IGNORED: {} {} ; wrong address family".format(dns_name, old_ip_address)
            )
            continue

        if ip_address == old_ip_address:
            print("UNCHANGED: {} {}".format(dns_name, ip_address))
            updated = True
            continue

        proxied_state = dns_record["proxied"]

        # Yes, we need to update this record - we know it's the same address type
        dns_record_id = dns_record["id"]
        dns_record = {
            "name": dns_name,
            "type": ip_address_type,
            "content": ip_address,
            "proxied": proxied_state,
        }
        try:
            dns_record = cf.zones.dns_records.put(
                zone_id, dns_record_id, data=dns_record
            )
        except CloudFlare.exceptions.CloudFlareAPIError as e:
            exit(
                "/zones.dns_records.put {} - {} {} - api call failed".format(
                    dns_name, e, e
                )
            )
        print("UPDATED: {} {} -> {}".format(dns_name, old_ip_address, ip_address))
        updated = True

    if updated:
        return

    # no exsiting dns record to update - so create dns record
    dns_record = {"name": dns_name, "type": ip_address_type, "content": ip_address}
    try:
        dns_record = cf.zones.dns_records.post(zone_id, data=dns_record)
    except CloudFlare.exceptions.CloudFlareAPIError as e:
        exit(
            "/zones.dns_records.post {} - {} {} - api call failed".format(
                dns_name, e, e
            )
        )
    print("CREATED: {} {}".format(dns_name, ip_address))


def main():

    args = parse_arguments()

    # try to match a config file by the exact domain name
    config_path = pathlib.Path("/etc/cfddns/{}.yaml".format(args.domain))

    # if the exact domain is not found, find the TLD config
    if not config_path.is_file():
        tld = tldextract.extract(args.domain)
        config_path = pathlib.Path(
            "/etc/cfddns/{}.{}.yaml".format(tld.domain, tld.suffix)
        )

    # if config file is still not found
    if not config_path.is_file():
        raise FileNotFoundError(config_path)

    # read config from config file
    with config_path.open("r") as config_file:
        config = yaml.load(config_file, Loader=yaml.FullLoader)

    # after reading the config, downgrade this process's privileges
    os.setuid(65534)

    # load values from the config file
    token = config["token"]
    frequency = config["frequency"]

    host_name, zone_name = (
        ".".join(args.domain.split(".")[:2]),
        ".".join(args.domain.split(".")[-2:]),
    )

    previous_ip = ""

    while True:
        ip_address, ip_address_type = get_external_ip()
        print("Current IP address: {} {}".format(args.domain, ip_address))

        if ip_address != previous_ip:
            print("Updating IP address")
            previous_ip = ip_address

            # create CloudFlare wrapper instance
            cf = CloudFlare.CloudFlare(token=token)

            # grab the zone identifier
            try:
                params = {"name": zone_name}
                zones = cf.zones.get(params=params)
            except CloudFlare.exceptions.CloudFlareAPIError as e:
                exit("/zones {} {} - api call failed".format(e, e))
            except Exception as e:
                exit("/zones.get - {} - api call failed".format(e))

            if len(zones) == 0:
                exit("/zones.get - {} - zone not found".format(zone_name))

            if len(zones) != 1:
                exit(
                    "/zones.get - {} - api call returned {} items".format(
                        zone_name, len(zones)
                    )
                )

            # update DNS record
            zone = zones[0]
            zone_name = zone["name"]
            zone_id = zone["id"]
            do_dns_update(
                cf, zone_name, zone_id, args.domain, ip_address, ip_address_type
            )

        else:
            print("IP address is the same, skipping update")

        # sleep for [frequency] seconds before the next run
        print("Sleeping for {} seconds".format(frequency))
        time.sleep(frequency)


if __name__ == "__main__":
    main()
