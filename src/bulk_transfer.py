import csv
import bittensor

# Initialize the wallet and subtensor
wallet = bittensor.wallet(name="owner")
print("wallet up")
subtensor = bittensor.subtensor("ws://100.28.51.29:9945")
print("subtensor up")
# Read the CSV file and extract Coldkeys
coldkeys = []
with open("tTAO_requests.csv", mode="r") as file:
    csv_reader = csv.DictReader(file)
    for row in csv_reader:
        print("Coldkey" + row["Coldkey"])
        coldkeys.append(row["Coldkey"])

# Read the funded coldkeys from data/funded_coldkeys.txt
funded_coldkeys = []
try:
    with open("data/funded_coldkeys.txt", mode="r") as funded_file:
        funded_coldkeys = [line.strip() for line in funded_file]
except FileNotFoundError:
    print(
        """data/funded_coldkeys.txt not found.
    Proceeding with an empty list of funded coldkeys."""
    )

# Filter out already funded coldkeys
coldkeys_to_fund = [
    coldkey for coldkey in coldkeys if coldkey not in funded_coldkeys
]

# Transfer 5 TAO to each Coldkey
total_coldkeys = len(coldkeys_to_fund)
for index, coldkey in enumerate(coldkeys_to_fund):
    try:
        subtensor.transfer(wallet=wallet, dest=coldkey, amount=20.0)
        print(f"Transferred 20 TAO to {coldkey}")
        print(f"{total_coldkeys - (index + 1)} coldkeys left")

        # Append the coldkey to data/funded_coldkeys.txt
        try:
            with open("data/funded_coldkeys.txt", mode="a") as funded_file:
                funded_file.write(f"{coldkey}\n")
        except Exception as e:
            print(f"Failed to append {coldkey} to data/funded_coldkeys.txt.")
            print(e)

    except Exception as e:
        print(f"Failed to transfer to {coldkey}: {e}")
