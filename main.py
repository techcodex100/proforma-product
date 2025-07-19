from fastapi import FastAPI, Response
from pydantic import BaseModel
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os
import threading

app = FastAPI()
lock = threading.Lock()
COUNTER_FILE = "counter.txt"

# ✅ Load font
FONT_PATH = os.path.join(os.path.dirname(__file__), "fonts", "arial.ttf")
try:
    FONT = ImageFont.truetype(FONT_PATH, 30)
except Exception as e:
    print("Font loading failed:", e)
    FONT = ImageFont.load_default()

TEMPLATE_PATH = "Your paragraph text.png"  # Set your actual template path here

# ✅ Grid helper (for debugging positions)
def draw_grid(draw, width, height, step=50):
    for x in range(0, width, step):
        draw.line([(x, 0), (x, height)], fill="lightgray", width=1)
        draw.text((x + 2, 2), str(x), font=FONT, fill="gray")
    for y in range(0, height, step):
        draw.line([(0, y), (width, y)], fill="lightgray", width=1)
        draw.text((2, y + 2), str(y), font=FONT, fill="gray")

# ✅ Data model
class InvoiceData(BaseModel):
    Exporter: str
    Invoice_No_and_Date: str
    Exporter_Ref: str
    Buyers_Order_No_and_Date: str
    Consignee: str
    Buyer_If_Other_than_Consignee: str
    Pre_carriage_by: str
    Place_of_Receipt: str
    Country_of_Origin_of_Goods: str
    Country_of_Final_Destination: str
    Vessel_or_Flight_No: str
    Port_of_Loading: str
    Terms_of_Delivery_and_Payment: str
    Port_of_Discharge: str
    Final_Destination: str

    HS_Codes: list[str]
    Marks_and_Nos: list[str]
    Packages: list[str]
    Descriptions: list[str]
    Quantities: list[int]
    Rates: list[float]

    Total_Cartons: str
    Total_Quantity: int
    Net_Weight: str
    Gross_Weight: str
    Variation: str
    Exporter_Bank_Details: str
    Total_Amount_in_Words: str
    Company_Name_Stamp: str
    Authorised_Signature: str

# ✅ Counter logic
def get_next_counter():
    with lock:
        if not os.path.exists(COUNTER_FILE):
            with open(COUNTER_FILE, "w") as f:
                f.write("1")
            return 1
        with open(COUNTER_FILE, "r+") as f:
            content = f.read().strip()
            count = int(content) if content else 1
            f.seek(0)
            f.write(str(count + 1))
            f.truncate()
            return count

# ✅ Draw text
def draw_text(draw, x, y, text):
    draw.text((x, y), str(text), font=FONT, fill="black")

# ✅ Main API
@app.post("/generate-invoice/")
async def generate_invoice(data: InvoiceData):
    try:
        # === Validate item list lengths ===
        if not (
            len(data.HS_Codes) == len(data.Marks_and_Nos) ==
            len(data.Packages) == len(data.Descriptions) ==
            len(data.Quantities) == len(data.Rates)
        ):
            return Response(
                content="Error: All item lists must have the same length.",
                media_type="text/plain",
                status_code=400
            )

        img = Image.open(TEMPLATE_PATH).convert("RGB")
        draw = ImageDraw.Draw(img)

        # ✅ draw_grid(draw, img.width, img.height)  # Debug only

        # === Header Info ===
        draw_text(draw, 100, 375, data.Exporter)
        draw_text(draw, 1350, 375, data.Invoice_No_and_Date)
        draw_text(draw, 1950, 375, data.Exporter_Ref)
        draw_text(draw, 1350, 510, data.Buyers_Order_No_and_Date)
        draw_text(draw, 100, 615, data.Consignee)
        draw_text(draw, 1300, 625, data.Buyer_If_Other_than_Consignee)
        draw_text(draw, 100, 850, data.Pre_carriage_by)
        draw_text(draw, 700, 850, data.Place_of_Receipt)
        draw_text(draw, 1350, 875, data.Country_of_Origin_of_Goods)
        draw_text(draw, 1950, 875, data.Country_of_Final_Destination)
        draw_text(draw, 90, 975, data.Vessel_or_Flight_No)
        draw_text(draw, 700, 975, data.Port_of_Loading)
        draw_text(draw, 1350, 975, data.Terms_of_Delivery_and_Payment)
        draw_text(draw, 90, 1225, data.Port_of_Discharge)
        draw_text(draw, 700, 1225, data.Final_Destination)

        # === Table ===
        table_x = [100, 300, 500, 850, 1275, 1700, 1950, 2200]
        y_start = 1440
        row_height = 55

        row_count = len(data.HS_Codes)
        for i in range(row_count):
            y = y_start + i * row_height
            draw_text(draw, table_x[0], y, str(i + 1))
            draw_text(draw, table_x[1], y, data.HS_Codes[i])
            draw_text(draw, table_x[2], y, data.Marks_and_Nos[i])
            draw_text(draw, table_x[3], y, data.Packages[i])
            draw_text(draw, table_x[4], y, data.Descriptions[i])
            draw_text(draw, table_x[5], y, str(data.Quantities[i]))
            draw_text(draw, table_x[6], y, f"{data.Rates[i]:.2f}")
            draw_text(draw, table_x[7], y, f"{data.Quantities[i] * data.Rates[i]:.2f}")

        # === Footer ===
        draw_text(draw, 520, 1820, data.Total_Cartons)
        draw_text(draw, 1700, 2480, f"{data.Total_Quantity} PCS")
        draw_text(draw, 520, 1870, f"{data.Net_Weight} KGS")
        draw_text(draw, 520, 1930, f"{data.Gross_Weight} KGS")
        draw_text(draw, 520, 1990, data.Variation)
        draw_text(draw, 100, 2100, data.Exporter_Bank_Details)

        total_value = sum(data.Quantities[i] * data.Rates[i] for i in range(row_count))
        draw_text(draw, 2190, 2475, f"{total_value:.2f}")
        draw_text(draw, 350, 2475, data.Total_Amount_in_Words)
        draw_text(draw, 1700, 2600, data.Company_Name_Stamp)
        draw_text(draw, 1750, 2640, data.Authorised_Signature)

        # === Save to PDF ===
        buffer = BytesIO()
        img.save(buffer, format="PDF")
        buffer.seek(0)
        filename = f"invoice_{get_next_counter()}.pdf"

        return Response(content=buffer.read(), media_type="application/pdf", headers={
            "Content-Disposition": f"attachment; filename={filename}"
        })

    except Exception as e:
        return Response(content=f"Error: {str(e)}", media_type="text/plain", status_code=500)