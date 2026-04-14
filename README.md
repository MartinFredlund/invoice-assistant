# Invoice Assistant

A simple, local web application to generate styled PDF invoices for freelancers and small businesses. It uses Flask to provide a web interface, and WeasyPrint to reliably transform HTML templates into well-structured PDFs.

## Disclaimer

**Please note:** This software is provided as-is. You are entirely responsible for ensuring that the generated invoices comply with your local accounting, tax, and legal requirements. Always double-check the calculations, VAT (moms) amounts, and mandatory information on the invoices before sending them to clients.

## Features

- **Web interface:** A clean form to input invoice details, add unlimited line items, and perform automatic calculations for sums, VAT (moms), and totals.
- **Customer Storage:** Save customer details to avoid re-typing them for frequent buyers. Data is saved locally in `data/customers.json`.
- **Automatic Numbering:** Auto-increments invoice numbers per year (e.g., `2026-1`), managed purely via local storage (`data/invoice_state.json`).
- **PDF Generation:** Outputs beautiful, fully formatted natively generated PDF files straight to your `invoices/` directory matching the standard Swedish invoice layout.

## Project Structure

```text
InvoiceAssistant/
├── app.py                      # Flask backend and routing
├── requirements.txt            # Python dependencies
├── data/                       # Storage for customer lists and invoice state (auto-created)
├── invoices/                   # Directory where generated invoice PDFs are saved (auto-created)
├── templates/                  
│   ├── form.html               # The local Web UI 
│   └── invoice_pdf.html        # The stylized HTML layout to be compiled into a PDF
└── static/
    └── style.css               # Styling for the Web UI
```

## Setup & Installation

**Prerequisites:** You will need Python (3.8+) installed. Since this app uses WeasyPrint, depending on your operating system, you might need extra system dependencies like Pango or Cairo if they are not already installed locally. (Linux typically has these installed or easily accessible via your package manager).

1. **Clone or navigate to the directory in a terminal**
   ```bash
   cd /path/to/InvoiceAssistant
   ```

2. **Set up a virtual environment (Recommended)**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**
   Copy the example environment file and update it with your own company details.
   ```bash
   cp .env.example .env
   ```
   *(Be sure to edit `.env` and fill in your company information so it populates correctly on generated invoices.)*

## Usage

1. **Start the local app**
   ```bash
   python app.py
   ```
2. **Access the application**
   Open your browser and navigate to [http://127.0.0.1:5000](http://127.0.0.1:5000).
3. **Generate**
   Fill in the invoice fields, and click "Skapa Faktura (PDF)". Your browser will smoothly download a copy of the PDF, and it will also be securely saved within the `invoices/` folder.

### About Your Data
This application operates completely locally and automatically creates its folders on startup. 
The `data/` and `invoices/` directories are explicitly ignored by Git (via `.gitignore`), ensuring that if you publish this code or push it to a repository like GitHub, your private customer records and invoices remain completely hidden on your local machine.

## Customization

### Adding a Logo

If you'd like your company logo to appear on the PDF invoice, simply add the file path to your `.env` file!

1. Save your image securely (e.g., in the `static/` directory as `logo.png`).
2. Update the `COMPANY_LOGO_PATH` in your `.env` file to point to it (a relative path like `static/logo.png` works perfectly).

```env
COMPANY_LOGO_PATH="static/logo.png"
```

### Sender Defaults

If you need to change your organization number, plusgiro, or address in the footer of the invoice later on, you can simply edit the `.env` file in the project's root folder. An example configuration is provided at `.env.example`.
