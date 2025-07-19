import time
import requests
import psutil
import os
import pandas as pd
import ast

CSV_FILE = "invoice_data.csv"
SAVE_FOLDER = "generated_invoices"
ENDPOINT = "https://proforma-product.onrender.com/generate-invoice/"  # 🔁 change this

os.makedirs(SAVE_FOLDER, exist_ok=True)

# 🧠 Parse stringified list fields from CSV
def parse_list_fields(row):
    list_fields = [
        "HS_Codes", "Marks_and_Nos", "Packages",
        "Descriptions", "Quantities", "Rates"
    ]
    for field in list_fields:
        try:
            row[field] = ast.literal_eval(row[field])
        except Exception as e:
            print(f"⚠️ Error parsing {field}: {e}")
            row[field] = []
    return row

# 🛠️ Convert certain fields to string
def fix_string_fields(row):
    for key in ["Total_Cartons", "Net_Weight", "Gross_Weight"]:
        row[key] = str(row.get(key, ""))
    return row

def send_requests():
    print("🚀 Auto Invoice PDF Generation Started...\n")
    start = time.time()

    df = pd.read_csv(CSV_FILE)

    for i, row in df.iterrows():
        print(f"📤 Generating Invoice #{i+1}...")
        try:
            row_dict = parse_list_fields(row.to_dict())
            row_dict = fix_string_fields(row_dict)  # ✅ fix types here

            response = requests.post(
                ENDPOINT,
                json=row_dict,
                allow_redirects=True
            )

            if response.status_code == 200 and response.headers.get("content-type") == "application/pdf":
                file_path = os.path.join(SAVE_FOLDER, f"invoice_{i+1}.pdf")
                with open(file_path, "wb") as f:
                    f.write(response.content)
                print(f"✅ Invoice #{i+1} saved to {file_path}")
            else:
                print(f"❌ Failed Invoice #{i+1} - Status: {response.status_code}")
                print(f"📝 Response: {response.text}")

        except Exception as e:
            print(f"💥 Error on Invoice #{i+1}: {e}")

    end = time.time()
    print("\n📊 Performance Report:")
    print(f"⏱️ Time Taken: {round(end - start, 2)} sec")
    print(f"🧠 Memory Used: {psutil.Process().memory_info().rss / 1024 / 1024:.2f} MB")
    print(f"⚙️ CPU Usage: {psutil.cpu_percent(interval=1)}%")

if __name__ == "__main__":
    send_requests()
