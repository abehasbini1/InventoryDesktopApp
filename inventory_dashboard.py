import csv
import os
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk
import mysql.connector
import requests
from dotenv import load_dotenv

# ================= HELPER FUNCTIONS =================


def send_teams_notification(message):
    """Sends a notification to a Microsoft Teams Channel."""
    webhook_url = os.getenv("TEAMS_WEBHOOK_URL")
    if not webhook_url:
        print("DEBUG: Teams Webhook URL missing from .env")
        return

    payload = {"text": message}
    try:
        requests.post(webhook_url, json=payload, timeout=5)
    except Exception as e:
        print(f"DEBUG: Teams notification failed: {e}")


COLOR_PURPLE = "#6E45E3"
NAVY = "#002D62"
GOLD = "#FFC72C"
WHITE = "#F2F2F2"
RED = "#D32D41"


def start_dashboard(container, user_data):
    # DEBUG: See what the FastAPI server sent
    print(f"DEBUG: user_data received: {user_data}")

    # ================= THEME & DB SETUP =================
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    load_dotenv()

    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            port=os.getenv("DB_PORT"),
        )
        # dictionary=True is used to access rows like res["part_id"]
        cursor = conn.cursor(dictionary=True, buffered=True)
    except Exception as e:
        print(f"FULL DEBUG ERROR: {e}")  # This will show in your VS Code terminal
        messagebox.showerror("Database Error", f"Connection failed: {e}")

    # ================= UI LAYOUT (NOTEBOOK) =================
    notebook = ttk.Notebook(container)
    notebook.pack(fill="both", expand=True)

    u_role = user_data.get("role", "No Role")

    # Define which tabs this specific user is allowed to see
    tabs = {}

    # # EVERYONE sees the Request Cart
    # tabs["Request Cart"] = ctk.CTkFrame(notebook)

    # ONLY Admins/Cage see Inventory and Approval tabs
    if u_role.lower() in ["admin", "cage"]:
        tabs["Parts"] = ctk.CTkFrame(notebook)
        tabs["Pending"] = ctk.CTkFrame(notebook)
        tabs["Transactions"] = ctk.CTkFrame(notebook)

    # ONLY Super Admins see the Users tab
    if u_role.lower() == "admin":
        tabs["Users"] = ctk.CTkFrame(notebook)

    for name, frame in tabs.items():
        notebook.add(frame, text=name)
    style = ttk.Style()
    style.theme_use("default")
    style.configure("TNotebook", background="#2b2b2b", borderwidth=0)
    style.configure(
        "TNotebook.Tab",
        background="#D7EDE6",
        fieldbackground="#D7EDE6",
        foreground="#002D62",
        padding=[15, 5],
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", "#FFC72C")],  # Gold when selected
        foreground=[("selected", "#002D62")],
    )

    tabs = {
        "Parts": ctk.CTkFrame(notebook),
        "Users": ctk.CTkFrame(notebook),
        "Transactions": ctk.CTkFrame(notebook),
        "Request Cart": ctk.CTkFrame(notebook),
        "Pending": ctk.CTkFrame(notebook),
    }
    for name, frame in tabs.items():
        notebook.add(frame, text=name)

    def safe_int(v):
        try:
            return int(v)
        except:
            return 0

    # ================= 1. PARTS (INVENTORY) TAB =================
    parts_tab = tabs["Parts"]
    input_frame = ctk.CTkFrame(parts_tab)
    input_frame.pack(fill="x", padx=10, pady=10)

    name_entry = ctk.CTkEntry(input_frame, placeholder_text="Part Name")
    name_entry.grid(row=0, column=0, padx=5)
    desc_entry = ctk.CTkEntry(input_frame, placeholder_text="Description")
    desc_entry.grid(row=0, column=1, padx=5)
    stock_entry = ctk.CTkEntry(
        input_frame, placeholder_text="Stock (Change)", width=100
    )
    stock_entry.grid(row=0, column=2, padx=5)
    area_entry = ctk.CTkEntry(input_frame, placeholder_text="Area", width=100)
    area_entry.grid(row=0, column=3, padx=5)

    tree = ttk.Treeview(
        parts_tab, columns=("ID", "Name", "Desc", "Stock", "Area"), show="headings"
    )
    for c in ("ID", "Name", "Desc", "Stock", "Area"):
        tree.heading(c, text=c)
    tree.pack(fill="both", expand=True, padx=10, pady=5)

    def refresh_parts():
        tree.delete(*tree.get_children())
        cursor.execute(
            "SELECT part_id, part_name, description, `current stock`, area FROM parts"
        )
        for r in cursor.fetchall():
            tree.insert("", "end", values=list(r.values()))

    def export_to_csv():
        file_path = filedialog.asksaveasfilename(defaultextension=".csv")
        if not file_path:
            return
        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Name", "Description", "Stock", "Area"])
            for row in tree.get_children():
                writer.writerow(tree.item(row)["values"])
        messagebox.showinfo("Success", "Export Complete")

    def on_row_double_click(event):
        sel = tree.focus()
        if not sel:
            return
        v = tree.item(sel)["values"]
        if v:
            name_entry.delete(0, "end")
            name_entry.insert(0, v[1])
            desc_entry.delete(0, "end")
            desc_entry.insert(0, v[2])
            stock_entry.delete(0, "end")
            stock_entry.insert(0, v[3])
            area_entry.delete(0, "end")
            area_entry.insert(0, v[4])

    tree.bind("<Double-1>", on_row_double_click)

    def add_part():
        name, desc, amt, area = (
            name_entry.get().strip(),
            desc_entry.get().strip(),
            safe_int(stock_entry.get()),
            area_entry.get().strip(),
        )
        if not name:
            messagebox.showwarning("Input Error", "Part Name is required.")
            return

        cursor.execute(
            "SELECT part_id, `current stock` FROM parts WHERE part_name = %s", (name,)
        )
        res = cursor.fetchone()

        if res:
            p_id = res["part_id"]
            new_stock = res["current stock"] + amt
            cursor.execute(
                "UPDATE parts SET `current stock` = %s, description = %s, area = %s WHERE part_id = %s",
                (new_stock, desc, area, p_id),
            )
        else:
            cursor.execute(
                "INSERT INTO parts (part_name, description, `current stock`, area) VALUES (%s,%s,%s,%s)",
                (name, desc, amt, area),
            )
            p_id = cursor.lastrowid

        # Log Transaction
        cursor.execute(
            "INSERT INTO transaction_history (part_id, quantity_changed) VALUES (%s, %s)",
            (p_id, amt),
        )
        conn.commit()
        send_teams_notification(f"📦 Inventory Update: {name} stock changed by {amt}")
        refresh_parts()
        refresh_tx()
        load_request_parts()
        for e in [name_entry, desc_entry, stock_entry, area_entry]:
            e.delete(0, "end")

    ctk.CTkButton(
        input_frame,
        text="Save/Update",
        fg_color="#002D62",  # Navy
        hover_color="#001F44",  # Darker Navy
        text_color="#F2F2F2",  # White text
        command=add_part,
    ).grid(row=0, column=4, padx=5)
    ctk.CTkButton(
        input_frame,
        text="Export CSV",
        fg_color="#FFC72C",
        hover_color="#E5B327",  # Darker Gold
        text_color="#002D62",
        command=export_to_csv,
    ).grid(row=0, column=5, padx=5)

    # ================= 2. REQUEST CART TAB =================
    req_tab = tabs["Request Cart"]
    u_name = user_data.get("username", "Unknown")
    u_id = user_data.get("id")

    ctk.CTkLabel(
        req_tab, text=f"Active User: {u_name}", font=("Arial", 12, "bold")
    ).pack(pady=5)

    cart = []
    cart_tree = ttk.Treeview(req_tab, columns=("ID", "Part", "Qty"), show="headings")
    for c in ("ID", "Part", "Qty"):
        cart_tree.heading(c, text=c)
    cart_tree.pack(side="right", fill="both", expand=True, padx=10)

    part_combo = ttk.Combobox(req_tab, state="readonly")
    part_combo.pack(pady=5)
    qty_req = ctk.CTkEntry(req_tab, placeholder_text="Qty")
    qty_req.pack(pady=5)

    def load_request_parts():
        cursor.execute("SELECT part_id, part_name FROM parts")
        part_combo["values"] = [
            f"{r['part_id']} - {r['part_name']}" for r in cursor.fetchall()
        ]

    def add_to_cart():
        if part_combo.get() and qty_req.get().isdigit():
            pid, name = part_combo.get().split(" - ")
            cart.append({"part_id": int(pid), "name": name, "qty": int(qty_req.get())})
            cart_tree.insert("", "end", values=(pid, name, qty_req.get()))

    def submit_request():
        if not cart:
            return

        try:
            # 1. Insert the main request record
            cursor.execute(
                "INSERT INTO requests (requested_by, status) VALUES (%s, 'pending')",
                (u_id,),
            )
            rid = cursor.lastrowid

            # 2. Build the "Items" string for the Teams notification
            # We start with the header, then loop through the cart to add bullets
            items_text = ""
            for item in cart:
                # Insert into DB
                cursor.execute(
                    "INSERT INTO request_items (request_id, part_id, quantity) VALUES (%s, %s, %s)",
                    (rid, item["part_id"], item["qty"]),
                )
                # Append to our notification string
                items_text += f"\n• {item['name']} (Qty: {item['qty']})"

            conn.commit()

            # 3. Construct the final payload string
            full_message = (
                f"📋 **New Request Submitted**\n"
                f"**By:** {u_name}\n"
                f"**Request ID:** {rid}\n"
                f"**Items:**{items_text}"
            )

            # 4. Send to Teams
            send_teams_notification(full_message)

            # 5. UI Cleanup
            cart.clear()
            cart_tree.delete(*cart_tree.get_children())
            refresh_pending()
            messagebox.showinfo("Success", f"Request #{rid} Submitted")

        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"Could not submit request: {e}")

    ctk.CTkButton(
        req_tab, text="Add to Cart", fg_color="#00B3B3", command=add_to_cart
    ).pack(pady=5)
    ctk.CTkButton(
        req_tab, text="Submit Request", fg_color="#6E45E3", command=submit_request
    ).pack(pady=5)

    # ================= 3. PENDING TAB =================
    pending_tab = tabs["Pending"]
    pending_tree = ttk.Treeview(
        pending_tab, columns=("RID", "User", "Part", "Qty"), show="headings"
    )
    for c in ("RID", "User", "Part", "Qty"):
        pending_tree.heading(c, text=c)
    pending_tree.pack(fill="both", expand=True, padx=10)

    def refresh_pending():
        pending_tree.delete(*pending_tree.get_children())
        query = """SELECT r.id, u.username, p.part_name, ri.quantity FROM requests r 
                   JOIN request_items ri ON ri.request_id = r.id 
                   JOIN parts p ON p.part_id = ri.part_id 
                   JOIN users u ON u.id = r.requested_by WHERE r.status = 'pending'"""
        cursor.execute(query)
        for r in cursor.fetchall():
            pending_tree.insert("", "end", values=list(r.values()))

    def approve_request():
        sel = pending_tree.selection()
        if not sel:
            return
        rid, user, part_name, qty = pending_tree.item(sel)["values"]
        cursor.execute(
            "SELECT part_id, `current stock` FROM parts WHERE part_name = %s",
            (part_name,),
        )
        p_data = cursor.fetchone()
        new_stock = p_data["current stock"] - int(qty)
        cursor.execute(
            "UPDATE parts SET `current stock` = %s WHERE part_id = %s",
            (new_stock, p_data["part_id"]),
        )
        cursor.execute("UPDATE requests SET status = 'approved' WHERE id = %s", (rid,))
        cursor.execute(
            "INSERT INTO transaction_history (part_id, quantity_changed) VALUES (%s, %s)",
            (p_data["part_id"], -int(qty)),
        )
        conn.commit()
        send_teams_notification(f"✅ Approved Request #{rid} for {user}")
        refresh_pending()
        refresh_parts()
        refresh_tx()

    ctk.CTkButton(
        pending_tab,
        text="Approve & Deduct",
        fg_color="#D32D41",  # Red
        hover_color="#B22637",  # Darker Red
        text_color="#F2F2F2",  # White text
        command=approve_request,
    ).pack(pady=10)

    # ================= 4. USERS TAB =================
    users_tab = tabs["Users"]
    users_tree = ttk.Treeview(
        users_tab, columns=("ID", "Username", "Role"), show="headings"
    )
    for c in ("ID", "Username", "Role"):
        users_tree.heading(c, text=c)
    users_tree.pack(fill="both", expand=True, padx=10)

    def refresh_users():
        users_tree.delete(*users_tree.get_children())
        cursor.execute("""SELECT u.id, u.username, IFNULL(r.description, 'No Role')
                          FROM users u LEFT JOIN user_roles ur ON u.id = ur.user_id
                          LEFT JOIN roles r ON ur.role_id = r.role_id""")
        for row in cursor.fetchall():
            users_tree.insert("", "end", values=list(row.values()))

    ctk.CTkButton(users_tab, text="Refresh Users", command=refresh_users).pack(pady=10)

    # ================= 5. TRANSACTIONS TAB =================
    tx_tab = tabs["Transactions"]
    tx_tree = ttk.Treeview(
        tx_tab, columns=("ID", "Part", "Change", "Date"), show="headings"
    )
    for c in ("ID", "Part", "Change", "Date"):
        tx_tree.heading(c, text=c)
    tx_tree.pack(fill="both", expand=True, padx=10)

    def refresh_tx():
        tx_tree.delete(*tx_tree.get_children())
        cursor.execute("""SELECT t.transaction_id, p.part_name, t.quantity_changed, t.transaction_date 
                          FROM transaction_history t JOIN parts p ON p.part_id = t.part_id 
                          ORDER BY t.transaction_date DESC""")
        for r in cursor.fetchall():
            tx_tree.insert("", "end", values=list(r.values()))

    # INITIAL LOAD
    refresh_parts()
    refresh_pending()
    refresh_users()
    refresh_tx()
    load_request_parts()
