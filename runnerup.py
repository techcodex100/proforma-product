from faker import Faker
import requests
import random
import time
import psutil
import os

fake = Faker()
url = "https://proforma-product.onrender.com/generate-invoice/"

# Create folder if not exists
output_folder = "invoices"
os.makedirs(output_folder, exist_ok=True)

def generate_fake_invoice_data():
    row_count = random.randint(3, 6)
    return {
        "Exporter": fake.company(),
        "Invoice_No_and_Date": f"{fake.bothify(text='INV-#####')}, {fake.date()}",
        "Exporter_Ref": fake.bothify(text="REF-####"),
        "Buyers_Order_No_and_Date": f"{fake.bothify(text='ORD-#####')}, {fake.date()}",
        "Consignee": fake.name(),
        "Buyer_If_Other_than_Consignee": fake.name(),
        "Pre_carriage_by": fake.word(),
        "Place_of_Receipt": fake.city(),
        "Country_of_Origin_of_Goods": fake.country(),
        "Country_of_Final_Destination": fake.country(),
        "Vessel_or_Flight_No": fake.bothify(text="VES###"),
        "Port_of_Loading": fake.city(),
        "Terms_of_Delivery_and_Payment": "FOB",
        "Port_of_Discharge": fake.city(),
        "Final_Destination": fake.city(),

        "HS_Codes": [fake.bothify(text="####.##") for _ in range(row_count)],
        "Marks_and_Nos": [fake.bothify(text="PKG##") for _ in range(row_count)],
        "Packages": [fake.word() for _ in range(row_count)],
        "Descriptions": [fake.catch_phrase() for _ in range(row_count)],
        "Quantities": [random.randint(1, 100) for _ in range(row_count)],
        "Rates": [round(random.uniform(10.0, 200.0), 2) for _ in range(row_count)],

        "Total_Cartons": str(random.randint(10, 50)),
        "Total_Quantity": random.randint(100, 500),
        "Net_Weight": str(round(random.uniform(100.0, 500.0), 2)),
        "Gross_Weight": str(round(random.uniform(150.0, 600.0), 2)),
        "Variation": fake.sentence(nb_words=4),
        "Exporter_Bank_Details": fake.text(max_nb_chars=100),
        "Total_Amount_in_Words": fake.sentence(nb_words=8),
        "Company_Name_Stamp": fake.company(),
        "Authorised_Signature": fake.name()
    }

# === Monitor Start ===
start_time = time.time()
process = psutil.Process(os.getpid())

print("🚀 Generating 50 Invoices using Faker...")

for i in range(50):
    payload = generate_fake_invoice_data()
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            filepath = os.path.join(output_folder, f"invoice_{i+1}.pdf")
            with open(filepath, "wb") as f:
                f.write(response.content)
            print(f"✅ Saved: {filepath}")
        else:
            print(f"❌ Failed at invoice {i+1} - Status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Exception at invoice {i+1}: {e}")

# === Monitor End ===
end_time = time.time()
total_time = round(end_time - start_time, 2)
memory_used = process.memory_info().rss / (1024 * 1024)
cpu_usage = psutil.cpu_percent(interval=1)

print("\n📊 Process Report:")
print(f"🕒 Time Taken       : {total_time} seconds")
print(f"🧠 Memory Used      : {memory_used:.2f} MB")
print(f"⚙️  CPU Utilization : {cpu_usage}%")
