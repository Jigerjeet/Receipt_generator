CourierX – Offline Courier Form (Tkinter, SQLite, CSV PIN lookup)

CourierX is a Windows-friendly desktop app for booking courier shipments.
It’s built with Tkinter + SQLAlchemy (SQLite) and includes:

📦 Sender/receiver form with validation

📍 Auto-fill city/state from India_pincode.csv

🧾 Auto-incrementing Receipt No with reset

💾 Save to SQLite (courierx.db)

🖨️ Print a formatted text receipt

📊 “Recent Reports” window (last N days)

🔒 4-day activation mechanism (offline, tamper-resistant overlay)

This repo is intended for Windows 10+. It also works on other OSes for basic UI/DB features (printing via os.startfile(..., "print") is Windows-specific).

✨ Features

Form fields: sender/receiver names, address, phones, pincode, weight, price, receipt/token.

PIN lookup: Type receiver PIN and tab out → district/state auto-fills from India_pincode.csv.

DB: Records stored in courierx.db via SQLAlchemy ORM model CourierForm.

Reports: View last X days (default 30) with double-click details.

Printing: Confirms, persists to DB, then prints a nicely boxed text receipt.

Activation: 4-day unlock with offline license blob, clock-tamper checks, full-screen lock overlay when expired.
🖨️ Printing

The Save and Print button (saves) will:

Validate and save form to DB

Ask confirmation to print

Create a text file in %TEMP%\courier_form.txt and call Windows print via os.startfile(temp_path, "print")

On non-Windows systems, os.startfile isn’t available; you can replace it with a platform-specific command or skip printing.

🗃 Database Model (ORM)

CourierForm fields (SQLite):

id, created_at, updated_at

receipt_no, token_no, weight, price

sender_* (name, address, pincode, phone)

receiver_* (name, house, street, locality, city, state, pincode, phone)

Use the Reports button in the header to open the recent records table, with double-click details.

🧪 Validations

Phone numbers: 10 digits

PIN codes: 6 digits

Names: letters/spaces (≤30 chars)

Basic non-empty checks for required fields

🐞 Troubleshooting

CSV not found / empty: Make sure India_pincode.csv is present and has columns as noted above.

Printing fails: Ensure a default printer is configured on Windows; otherwise you’ll see a print error dialog.

License expired immediately: If system clock was adjusted backwards, the overlay will appear. Use Activate to extend or reset your trial.

DB locked: If you force-close the app during writes, SQLite may lock. Re-run the app; it uses scoped_session and commits per insert.
