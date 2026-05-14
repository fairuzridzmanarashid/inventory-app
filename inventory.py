from flask import Flask, render_template_string, request
import pandas as pd
from datetime import datetime
import os
import shutil

app = Flask(__name__)

FILE_PATH = "Inventory.xlsx"
BACKUP_PATH = "Inventory_backup.xlsx"

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
    df.to_excel(FILE_PATH, index=False)

# -----------------------------
# ✅ CLEAR RECORD (WITH BACKUP)
# -----------------------------
def clear_records():
    # Save backup before deleting
    if os.path.exists(FILE_PATH):
        shutil.copy(FILE_PATH, BACKUP_PATH)

    df = pd.DataFrame(columns=["No", "Name", "ID", "Item", "Date", "Out", "In"])
    df.to_excel(FILE_PATH, index=False)

# -----------------------------
# ✅ UNDO DELETE
# -----------------------------
def undo_delete():
    if os.path.exists(BACKUP_PATH):
        shutil.copy(BACKUP_PATH, FILE_PATH)
        return True
    return False

# -----------------------------
# ✅ MAIN ROUTE
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    message = ""
    df = load_excel()

    if request.method == "POST":

        # 🔴 CLEAR RECORDS
        if "clear" in request.form:
            clear_records()
            df = load_excel()
            message = "🗑️ Records cleared! (You can undo)"

        # 🔄 UNDO DELETE
        elif "undo" in request.form:
            if undo_delete():
                df = load_excel()
                message = "↩️ Undo successful! Records restored"
            else:
                message = "❌ No backup found"

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
                    index_to_update = match.index[0]
                    df.at[index_to_update, "In"] = current_time
                    message = "✅ Item returned (IN recorded)"
                else:
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

        <!-- CLEAR BUTTON -->
        <form method="POST" style="display:inline;">
            <button type="submit" name="clear"
                onclick="return confirm('Delete ALL records?');">
                🗑️ Clear Records
            </button>
        </form>

        <!-- UNDO BUTTON -->
        <form method="POST" style="display:inline;">
            <button type="submit" name="undo">
                ↩️ Undo Delete
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
