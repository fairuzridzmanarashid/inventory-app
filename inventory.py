from flask import Flask, render_template_string, request
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)

FILE_PATH = "Inventory.xlsx"

# -----------------------------
# ✅ CREATE FILE IF NOT EXIST
# -----------------------------
def create_file():
    if not os.path.exists(FILE_PATH):
        df = pd.DataFrame(columns=["No", "Name", "ID", "Item", "Date", "Out", "In"])
        df.to_excel(FILE_PATH, index=False)


# -----------------------------
# ✅ LOAD EXCEL
# -----------------------------
def load_excel():
    create_file()
    df = pd.read_excel(FILE_PATH)
    return df


# -----------------------------
# ✅ SAVE EXCEL
# -----------------------------
def save_excel(df):
    try:
        df.to_excel(FILE_PATH, index=False)
    except PermissionError:
        print("❌ Close Excel file first!")


# -----------------------------
# ✅ MAIN ROUTE
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    message = ""

    df = load_excel()

    if request.method == "POST":
        name = request.form.get("name")
        staff_id = request.form.get("id")
        item = request.form.get("item")

        if name and staff_id and item:
            new_row = {
                "No": len(df) + 1,
                "Name": name,
                "ID": staff_id,
                "Item": item,
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Out": "Yes",
                "In": ""
            }

            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_excel(df)
            message = "✅ Item recorded successfully!"
        else:
            message = "❌ Please fill all fields"

    # Convert table to HTML
    table = df.to_html(index=False)

    # Simple UI (no templates needed)
    return render_template_string("""
    <html>
    <head>
        <title>Inventory App</title>
    </head>
    <body>
        <h1>📦 Inventory System</h1>

        <form method="POST">
            Name: <input type="text" name="name"><br><br>
            ID: <input type="text" name="id"><br><br>
            Item: <input type="text" name="item"><br><br>
            <button type="submit">Submit</button>
        </form>

        <p>{{message}}</p>

        <h2>📋 Records</h2>
        {{table|safe}}
    </body>
    </html>
    """, message=message, table=table)


# -----------------------------
# ✅ RUN APP
# -----------------------------

if __name__ == "__main__":
    app.run()
