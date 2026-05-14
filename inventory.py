from flask import Flask, render_template_string, request
import pandas as pd
from datetime import datetime
import os
import shutil
import pytz

app = Flask(__name__)

FILE_PATH = "Inventory.xlsx"
BACKUP_PATH = "Inventory_backup.xlsx"

# 🔐 SET YOUR PASSWORD HERE
CLEAR_PASSWORD = "admin123"

# ✅ Duplicate scan control
LAST_SCAN = {"key": None, "time": None}
BLOCK_SECONDS = 5


# -----------------------------
# ✅ CREATE FILE
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
    return pd.read_excel(FILE_PATH).fillna("")


# -----------------------------
# ✅ SAVE EXCEL
# -----------------------------
def save_excel(df):
    df.to_excel(FILE_PATH, index=False)


# -----------------------------
# ✅ CLEAR + BACKUP
# -----------------------------
def clear_records():
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

    template = """
    <html>
    <body>

        <h1>📦 Inventory Scanner</h1>

        <form method="POST">
            Name: <input name="name" required><br><br>
            ID: <input name="id" required><br><br>

            Scan Item:
            <input type="text" name="item" id="barcode" autofocus
                style="width:250px; height:35px;">
            <br><br>

            <button type="submit">Submit</button>
        </form>

        <br>

        <!-- CLEAR with password -->
        <form method="POST" style="display:inline;">
            Password:
            <input type="password" name="clear_password" required>
            <button name="clear">🗑️ Clear</button>
        </form>

        <form method="POST" style="display:inline;">
            <button name="undo">↩️ Undo</button>
        </form>

        <p>{{message}}</p>

        <h3>Records</h3>
        {{table|safe}}

        <script>
            document.getElementById("barcode").focus();
        </script>

    </body>
    </html>
    """

    if request.method == "POST":

        # 🔐 CLEAR WITH PASSWORD
        if "clear" in request.form:
            entered_password = request.form.get("clear_password")

            if entered_password == CLEAR_PASSWORD:
                clear_records()
                df = load_excel()
                message = "🗑️ Records cleared successfully"
            else:
                message = "❌ Wrong password"

        # ↩️ UNDO
        elif "undo" in request.form:
            if undo_delete():
                df = load_excel()
                message = "↩️ Undo successful"
            else:
                message = "❌ No backup found"

        else:
            name = request.form.get("name")
            staff_id = request.form.get("id")
            item = request.form.get("item")

            if name and staff_id and item:

                # ✅ Correct timezone
                tz = pytz.timezone("Asia/Singapore")
                now = datetime.now(tz)

                # ✅ Duplicate check
                scan_key = f"{name}-{staff_id}-{item}"

                if LAST_SCAN["key"] == scan_key:
                    diff = (now - LAST_SCAN["time"]).total_seconds()
                    if diff < BLOCK_SECONDS:
                        return render_template_string(
                            template,
                            message=f"⚠️ Duplicate blocked ({int(diff)}s)",
                            table=df.to_html(index=False)
                        )

                LAST_SCAN["key"] = scan_key
                LAST_SCAN["time"] = now

                current_time = now.strftime("%H:%M:%S")
                current_date = now.strftime("%d/%m/%y")

                match = df[
                    (df["Name"] == name) &
                    (df["ID"].astype(str) == str(staff_id)) &
                    (df["Item"] == item) &
                    (df["In"] == "")
                ]

                if len(match) > 0:
                    idx = match.index[0]
                    df.at[idx, "In"] = current_time
                    message = "✅ IN recorded"
                else:
                    new_row = {
                        "No": len(df) + 1,
                        "Name": name,
                        "ID": str(staff_id),
                        "Item": item,
                        "Date": current_date,
                        "Out": current_time,
                        "In": ""
                    }

                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    message = "✅ OUT recorded"

                save_excel(df)

            else:
                message = "❌ Fill all fields"

    return render_template_string(template, message=message, table=df.to_html(index=False))


# -----------------------------
# ✅ RUN APP
# -----------------------------
if __name__ == "__main__":
    app.run()
