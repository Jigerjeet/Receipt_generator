import tkinter as tk
from tkinter import ttk, messagebox, font
import tempfile
import os, sys
import pandas as pd
import logging
from datetime import datetime
import json, hashlib, uuid, time, base64


# ---- SQLAlchemy ORM ----
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session

# =========================
# Logging
# =========================
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# =========================
# Utility: resource path (PyInstaller-safe)
# =========================
def resource_path(relative_path: str) -> str:
    try:
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except Exception:
        base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    return os.path.join(base_path, relative_path)



from tkinter import filedialog
from tkinter import messagebox
from datetime import datetime, timedelta
from datetime import datetime, timedelta

RECENT_DAYS = 30  # change this to 7/90/etc to control what "recent" means

def open_reports_window():
    # ---------- Window ----------
    win = tk.Toplevel(root)
    win.title("CourierX Reports (Recent)")
    win.geometry("1100x650")
    win.configure(bg="#FAFAFA")
    win.transient(root)
    win.grab_set()

    # ---------- Header / Controls ----------
    top = tk.Frame(win, bg="#FAFAFA")
    top.pack(fill="x", padx=12, pady=8)

    info_lbl = ttk.Label(
        top,
        text=f"Showing records from the last {RECENT_DAYS} day(s), newest first.",
        font=("Helvetica", 11)
    )
    info_lbl.pack(side="left")

    btn_refresh = ttk.Button(top, text="🔄 Refresh")
    btn_refresh.pack(side="right", padx=4)

    # ---------- Table ----------
    cols = [
        "id","created_at","receipt_no","token_no","price","weight",
        "sender_name","sender_phone",
        "receiver_name","receiver_phone",
        "city","state","receiver_pincode"
    ]
    col_headers = {
        "id": "ID",
        "created_at": "Created At",
        "receipt_no": "Receipt",
        "token_no": "Token",
        "price": "Price",
        "weight": "Weight",
        "sender_name": "Sender Name",
        "sender_phone": "Sender Phone",
        "receiver_name": "Receiver Name",
        "receiver_phone": "Receiver Phone",
        "city": "City",
        "state": "State",
        "receiver_pincode": "Recv Pin"
    }

    table_frame = tk.Frame(win, bg="#FAFAFA")
    table_frame.pack(fill="both", expand=True, padx=12, pady=(0,8))

    tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=22)
    vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
    tree.configure(yscroll=vsb.set, xscroll=hsb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")

    table_frame.grid_rowconfigure(0, weight=1)
    table_frame.grid_columnconfigure(0, weight=1)

    # headings & widths
    for c in cols:
        tree.heading(c, text=col_headers[c])
    widths = {
        "id": 60, "created_at": 140, "receipt_no": 110, "token_no": 90, "price": 80, "weight": 80,
        "sender_name": 160, "sender_phone": 120,
        "receiver_name": 160, "receiver_phone": 120,
        "city": 120, "state": 120, "receiver_pincode": 100
    }
    for c in cols:
        tree.column(c, width=widths.get(c, 120), anchor="w", stretch=True)

    # ---------- Data loader ----------
    def load_recent():
        # clear table
        for it in tree.get_children():
            tree.delete(it)

        session = get_session()
        try:
            cutoff = datetime.now() - timedelta(days=RECENT_DAYS)
            rows = (session.query(CourierForm)
                        .filter(CourierForm.created_at >= cutoff)
                        .order_by(CourierForm.created_at.desc())
                        .all())
        finally:
            session.close()

        for obj in rows:
            tree.insert("", "end", values=(
                obj.id,
                obj.created_at.strftime("%Y-%m-%d %H:%M:%S") if obj.created_at else "",
                obj.receipt_no or "",
                obj.token_no or "",
                obj.price or "",
                obj.weight or "",
                obj.sender_name or "",
                obj.sender_phone or "",
                obj.receiver_name or "",
                obj.receiver_phone or "",
                obj.city or "",
                obj.state or "",
                obj.receiver_pincode or ""
            ))

    # ---------- Row detail (optional) ----------
    def on_row_double_click(_evt):
        sel = tree.selection()
        if not sel:
            return
        vals = tree.item(sel[0], "values")
        rec_id = int(vals[0])

        detail = tk.Toplevel(win)
        detail.title(f"Record #{rec_id}")
        detail.geometry("520x420")

        txt = tk.Text(detail, wrap="word")
        txt.pack(fill="both", expand=True)

        session = get_session()
        try:
            obj = session.query(CourierForm).get(rec_id)
        finally:
            session.close()

        if not obj:
            txt.insert("end", "Record not found.")
        else:
            lines = [
                f"ID: {obj.id}",
                f"Created: {obj.created_at}",
                f"Updated: {obj.updated_at}",
                f"Receipt: {obj.receipt_no}",
                f"Token: {obj.token_no}",
                f"Price: {obj.price}",
                f"Weight: {obj.weight}",
                "",
                f"Sender: {obj.sender_name}",
                f"Sender Addr: {obj.sender_address}",
                f"Sender Pin: {obj.sender_pincode}",
                f"Sender Phone: {obj.sender_phone}",
                "",
                f"Receiver: {obj.receiver_name}",
                f"House: {obj.house}",
                f"Street: {obj.street}",
                f"Locality: {obj.locality}",
                f"City: {obj.city}",
                f"State: {obj.state}",
                f"Receiver Pin: {obj.receiver_pincode}",
                f"Receiver Phone: {obj.receiver_phone}",
            ]
            txt.insert("end", "\n".join(str(x) for x in lines))
        txt.configure(state="disabled")

    # Bind & initial load
    tree.bind("<Double-1>", on_row_double_click)
    btn_refresh.configure(command=load_recent)
    load_recent()

# Paths
CSV_PATH = resource_path("India_pincode.csv")
APP_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
DB_PATH = os.path.join(APP_DIR, "courierx.db")
DB_URL = f"sqlite:///{DB_PATH}"

# =========================
# SQLAlchemy setup
# =========================
Base = declarative_base()
_engine = None
SessionLocal = None

class CourierForm(Base):
    __tablename__ = "courier_forms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    receipt_no = Column(String(32))
    token_no = Column(String(32))
    weight = Column(String(32))
    price = Column(String(32))

    sender_name = Column(String(128))
    sender_address = Column(String(256))
    sender_pincode = Column(String(16))
    sender_phone = Column(String(16))

    receiver_name = Column(String(128))
    house = Column(String(64))
    street = Column(String(128))
    locality = Column(String(128))
    city = Column(String(128))
    state = Column(String(64))
    receiver_pincode = Column(String(16))
    receiver_phone = Column(String(16))

    created_at = Column(DateTime)
    updated_at = Column(DateTime)

def init_db():
    global _engine, SessionLocal
    _engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
    SessionLocal = scoped_session(sessionmaker(bind=_engine, autoflush=False, autocommit=False))
    Base.metadata.create_all(_engine)
    logging.info("SQLAlchemy DB ready at %s", DB_PATH)

def get_session():
    if SessionLocal is None:
        raise RuntimeError("DB not initialized. Call init_db() first.")
    return SessionLocal()

def insert_form_row_sqlalchemy(data: dict):
    """Insert one row via SQLAlchemy ORM."""
    try:
        now = datetime.now()
        obj = CourierForm(
            receipt_no=data.get("receipt_no"),
            token_no=data.get("token_no"),
            weight=data.get("weight"),
            price=data.get("price"),

            sender_name=data.get("sender_name"),
            sender_address=data.get("sender_address"),
            sender_pincode=data.get("sender_pincode"),
            sender_phone=data.get("sender_phone"),

            receiver_name=data.get("receiver_name"),
            house=data.get("house"),
            street=data.get("street"),
            locality=data.get("locality"),
            city=data.get("city"),
            state=data.get("state"),
            receiver_pincode=data.get("receiver_pincode"),
            receiver_phone=data.get("receiver_phone"),

            created_at=now,
            updated_at=now
        )
        session = get_session()
        session.add(obj)
        session.commit()
        session.close()
        return True, None
    except Exception as e:
        logging.exception("Insert failed: %s", e)
        # try to rollback if session is still open
        try:
            session.rollback()
            session.close()
        except Exception:
            pass
        return False, str(e)

# =========================
# Pincode CSV load (cached)
# =========================
PINCODES_DF = None
COL_AREA = COL_PIN = COL_DIST = COL_STATE = None

def load_pincode_csv():
    """Load India_pincode.csv with flexible column detection."""
    global PINCODES_DF, COL_AREA, COL_PIN, COL_DIST, COL_STATE
    try:
        PINCODES_DF = pd.read_csv(
            CSV_PATH, low_memory=False, dtype=str,
            encoding="utf-8", keep_default_na=False
        )
        PINCODES_DF.columns = [c.strip() for c in PINCODES_DF.columns]

        def find_col(candidates):
            cols_norm = {c: c.strip().lower().replace(" ", "").replace("_", "") for c in PINCODES_DF.columns}
            for c, n in cols_norm.items():
                if n in candidates:
                    return c
            return None

        COL_AREA = find_col({"area", "locality", "officename", "village", "location", "place", "areaname"})
        COL_PIN  = find_col({"pincode", "pin", "postcode", "zipcode", "pincodeno", "pincodenumber"})
        if COL_PIN is None:
            for c in PINCODES_DF.columns:
                if c.strip().lower() in ("pin code", "pin-code", "pin code number", "p.o.pincode"):
                    COL_PIN = c
                    break

        COL_DIST = next((c for c in PINCODES_DF.columns
                         if c.strip().lower() in ("district", "districtname", "district name")), None)
        COL_STATE = next((c for c in PINCODES_DF.columns
                          if c.strip().lower() in ("state", "statename", "state name")), None)
    except Exception as e:
        logging.exception(f"Failed to load India_pincode.csv from {CSV_PATH}: {e}")

load_pincode_csv()
if PINCODES_DF is None:
    logging.error("India_pincode.csv failed to load. CSV_PATH=%s", CSV_PATH)
else:
    logging.info("Loaded India_pincode.csv: %d rows. Using columns -> PIN: %s, DIST: %s, STATE: %s",
                 len(PINCODES_DF), COL_PIN, COL_DIST, COL_STATE)

# =========================
# Persistent Receipt Counter (text file)
# =========================
RECEIPT_FILE = os.path.join(tempfile.gettempdir(), "courierx_receipt_counter.txt")

def load_receipt_counter() -> int:
    try:
        if os.path.exists(RECEIPT_FILE):
            with open(RECEIPT_FILE, "r", encoding="utf-8") as f:
                val = int((f.read() or "0").strip())
                return max(1, val)
    except Exception:
        pass
    return 1

def save_receipt_counter(counter: int) -> None:
    try:
        with open(RECEIPT_FILE, "w", encoding="utf-8") as f:
            f.write(str(counter))
    except Exception:
        pass

_receipt_counter = load_receipt_counter()

def get_next_receipt() -> str:
    global _receipt_counter
    receipt_no = f"RX{_receipt_counter:05d}"
    _receipt_counter += 1
    save_receipt_counter(_receipt_counter)
    return receipt_no

def set_next_receipt_into_entry():
    entry_receipt.delete(0, tk.END)
    entry_receipt.insert(0, get_next_receipt())

def reset_receipt_counter():
    global _receipt_counter
    if messagebox.askyesno("Confirm Reset", "Do you want to reset Receipt No back to RX00001?"):
        _receipt_counter = 1
        save_receipt_counter(_receipt_counter)
        set_next_receipt_into_entry()
        status_var.set("Receipt counter reset to RX00001")

# =========================
# PIN lookup helpers (Receiver autofill)
# =========================
def lookup_pin(pin: str):
    """Return (district, state) from the loaded CSV for a given 6-digit pin."""
    if not (PINCODES_DF is not None and COL_PIN):
        return None, None
    pin = (pin or "").strip()
    if len(pin) != 6 or not pin.isdigit():
        return None, None
    try:
        rows = PINCODES_DF[PINCODES_DF[COL_PIN] == pin]
        if rows.empty:
            return None, None
        dist = rows.iloc[0][COL_DIST] if COL_DIST else ""
        state = rows.iloc[0][COL_STATE] if COL_STATE else ""
        return (str(dist).strip(), str(state).strip())
    except Exception as e:
        logging.exception("PIN lookup failed: %s", e)
        return None, None

def autofill_receiver_from_pin(_evt=None):
    dist, state = lookup_pin(entry_pincode.get())
    if dist:
        entry_city.delete(0, tk.END)
        entry_city.insert(0, dist)
    if state and state in INDIA_STATES:
        entry_state.set(state)
    status_var.set("PIN found." if (dist or state) else "PIN not found in CSV.")

# =========================
# Tkinter App
# =========================
def clear_form():
    entry_weight.delete(0, tk.END)
    entry_receipt.delete(0, tk.END)
    entry_pr.delete(0, tk.END)

    entry_sender_name.delete(0, tk.END)
    entry_sender_address.delete(0, tk.END)
    entry_pincode_sender.delete(0, tk.END)
    entry_sender_phone.delete(0, tk.END)

    entry_receiver_name.delete(0, tk.END)
    entry_house.delete(0, tk.END)
    entry_street.delete(0, tk.END)
    entry_locality.delete(0, tk.END)
    entry_city.delete(0, tk.END)
    entry_state.set("")
    entry_pincode.delete(0, tk.END)
    entry_receiver_phone.delete(0, tk.END)

    set_next_receipt_into_entry()
    status_var.set("Form cleared and new Receipt No assigned.")
    entry_token.focus_set()

def collect_form_data() -> dict:
    return {
        "receipt_no": entry_receipt.get().strip(),
        "token_no": entry_token.get().strip(),
        "weight": entry_weight.get().strip(),
        "price": entry_pr.get().strip(),

        "sender_name": entry_sender_name.get().strip(),
        "sender_address": entry_sender_address.get().strip(),
        "sender_pincode": entry_pincode_sender.get().strip(),
        "sender_phone": entry_sender_phone.get().strip(),

        "receiver_name": entry_receiver_name.get().strip(),
        "house": entry_house.get().strip(),
        "street": entry_street.get().strip(),
        "locality": entry_locality.get().strip(),
        "city": entry_city.get().strip(),
        "state": entry_state.get().strip(),
        "receiver_pincode": entry_pincode.get().strip(),
        "receiver_phone": entry_receiver_phone.get().strip(),
    }

def basic_validate(data: dict) -> bool:
    if not data["receipt_no"]:
        messagebox.showerror("Validation", "Receipt No is required.")
        return False
    if not data["sender_name"] or not data["receiver_name"]:
        messagebox.showerror("Validation", "Sender and Receiver names are required.")
        return False
    if data["receiver_pincode"] and (not data["receiver_pincode"].isdigit() or len(data["receiver_pincode"]) != 6):
        messagebox.showerror("Validation", "Receiver Pin Code must be 6 digits.")
        return False
    if data["sender_pincode"] and (not data["sender_pincode"].isdigit() or len(data["sender_pincode"]) != 6):
        messagebox.showerror("Validation", "Sender Pin Code must be 6 digits.")
        return False
    if data["sender_phone"] and (not data["sender_phone"].isdigit() or len(data["sender_phone"]) != 10):
        messagebox.showerror("Validation", "Sender Phone must be 10 digits.")
        return False
    if data["receiver_phone"] and (not data["receiver_phone"].isdigit() or len(data["receiver_phone"]) != 10):
        messagebox.showerror("Validation", "Receiver Phone must be 10 digits.")
        return False
    return True

def save_to_db():
    data = collect_form_data()
    if not basic_validate(data):
        return
    ok, err = insert_form_row_sqlalchemy(data)
    if ok:
        status_var.set("Saved.")
        messagebox.showinfo("Saved", "Form data saved to database.")
    else:
        messagebox.showerror("DB Error", f"Failed to save: {err or 'unknown error'}")

def print_form_details(font_size=12, line_spacing=1.5):
    # Save to DB before printing (submit)
    data = collect_form_data()
    if not basic_validate(data):
        return
    ok, err = insert_form_row_sqlalchemy(data)
    if not ok:
        messagebox.showerror("DB Error", f"Failed to save before printing: {err}")
        return

    details_left = {
        "Sender Name": data["sender_name"],
        "Sender Address": data["sender_address"],
        "Sender Pin Code": data["sender_pincode"],
        "Sender Phone": data["sender_phone"],
    }
    details_right = {
        "Receiver Name": data["receiver_name"],
        "House/Flat No": data["house"],
        "Street Name": data["street"],
        "Locality/Area": data["locality"],
        "City": data["city"],
        "State": data["state"],
        "Receiver Pin Code": data["receiver_pincode"],
        "Receiver Phone": data["receiver_phone"],
    }

    receipt_no = data["receipt_no"]
    token_no = data["token_no"]
    weight = data["weight"]
    price = data["price"]

    left_lines = [f"{k}: {v}" for k, v in details_left.items()]
    right_lines = [f"{k}: {v}" for k, v in details_right.items()]
    max_lines = max(len(left_lines), len(right_lines))
    while len(left_lines) < max_lines: left_lines.append("")
    while len(right_lines) < max_lines: right_lines.append("")

    left_width = max((len(line) for line in left_lines), default=20)
    right_width = max((len(line) for line in right_lines), default=20)

    header = f"*** RECEIPT NO: {receipt_no} ***"
    token_line = f"Token No: {token_no}"
    weight_price = f"Weight: {weight} kg   |   Price: ₹{price}"

    total_width = left_width + right_width + 7
    border_top = "╔" + "═" * total_width + "╗"
    border_bottom = "╚" + "═" * total_width + "╝"
    title = " CourierX Form Details "
    title_line = "║" + title.center(total_width) + "║"
    mid_sep = "╟" + "─" * total_width + "╢"

    content_lines = [
        "║ " + l.ljust(left_width) + " │ " + r.ljust(right_width) + " ║"
        for l, r in zip(left_lines, right_lines)
    ]

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    boxed_text = [
        border_top,
        title_line,
        "║" + header.center(total_width) + "║",
        "║" + token_line.center(total_width) + "║",
        "║" + weight_price.center(total_width) + "║",
        "║" + f"Day/Time: {ts}".center(total_width) + "║",
        mid_sep,
        *content_lines,
        border_bottom
    ]
    formatted_text = "\n".join(boxed_text)

    if not messagebox.askyesno("Confirm Print", "Saved to DB.\nDo you want to print the CourierX form details now?"):
        status_var.set("Saved to DB. Print cancelled by user.")
        return

    temp_path = os.path.join(tempfile.gettempdir(), "courier_form.txt")
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(formatted_text)
        os.startfile(temp_path, "print")
        status_var.set("Record saved and sending form to printer...")
    except Exception as e:
        messagebox.showerror("Print Error", f"Failed to print: {e}")

# =========================
# Build UI
# =========================
# Ensure DB exists
init_db()


# =========================
# 4-day unlock license (offline, tamper-resistant)
# =========================
TRIAL_DAYS = 4                               # Your 4-day unlock
TRIAL_SECONDS = TRIAL_DAYS * 86400           # Optional usage-seconds cap
LICENSE_FILE = os.path.join(APP_DIR, "courierx.lic")
SECRET_SALT = "CHANGE_ME_STRONG_RANDOM_SALT_32B"      # <<< change me
ACTIVATION_KEY = ("enter you passoword")                    # <<< your key

# Tamper controls
SMALL_SKEW = 120            # 2 minutes allowable backward skew
FORWARD_JUMP_CAP = 6*3600   # honor at most 6 hours of forward jump per run

def _machine_id() -> str:
    """Stable device id (MAC)."""
    return hex(uuid.getnode())[2:]

def _sign_blob(d: dict) -> str:
    """Sign all important fields + machine id with SECRET_SALT."""
    payload = json.dumps({
        "exp": int(d["exp"]),
        "last_wall": int(d["last_wall"]),
        "last_mono": round(float(d["last_mono"]), 3),
        "consumed_secs": int(d["consumed_secs"]),
        "mid": _machine_id()
    }, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload + SECRET_SALT.encode()).hexdigest()

def _save_license_blob(d: dict):
    d["sig"] = _sign_blob(d)
    blob = base64.b64encode(json.dumps(d).encode("utf-8"))
    with open(LICENSE_FILE, "wb") as f:
        f.write(blob)

def _load_license_blob():
    try:
        with open(LICENSE_FILE, "rb") as f:
            data = json.loads(base64.b64decode(f.read()).decode("utf-8"))
        expected = _sign_blob(data)
        if data.get("sig") != expected:
            return None
        return data
    except Exception:
        return None

def _init_new_license(exp_epoch: int):
    now_wall = int(time.time())
    now_mono = time.monotonic()
    d = {
        "exp": exp_epoch,
        "last_wall": now_wall,
        "last_mono": now_mono,
        "consumed_secs": 0
    }
    _save_license_blob(d)
    return d

def extend_license_days(days: int):
    """Stackable extension by calendar days; creates blob if missing."""
    now = int(time.time())
    d = _load_license_blob()
    if not d:
        base = now
        _init_new_license(base + days*86400)
        return
    base = max(int(d["exp"]), now)
    d["exp"] = base + days*86400
    _save_license_blob(d)

def _update_runtime_and_check():
    """
    Update checkpoints, accumulate usage (monotonic), detect clock tamper.
    Returns (ok: bool, reason: str).
    """
    d = _load_license_blob()
    if not d:
        return False, "No license"

    now_wall = int(time.time())
    now_mono = time.monotonic()
    try:
        last_wall = int(d.get("last_wall", now_wall))
        last_mono = float(d.get("last_mono", now_mono))
        consumed = int(d.get("consumed_secs", 0))
        exp = int(d.get("exp", 0))
    except Exception:
        return False, "Corrupt license data"

    # Detect backward clock
    if now_wall + SMALL_SKEW < last_wall:
        return False, "Clock rollback detected"

    # Monotonic delta
    delta_mono = max(0.0, now_mono - last_mono)

    # Forward jump handling (only honor up to CAP per run)
    forward_jump = max(0, now_wall - last_wall)
    honored_forward = min(forward_jump, FORWARD_JUMP_CAP)

    # Accumulate usage
    consumed += int(delta_mono + honored_forward)

    # Save updated checkpoints
    d["last_wall"] = now_wall
    d["last_mono"] = now_mono
    d["consumed_secs"] = consumed
    _save_license_blob(d)

    # Calendar AND/OR Usage checks
    calendar_ok = now_wall < exp
    usage_ok = consumed < TRIAL_SECONDS

    ok = calendar_ok and usage_ok
    reason = "" if ok else "Trial expired (calendar/usage)"
    return ok, reason

def license_is_active() -> bool:
    ok, _ = _update_runtime_and_check()
    return ok

def license_days_left() -> int:
    """
    Report remaining whole days by calendar (exp - now).
    Note: usage cap may expire earlier; this is for status display.
    """
    d = _load_license_blob()
    if not d:
        return 0
    exp = int(d.get("exp", 0))
    now = int(time.time())
    remaining = max(0, exp - now)
    return remaining // 86400


def show_activation_dialog(parent) -> bool:
    """Ask for key; if correct, extend by TRIAL_DAYS and return True. Else False."""
    ok_flag = {"ok": False}

    win = tk.Toplevel(parent)
    win.title("Activate CourierX (4-day unlock)")
    win.geometry("420x180")
    win.transient(parent)
    win.grab_set()
    win.resizable(False, False)

    frm = tk.Frame(win, padx=14, pady=14)
    frm.pack(fill="both", expand=True)

    tk.Label(frm, text="Enter activation key:", font=("Helvetica", 12)).pack(anchor="w")
    key_var = tk.StringVar()
    ent = ttk.Entry(frm, textvariable=key_var, width=36, show="*")
    ent.pack(fill="x", pady=(6,10))
    ent.focus_set()

    msg_var = tk.StringVar(value="")
    lbl_msg = tk.Label(frm, textvariable=msg_var, fg="red")
    lbl_msg.pack(anchor="w", pady=(0,6))

    btns = tk.Frame(frm)
    btns.pack(fill="x")
    def _do_ok():
        key = key_var.get().strip()
        if key == ACTIVATION_KEY:
            extend_license_days(TRIAL_DAYS)
            ok_flag["ok"] = True
            messagebox.showinfo("Success", f"Activated for {TRIAL_DAYS} days.")
            win.destroy()
        else:
            msg_var.set("Invalid key. Please try again.")

    def _do_cancel():
        ok_flag["ok"] = False
        win.destroy()

    ttk.Button(btns, text="Activate", command=_do_ok).pack(side="left")
    ttk.Button(btns, text="Cancel", command=_do_cancel).pack(side="right")

    parent.wait_window(win)
    return ok_flag["ok"]

def enforce_license_or_exit(root_window) -> None:
    """Call this early. Blocks UI until activated; exits if user cancels."""
    if license_is_active():
        return
    if not show_activation_dialog(root_window):
        messagebox.showwarning("Activation required", "App will now close.")
        root_window.destroy()
        sys.exit(0)


# ===== Runtime lock (overlay) =====
EXPIRED_LOCK = {"win": None}

def _show_expired_overlay():
    # If already showing, bring front and focus (avoid duplicate hooks)
    if EXPIRED_LOCK["win"] is not None and EXPIRED_LOCK["win"].winfo_exists():
        try:
            EXPIRED_LOCK["win"].lift()
            EXPIRED_LOCK["win"].focus_force()
        except Exception:
            pass
        return

    win = tk.Toplevel(root)
    EXPIRED_LOCK["win"] = win
    win.title("License expired")
    try:
        win.attributes("-fullscreen", True)
    except Exception:
        win.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0")
    win.configure(bg="#111111")
    try:
        win.attributes("-topmost", True)
        win.attributes("-alpha", 0.90)  # dim overlay (optional)
    except Exception:
        pass

    # Block and trap focus so nothing underneath is clickable/typable
    win.transient(root)
    win.grab_set()
    win.focus_set()

    # Make it non-closable / non-escapable
    win.protocol("WM_DELETE_WINDOW", lambda: None)
    win.bind("<Alt-F4>", lambda e: "break")
    win.bind("<Escape>", lambda e: "break")

    # Consume all input globally while overlay is up
    def _consume(_e): return "break"
    for seq in ("<Button>", "<ButtonRelease>", "<Motion>", "<Key>", "<KeyRelease>"):
        try: win.unbind_all(seq)
        except Exception: pass
        win.bind_all(seq, _consume)

    # Center card UI
    card = tk.Frame(win, bg="white", padx=24, pady=24)
    card.place(relx=0.5, rely=0.5, anchor="center")

    tk.Label(card, text="🔒 CourierX is Locked",
             font=("Helvetica", 18, "bold"), bg="white").pack(pady=(4,8))
    tk.Label(card,
             text="Your license has expired or clock tampering was detected.\nPlease activate to continue.",
             font=("Helvetica", 12), bg="white", justify="center").pack(pady=(0,16))

    btns = tk.Frame(card, bg="white"); btns.pack()

    def _do_activate():
        if show_activation_dialog(root):
            # Close overlay after successful activation
            try: win.grab_release()
            except Exception: pass
            win.destroy()
            EXPIRED_LOCK["win"] = None

    def _do_exit():
        try: win.grab_release()
        except Exception: pass
        root.destroy()
        sys.exit(0)

    ttk.Button(btns, text="🔑 Activate", command=_do_activate).pack(side="left", padx=6)
    ttk.Button(btns, text="Exit", command=_do_exit).pack(side="left", padx=6)


root = tk.Tk()
root.attributes("-fullscreen", True)
root.title("Courier Form")
root.configure(bg="#F5F5F5")

enforce_license_or_exit(root)


def _license_watchdog():
    if not license_is_active():
        _show_expired_overlay()
    root.after(1000, _license_watchdog)  # check every second

_license_watchdog()


# Header
header = tk.Frame(root, bg="#1a237e")
header.pack(side="top", fill="x")
tk.Label(header, text="CourierX", fg="white", bg="#1a237e",
         font=("Helvetica", 18, "bold")).pack(side="left", padx=16, pady=10)

btn_frame = tk.Frame(header, bg="#1a237e")
btn_frame.pack(side="right", padx=10)



def on_close():
    if messagebox.askyesno("Exit", "Are you sure you want to close CourierX?"):
        root.destroy()

def on_minimize():
    root.iconify()



btn_close = tk.Label(btn_frame, text="✖", fg="white", bg="#1a237e",
                     font=("Helvetica", 16, "bold"), width=3, cursor="hand2")
btn_close.pack(side="right", padx=2)
btn_close.bind("<Enter>", lambda e: btn_close.config(bg="red"))
btn_close.bind("<Leave>", lambda e: btn_close.config(bg="#1a237e"))
btn_close.bind("<Button-1>", lambda e: on_close())

btn_min = tk.Label(btn_frame, text="➖", fg="white", bg="#1a237e",
                   font=("Helvetica", 16, "bold"), width=3, cursor="hand2")
btn_min.pack(side="right", padx=2)
btn_min.bind("<Enter>", lambda e: btn_min.config(bg="#3949ab"))
btn_min.bind("<Leave>", lambda e: btn_min.config(bg="#1a237e"))
btn_min.bind("<Button-1>", lambda e: on_minimize())
btn_reports = tk.Label(btn_frame, text="📊 Reports", fg="white", bg="#1a237e",
                       font=("Helvetica", 12, "bold"), cursor="hand2", padx=10, pady=4)
btn_reports.pack(side="right", padx=8)
btn_reports.bind("<Enter>", lambda e: btn_reports.config(bg="#3949ab"))
btn_reports.bind("<Leave>", lambda e: btn_reports.config(bg="#1a237e"))
btn_reports.bind("<Button-1>", lambda e: open_reports_window())

btn_activate = tk.Label(btn_frame, text="🔑 Activate", fg="white", bg="#1a237e",
                        font=("Helvetica", 12, "bold"), cursor="hand2", padx=10, pady=4)
btn_activate.pack(side="right", padx=8)
btn_activate.bind("<Enter>", lambda e: btn_activate.config(bg="#3949ab"))
btn_activate.bind("<Leave>", lambda e: btn_activate.config(bg="#1a237e"))
def _do_activate(_=None):
    if show_activation_dialog(root):
        # refresh status bar with remaining days
        try:
            status_var.set(f"Activated. Days left: {license_days_left()}")
        except Exception:
            pass
btn_activate.bind("<Button-1>", _do_activate)


# Fonts and Styles
LABEL_FONT = ("Helvetica", 15)
HEADER_FONT = ("Helvetica", 18, "bold")
style = ttk.Style()
style.configure("TLabel", background="#F5F5F5", font=LABEL_FONT)
style.configure("TButton", font=LABEL_FONT, padding=10)
style.configure("TEntry", font=LABEL_FONT, padding=8)
style.configure("TLabelframe.Label", font=HEADER_FONT)

# Status Bar
status_var = tk.StringVar(value="Ready")
status_bar = ttk.Label(root, textvariable=status_var, relief="sunken", anchor="w")
status_bar.pack(fill="x", side="bottom")

# Validations
def validate_phone(P): return P == "" or (P.isdigit() and len(P) <= 10)
def validate_pincode(P): return P == "" or (P.isdigit() and len(P) <= 6)
def validate_name(P): return P == "" or (len(P) <= 30 and all(c.isalpha() or c.isspace() for c in P))

phone_vcmd = (root.register(validate_phone), '%P')
pincode_vcmd = (root.register(validate_pincode), '%P')
name_vcmd = (root.register(validate_name), '%P')

# Package Details
package_frame = ttk.LabelFrame(root, text="📦 Package Details", padding=10)
package_frame.pack(fill="x", padx=20, pady=10)

ttk.Label(package_frame, text="Weight (kg):").grid(row=0, column=0, sticky="w", pady=5)
entry_weight = ttk.Entry(package_frame, width=30)
entry_weight.grid(row=0, column=1, pady=5)

ttk.Label(package_frame, text="Receipt No:").grid(row=0, column=2, sticky="w", pady=5)
entry_receipt = ttk.Entry(package_frame, width=30)
entry_receipt.grid(row=0, column=3, pady=5)

ttk.Label(package_frame, text="Token No:").grid(row=0, column=4, sticky="w", pady=5)
entry_token = ttk.Entry(package_frame, width=30)
entry_token.grid(row=0, column=5, pady=5)
entry_token.focus_set()

def clear_token():
    entry_token.delete(0, tk.END)
    entry_token.focus_set()
    status_var.set("Token number cleared.")

btn_clear_token = ttk.Button(package_frame, text="Clear Token", command=clear_token)
btn_clear_token.grid(row=1, column=5, pady=5, sticky="e")

btn_reset_counter = tk.Button(package_frame, text="⟲", width=2,
                              command=reset_receipt_counter, bg="#e0e0e0", fg="black")
btn_reset_counter.grid(row=1, column=2, sticky="e", padx=(0,5), pady=5)

btn_next_receipt = ttk.Button(package_frame, text="Next Receipt No", command=set_next_receipt_into_entry)
btn_next_receipt.grid(row=1, column=3, pady=5, sticky="w")

price_live_var = tk.StringVar(value=" ₹ Price:")
ttk.Label(package_frame, textvariable=price_live_var).grid(row=1, column=0, columnspan=2, sticky="w")
entry_pr = ttk.Entry(package_frame, width=30)
entry_pr.grid(row=1, column=1, pady=5)

# Sender Info
sender_frame = ttk.LabelFrame(root, text="📍 Sender Information", padding=10)
sender_frame.pack(fill="x", padx=20, pady=10)

ttk.Label(sender_frame, text="Full Name:").grid(row=0, column=0, sticky="w", pady=5)
entry_sender_name = ttk.Entry(sender_frame, width=30, validate="key", validatecommand=name_vcmd)
entry_sender_name.grid(row=0, column=1, pady=5)

ttk.Label(sender_frame, text="Address:").grid(row=1, column=0, sticky="w", pady=5)
entry_sender_address = ttk.Entry(sender_frame, width=30)
entry_sender_address.grid(row=1, column=1, pady=5)

ttk.Label(sender_frame, text="Pin Code:").grid(row=1, column=2, sticky="w", pady=5)
entry_pincode_sender = ttk.Entry(sender_frame, width=30, validate="key", validatecommand=pincode_vcmd)
entry_pincode_sender.grid(row=1, column=3, pady=5)

ttk.Label(sender_frame, text="Phone Number:").grid(row=2, column=0, sticky="w", pady=5)
entry_sender_phone = ttk.Entry(sender_frame, width=30, validate="key", validatecommand=phone_vcmd)
entry_sender_phone.grid(row=2, column=1, pady=5)

# Receiver Info
receiver_frame = ttk.LabelFrame(root, text="📦 Receiver Information", padding=10)
receiver_frame.pack(fill="x", padx=20, pady=10)

ttk.Label(receiver_frame, text="Full Name:").grid(row=0, column=0, sticky="w", pady=5)
entry_receiver_name = ttk.Entry(receiver_frame, width=30, validate="key", validatecommand=name_vcmd)
entry_receiver_name.grid(row=0, column=1, pady=5)

ttk.Label(receiver_frame, text="House/Flat No.:").grid(row=0, column=2, sticky="w", pady=5)
entry_house = ttk.Entry(receiver_frame, width=30)
entry_house.grid(row=0, column=3, pady=5)

ttk.Label(receiver_frame, text="Street Name:").grid(row=1, column=0, sticky="w", pady=5)
entry_street = ttk.Entry(receiver_frame, width=30)
entry_street.grid(row=1, column=1, pady=5)

ttk.Label(receiver_frame, text="Locality/Area:").grid(row=1, column=2, sticky="w", pady=5)
entry_locality = ttk.Entry(receiver_frame, width=30)
entry_locality.grid(row=1, column=3, pady=5)

ttk.Label(receiver_frame, text="City (District):").grid(row=2, column=0, sticky="w", pady=5)
entry_city = ttk.Entry(receiver_frame, width=30)
entry_city.grid(row=2, column=1, pady=5)

ttk.Label(receiver_frame, text="State:").grid(row=2, column=2, sticky="w", pady=5)
INDIA_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Delhi", "Goa", "Gujarat", "Haryana",
    "Himachal Pradesh", "Jammu and Kashmir", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra",
    "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana",
    "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal", "Chandigarh", "Ladakh", "Puducherry",
    "Andaman and Nicobar Islands", "Dadra and Nagar Haveli and Daman and Diu", "Lakshadweep"
]
entry_state = ttk.Combobox(receiver_frame, width=28, values=INDIA_STATES)
entry_state.grid(row=2, column=3, pady=5)

ttk.Label(receiver_frame, text="Pin Code:").grid(row=3, column=0, sticky="w", pady=5)
entry_pincode = ttk.Entry(receiver_frame, width=30, validate="key", validatecommand=pincode_vcmd)
entry_pincode.grid(row=3, column=1, pady=5)
entry_pincode.bind("<FocusOut>", autofill_receiver_from_pin)

ttk.Label(receiver_frame, text="Phone Number:").grid(row=3, column=2, sticky="w", pady=5)
entry_receiver_phone = ttk.Entry(receiver_frame, width=30, validate="key", validatecommand=phone_vcmd)
entry_receiver_phone.grid(row=3, column=3, pady=5)

btn_clear_form = ttk.Button(receiver_frame, text="Clear Form", command=clear_form)
btn_clear_form.grid(row=3, column=4, padx=10, pady=5)

btn_print_form = ttk.Button(receiver_frame, text="saves", command=print_form_details)
btn_print_form.grid(row=3, column=5, padx=10, pady=5)

# Save button
btn_save_db = ttk.Button(receiver_frame, text="💾 Save to DB", command=save_to_db)
btn_save_db.grid(row=4, column=5, padx=10, pady=(5,10), sticky="e")

# Status + DB path quick info
db_hint = ttk.Label(root, text=f"DB: {DB_PATH}", font=("Helvetica", 9))
db_hint.pack(side="bottom", anchor="w", padx=8, pady=(0,6))

# Initialize first receipt number
set_next_receipt_into_entry()

root.mainloop()
