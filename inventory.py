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
    return pd.read_excel(FILE_PATH)

# -----------------------------
# ✅ SAVE EXCEL
# -----------------------------
def save_excel(df):
    try:
        df.to_excel(FILE_PATH, index=False)
    except PermissionError:
        print("Close Excel file first!")

# -----------------------------
# ✅ CLEAR RECORD
# -----------------------------
def clear_records():
    df = pd.DataFrame(columns=["No", "Name", "ID", "Item", "Date", "Out", "In"])
    df.to_excel(FILE_PATH, index=False)

# -----------------------------
# ✅ MAIN ROUTE
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    message = ""
    df = load_excel()

    if request.method == "POST":

        # 🔴 CLEAR BUTTON
        if "clear" in request.form:
            clear_records()
            df = load_excel()
            message = "🗑️ All records cleared!"

        else:
            name = request.form.get("name")
            staff_id = request.form.get("id")
            item = request.form.get("item")

            current_time = datetime.now().strftime("%H:%M:%S")
            current_date = datetime.now().strftime("%d/%m/%y")

            if name and staff_id and item:

                match = df[
                    (df["Name"] == name) &
                    (df["ID"] == staff_id) &
                    (df["Item"] == item) &
                    (df["In"].isna() | (df["In"] == ""))
                ]

                if not match.empty:
                    # ✅ SECOND SCAN → IN
                    index_to_update = match.index[0]
                    df.at[index_to_update, "In"] = current_time
                    message = "✅ Item returned (IN recorded)"
                else:
                    # ✅ FIRST SCAN → OUT
                    new_row = {
                        "No": len(df) + 1,
                        "Name": name,
                        "ID": staff_id,
                        "Item": item,
                        "Date": current_date,
                        "Out": current_time,
                        "In": ""
                    }

                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    message = "✅ Item checked OUT"

                save_excel(df)
            else:
                message = "❌ Please fill all fields"

    table = df.to_html(index=False)

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

            <button type="submit">Scan</button>
        </form>

        <br>

        <!-- 🔴 CLEAR BUTTON -->
        <form method="POST">
            <button type="submit" name="clear"
                onclick="return confirm('Are you sure you want to delete ALL records?');">
                🗑️ Clear All Records
            </button>
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
