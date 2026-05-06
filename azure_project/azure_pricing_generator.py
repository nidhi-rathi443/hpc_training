
import argparse

import sys

import time

from collections import defaultdict
 
import h5py

import numpy as np

import requests
 
def fetch_azure_pricing():

    print("\n[1/4] Fetching Azure VM pricing from public API...")

    print("      (This may take 2-3 minutes due to pagination)\n")

    base_url = "https://prices.azure.com/api/retail/prices"

    params = {

        "$filter": (

            "serviceName eq 'Virtual Machines' "

            "and priceType eq 'Consumption' "

            "and currencyCode eq 'USD'"

        )

    }

    all_items = []

    page = 1

    url = base_url

    while url:

        print(f"      Fetching page {page}...", end="\r")

        try:

            response = requests.get(url, params=params, timeout=30)

            response.raise_for_status()

            data = response.json()

        except requests.exceptions.RequestException as e:

            print(f"\n[ERROR] Failed to fetch pricing data: {e}")

            sys.exit(1)

        items = data.get("Items", [])

        all_items.extend(items)

        url = data.get("NextPageLink")

        params = {}

        page += 1

        time.sleep(0.1)

    print(f"\n      Done! Fetched {len(all_items):,} total pricing records")

    return all_items
 
def filter_linux_ondemand(all_items):

    print("\n[2/4] Filtering to Linux on-demand prices only...")

    filtered = []

    for item in all_items:

        sku_name = item.get("skuName", "")

        region   = item.get("armRegionName", "")

        arm_sku  = item.get("armSkuName", "")

        price    = item.get("retailPrice", 0)

        if "Windows" in sku_name:

            continue

        if "Spot" in sku_name:

            continue

        if "Low Priority" in sku_name:

            continue

        if not region or not arm_sku:

            continue

        if price <= 0:

            continue

        filtered.append({"instance": arm_sku, "price": price, "region": region})

    print(f"      Done! {len(filtered):,} records after filtering")

    return filtered
 
FALLBACK_SKU_MAP = {

    "Standard_D2s_v3":  {"vCPUs": 2,  "memoryGB": 8.0},

    "Standard_D4s_v3":  {"vCPUs": 4,  "memoryGB": 16.0},

    "Standard_D8s_v3":  {"vCPUs": 8,  "memoryGB": 32.0},

    "Standard_D16s_v3": {"vCPUs": 16, "memoryGB": 64.0},

    "Standard_D32s_v3": {"vCPUs": 32, "memoryGB": 128.0},

    "Standard_D2_v3":   {"vCPUs": 2,  "memoryGB": 8.0},

    "Standard_D4_v3":   {"vCPUs": 4,  "memoryGB": 16.0},

    "Standard_D8_v3":   {"vCPUs": 8,  "memoryGB": 32.0},

    "Standard_D2s_v4":  {"vCPUs": 2,  "memoryGB": 8.0},

    "Standard_D4s_v4":  {"vCPUs": 4,  "memoryGB": 16.0},

    "Standard_D8s_v4":  {"vCPUs": 8,  "memoryGB": 32.0},

    "Standard_D2s_v5":  {"vCPUs": 2,  "memoryGB": 8.0},

    "Standard_D4s_v5":  {"vCPUs": 4,  "memoryGB": 16.0},

    "Standard_D8s_v5":  {"vCPUs": 8,  "memoryGB": 32.0},

    "Standard_D16s_v5": {"vCPUs": 16, "memoryGB": 64.0},

    "Standard_F2s_v2":  {"vCPUs": 2,  "memoryGB": 4.0},

    "Standard_F4s_v2":  {"vCPUs": 4,  "memoryGB": 8.0},

    "Standard_F8s_v2":  {"vCPUs": 8,  "memoryGB": 16.0},

    "Standard_F16s_v2": {"vCPUs": 16, "memoryGB": 32.0},

    "Standard_F32s_v2": {"vCPUs": 32, "memoryGB": 64.0},

    "Standard_E2s_v3":  {"vCPUs": 2,  "memoryGB": 16.0},

    "Standard_E4s_v3":  {"vCPUs": 4,  "memoryGB": 32.0},

    "Standard_E8s_v3":  {"vCPUs": 8,  "memoryGB": 64.0},

    "Standard_E16s_v3": {"vCPUs": 16, "memoryGB": 128.0},

    "Standard_E32s_v3": {"vCPUs": 32, "memoryGB": 256.0},

    "Standard_E2s_v5":  {"vCPUs": 2,  "memoryGB": 16.0},

    "Standard_E4s_v5":  {"vCPUs": 4,  "memoryGB": 32.0},

    "Standard_E8s_v5":  {"vCPUs": 8,  "memoryGB": 64.0},

    "Standard_L8s_v3":  {"vCPUs": 8,  "memoryGB": 64.0},

    "Standard_L16s_v3": {"vCPUs": 16, "memoryGB": 128.0},

    "Standard_L32s_v3": {"vCPUs": 32, "memoryGB": 256.0},

    "Standard_NC6":     {"vCPUs": 6,  "memoryGB": 56.0},

    "Standard_NC12":    {"vCPUs": 12, "memoryGB": 112.0},

    "Standard_NC24":    {"vCPUs": 24, "memoryGB": 224.0},

    "Standard_B1s":     {"vCPUs": 1,  "memoryGB": 1.0},

    "Standard_B2s":     {"vCPUs": 2,  "memoryGB": 4.0},

    "Standard_B4ms":    {"vCPUs": 4,  "memoryGB": 16.0},

    "Standard_B8ms":    {"vCPUs": 8,  "memoryGB": 32.0},

}
 
def build_region_data(filtered_items, sku_map):

    print("\n[3/4] Organizing data by region...")

    region_data = defaultdict(list)

    for item in filtered_items:

        sku    = item["instance"]

        price  = item["price"]

        region = item["region"]

        specs  = sku_map.get(sku, {})

        region_data[region].append({

            "instance": sku,

            "price":    price,

            "memory":   specs.get("memoryGB", 0.0),

            "vcpu":     specs.get("vCPUs", 0),

        })

    print(f"      Done! {len(region_data):,} regions found")

    return region_data
 
def write_hdf5(region_data, output_file="azure_pricing.h5"):

    print(f"\n[4/4] Writing HDF5 file: {output_file}")

    with h5py.File(output_file, "w") as f:

        azure_group = f.create_group("Azure")

        for region, instances in sorted(region_data.items()):

            if not instances:

                continue

            rg = azure_group.create_group(region)

            rg.create_dataset("Instance",         data=np.array([i["instance"] for i in instances], dtype=h5py.string_dtype()))

            rg.create_dataset("Instance Pricing", data=np.array([i["price"]    for i in instances], dtype=np.float64))

            rg.create_dataset("Memory",           data=np.array([i["memory"]   for i in instances], dtype=np.float64))

            rg.create_dataset("vCPU",             data=np.array([i["vcpu"]     for i in instances], dtype=np.int32))

    print(f"      HDF5 file written successfully!")

    print(f"\n{'='*55}")

    print(f"  Output file : {output_file}")

    print(f"  Regions     : {len(region_data)}")

    print(f"  Total VMs   : {sum(len(v) for v in region_data.values()):,}")

    print(f"{'='*55}")

    print(f"\n  View at: https://myhdf5.hdfgroup.org\n")
 
def main():

    print("=" * 55)

    print("  Azure VM Pricing -> HDF5 Generator")

    print("  Team: Nidhi & Kaveri Pandappa Kallennavar")

    print("=" * 55)

    all_items   = fetch_azure_pricing()

    filtered    = filter_linux_ondemand(all_items)

    sku_map     = FALLBACK_SKU_MAP

    print("\n[3/4] Using built-in VM specs table...")

    region_data = build_region_data(filtered, sku_map)

    write_hdf5(region_data, output_file=os.path.expanduser("~/azure_project/azure_pricing.h5"))
 
import os

if __name__ == "__main__":

    main()

