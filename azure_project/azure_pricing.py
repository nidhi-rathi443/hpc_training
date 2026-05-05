import requests
import h5py
import numpy as np
import time
import re

# -----------------------------
# SAFE REQUEST (retry + timeout)
# -----------------------------
def safe_request(url, retries=3):
    for i in range(retries):
        try:
            response = requests.get(url, timeout=10)
            return response.json()
        except Exception as e:
            print(f"⚠️ Retry {i+1}/{retries} failed: {e}")
            time.sleep(2)

    print("❌ Failed after retries")
    return None


# -----------------------------
# FETCH AZURE PRICING (LIMITED)
# -----------------------------
def fetch_pricing(region):
    print(f"\nFetching pricing for region: {region}")

    url = f"https://prices.azure.com/api/retail/prices?$filter=serviceName eq 'Virtual Machines' and armRegionName eq '{region}' and priceType eq 'Consumption'"

    all_data = []
    page_count = 0

    while url:
        res = safe_request(url)

        if res is None:
            break

        all_data.extend(res["Items"])
        url = res.get("NextPageLink")

        page_count += 1
        print(f"Fetched page {page_count}")

        # safety limit (avoid huge downloads)
        if page_count >= 20:
            break

    print(f"Total records fetched: {len(all_data)}")
    return all_data


# -----------------------------
# FETCH VM SPECS (PUBLIC)
# -----------------------------
import re

def extract_specs_from_sku(sku):
    """
    Extract vCPU and Memory from Azure SKU
    Example: Standard_D2s_v3 → vCPU=2, Memory≈8GB
    """

    if not sku:
        return 0, 0

    # Remove prefix
    sku = sku.replace("Standard_", "")

    # Match patterns like D2s_v3, D4s_v3, F8, etc.
    match = re.match(r"[A-Za-z]+(\d+)", sku)

    if not match:
        return 0, 0

    vcpu = int(match.group(1))

    # Better approximation by series
    if sku.startswith("D"):
        memory = vcpu * 4
    elif sku.startswith("E"):
        memory = vcpu * 8
    elif sku.startswith("F"):
        memory = vcpu * 2
    else:
        memory = vcpu * 4  # default fallback

    return vcpu, memory


def fetch_vm_specs():
    print("Using dynamic SKU-based spec extraction (no external API)...")
    return {}


# -----------------------------
# PROCESS DATA
# -----------------------------
def process_data(pricing_data, spec_map):
    result = {
        "Instance": [],
        "Instance_Pricing": [],
        "Memory": [],
        "vCPU": []
    }

    seen = set()

    for item in pricing_data:
        if "Linux" not in item.get("productName", ""):
            continue

        instance = item.get("armSkuName")
        price = item.get("retailPrice")

        if not instance or "Standard_" not in instance:
            continue

        if instance not in seen:
            seen.add(instance)

            vcpu, memory = extract_specs_from_sku(instance)

            result["Instance"].append(instance)
            result["Instance_Pricing"].append(price)
            result["Memory"].append(memory)
            result["vCPU"].append(vcpu)

    return result


# -----------------------------
# PRINT OUTPUT
# -----------------------------
def print_data(region, data):
    print(f"\n========== REGION: {region} ==========\n")

    for i in range(len(data["Instance"])):
        print(f"""
Instance   : {data['Instance'][i]}
Price/hr   : {data['Instance_Pricing'][i]}
Memory     : {data['Memory'][i]} GB
vCPU       : {data['vCPU'][i]}
---------------------------------------
""")


# -----------------------------
# SAVE TO HDF5
# -----------------------------
def save_hdf5(region_data):
    with h5py.File("azure_pricing.h5", "w") as f:
        azure_grp = f.create_group("Azure")

        for region, data in region_data.items():
            reg_grp = azure_grp.create_group(region)

            reg_grp.create_dataset(
                "Instance",
                data=np.array(data["Instance"], dtype='S')
            )
            reg_grp.create_dataset(
                "Instance_Pricing",
                data=data["Instance_Pricing"]
            )
            reg_grp.create_dataset(
                "Memory",
                data=data["Memory"]
            )
            reg_grp.create_dataset(
                "vCPU",
                data=data["vCPU"]
            )

    print("\n✅ File saved: azure_pricing.h5")


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    # Choose limited regions (SAFE)
    regions = ["eastus", "centralindia"]

    spec_map = fetch_vm_specs()

    all_region_data = {}

    for region in regions:
        pricing_data = fetch_pricing(region)

        if not pricing_data:
            print(f"⚠️ No data for {region}")
            continue

        processed = process_data(pricing_data, spec_map)

        if len(processed["Instance"]) == 0:
            print(f"⚠️ No valid instances for {region}")
            continue

        print_data(region, processed)
        all_region_data[region] = processed

    save_hdf5(all_region_data)
