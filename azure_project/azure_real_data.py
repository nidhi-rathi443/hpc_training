import requests
import h5py
import numpy as np

# -----------------------------
# YOUR CREDENTIALS
# -----------------------------
TENANT_ID = os.getenv("AZURE_TENANT_ID")
CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID")


# -----------------------------
# AUTH TOKEN
# -----------------------------
def get_access_token():
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/token"

    payload = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "resource": "https://management.azure.com/"
    }

    res = requests.post(url, data=payload)

    if res.status_code != 200:
        print("❌ Token error")
        print(res.text)
        exit()

    print("✅ Token acquired")

    return res.json()["access_token"]

# -----------------------------
# GET REGIONS
# ----------------------------
def get_regions(token):
    url = f"https://management.azure.com/subscriptions/{SUBSCRIPTION_ID}/locations?api-version=2021-04-01"

    headers = {"Authorization": f"Bearer {token}"}

    res = requests.get(url, headers=headers)

    if res.status_code != 200:
        print("❌ Failed to fetch regions")
        print(res.text)
        return []

    data = res.json()

    regions = [r["name"] for r in data.get("value", [])]

    print(f"✅ Regions fetched: {len(regions)}")

    return regions




# ----------------------------
# GET VM INSTANCES
# -----------------------------
def get_vms(token):
    url = f"https://management.azure.com/subscriptions/{SUBSCRIPTION_ID}/providers/Microsoft.Compute/virtualMachines?api-version=2023-03-01"

    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(url, headers=headers).json()

    vms = []

    for vm in res.get("value", []):
        vms.append({
            "name": vm["name"],
            "size": vm["properties"]["hardwareProfile"]["vmSize"],
            "region": vm["location"]
        })

    return vms

# GET ALL VM SIZES
def get_all_vm_sizes(token, region):
    url = f"https://management.azure.com/subscriptions/{SUBSCRIPTION_ID}/providers/Microsoft.Compute/locations/{region}/vmSizes?api-version=2023-03-01"

    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(url, headers=headers)

    if res.status_code != 200:
        print(f"❌ Failed for region: {region}")
        print(res.text)
        return []

    data = res.json()

    instances = []

    for vm in data.get("value", []):
        instances.append({
            "name": vm["name"],
            "vCPU": vm["numberOfCores"],
            "Memory": vm["memoryInMB"] / 1024
        })

    return instances

# --------------------------
# Pricing
# --------------------------
import time

def get_region_pricing(region):
    print(f"Fetching pricing for region: {region}")

    url = (
        "https://prices.azure.com/api/retail/prices"
        f"?$filter=serviceName eq 'Virtual Machines'"
        f" and armRegionName eq '{region}'"
        f" and priceType eq 'Consumption'"
    )

    pricing_map = {}

    while url:
        try:
            res = requests.get(url, timeout=10)

            if res.status_code != 200:
                print(f"❌ Pricing failed for {region}")
                return pricing_map

            data = res.json()

            for item in data.get("Items", []):
                if "Windows" in item.get("productName", ""):
                    continue

                sku = item.get("armSkuName")
                price = item.get("retailPrice")

                if sku and sku not in pricing_map:
                    pricing_map[sku] = price

            url = data.get("NextPageLink")

        except Exception as e:
            print(f"⚠️ Retry pricing for {region}")
            time.sleep(2)

    return pricing_map


# -----------------------------
# GET VM SIZE (CPU + MEMORY)
# -----------------------------
def get_all_vm_sizes(token, region):
    url = f"https://management.azure.com/subscriptions/{SUBSCRIPTION_ID}/providers/Microsoft.Compute/locations/{region}/vmSizes?api-version=2023-03-01"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        res = requests.get(url, headers=headers)

        if res.status_code != 200:
            print(f"⚠️ Skipping unsupported region: {region}")
            return None

        data = res.json()

        vm_list = []

        for vm in data.get("value", []):
            vm_list.append({
                "name": vm["name"],
                "vCPU": vm["numberOfCores"],
                "Memory": vm["memoryInMB"] / 1024
            })

        return vm_list

    except Exception as e:
        print(f"❌ Error fetching VM sizes for {region}: {e}")
        return None



# -----------------------------
# SAVE TO HDF5
# ----------------------------
import h5py
import numpy as np

def save_hdf5(region_data):
    with h5py.File("azure_real_data.h5", "w") as f:
        azure_grp = f.create_group("Azure")

        for region, data in region_data.items():
            reg_grp = azure_grp.create_group(region)

            reg_grp.create_dataset(
                "Instance",
                data=np.array(data["Instance"], dtype='S')
            )
            reg_grp.create_dataset(
                "Memory",
                data=data["Memory"]
            )
            reg_grp.create_dataset(
                "vCPU",
                data=data["vCPU"]
            )
            reg_grp.create_dataset(
                "Pricing",
                data=data["Pricing"]
            )
            reg_grp.create_dataset(
                "Region",
                data=np.array(data["Region"], dtype='S')
            )

    print("✅ Saved: azure_real_data.h5")

import csv

def save_csv(region_data):
    with open("azure_output.csv", "w", newline="") as f:
        writer = csv.writer(f)

        writer.writerow(["Region", "Instance", "vCPU", "Memory(GB)", "Price"])

        for region, data in region_data.items():
            for i in range(len(data["Instance"])):
                writer.writerow([
                    region,
                    data["Instance"][i],
                    data["vCPU"][i],
                    data["Memory"][i],
                    data["Pricing"][i]
                ])

    print("✅ CSV saved: azure_output.csv")


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    token = get_access_token()

    regions = get_regions(token)
    #regions = regions[:3]   # limit for testing

    print(f"\nTotal regions: {len(regions)}")

    all_data = {}

    for region in regions:
        print(f"\n========== REGION: {region} ==========\n")

        vm_list = get_all_vm_sizes(token, region)

        if not vm_list:
            continue

        pricing_map = get_region_pricing(region)

        all_data[region] = {
            "Instance": [],
            "Memory": [],
            "vCPU": [],
            "Pricing": [],
            "Region": []
        }

        for vm in vm_list:
            name = vm["name"]
            price = pricing_map.get(name, 0)

            all_data[region]["Instance"].append(name)
            all_data[region]["Memory"].append(vm["Memory"])
            all_data[region]["vCPU"].append(vm["vCPU"])
            all_data[region]["Pricing"].append(price)
            all_data[region]["Region"].append(region)

            print(f"""
Instance : {name}
Region   : {region}
vCPU     : {vm['vCPU']}
Memory   : {vm['Memory']} GB
Price    : {price}
---------------------------
""")

    save_hdf5(all_data)
    save_csv(all_data)
