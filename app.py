import os
import json
import uuid
import datetime
from flask import Flask, render_template, request, jsonify, send_file
from weasyprint import HTML, CSS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
INVOICE_DIR = os.path.join(os.path.dirname(__file__), 'invoices')
CUSTOMERS_FILE = os.path.join(DATA_DIR, 'customers.json')
STATE_FILE = os.path.join(DATA_DIR, 'invoice_state.json')

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(INVOICE_DIR, exist_ok=True)

# Create init files if they don't exist
if not os.path.exists(CUSTOMERS_FILE):
    with open(CUSTOMERS_FILE, 'w') as f:
        json.dump([], f)
if not os.path.exists(STATE_FILE):
    with open(STATE_FILE, 'w') as f:
        json.dump({"next_invoice_number": 1, "year": datetime.date.today().year}, f)

def read_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_next_invoice_number():
    state = read_json(STATE_FILE)
    current_year = datetime.date.today().year
    
    if state.get("year") != current_year:
        state["year"] = current_year
        state["next_invoice_number"] = 1
        write_json(STATE_FILE, state)
        
    return f"{state['year']}-{state['next_invoice_number']}"

def increment_invoice_number():
    state = read_json(STATE_FILE)
    state["next_invoice_number"] += 1
    write_json(STATE_FILE, state)

@app.template_filter('sek')
def format_sek(value):
    try:
        val = float(value)
        # Format like 1.800,00
        formatted = f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", " ")
        return formatted
    except (ValueError, TypeError):
        return value

SENDER_DEFAULTS = {
    "name": os.getenv("COMPANY_NAME", "Eva Fredlund Keramik"),
    "street": os.getenv("COMPANY_STREET", "Ljungvägen 1"),
    "city": os.getenv("COMPANY_CITY", "247 60 Veberöd"),
    "contact": os.getenv("COMPANY_CONTACT", "Eva Fredlund, 0730-264123"),
    "plusgiro": os.getenv("COMPANY_PLUSGIRO", "199 94 87-0"),
    "org_nr": os.getenv("COMPANY_ORG_NR", "196906129363"),
    "f_skatt": os.getenv("COMPANY_F_SKATT", "True").lower() in ("true", "1", "yes")
}

@app.route('/')
def index():
    today = datetime.date.today()
    due_date = today + datetime.timedelta(days=20)
    
    defaults = {
        "invoice_number": get_next_invoice_number(),
        "invoice_date": today.strftime('%Y-%m-%d'),
        "due_date": due_date.strftime('%Y-%m-%d')
    }
    return render_template('form.html', defaults=defaults)

@app.route('/generate', methods=['POST'])
def generate_invoice():
    data = request.json
    
    items = data.get('items', [])
    exkl_moms = 0
    moms_total = 0
    
    for item in items:
        # Expected: antal, a_pris, moms_procent
        antal = float(item.get('antal', 0))
        a_pris = float(item.get('a_pris', 0))
        moms_procent = float(item.get('moms_procent', 0))
        
        summa = antal * a_pris
        item['summa'] = summa
        exkl_moms += summa
        moms_total += summa * (moms_procent / 100.0)
        
    att_betala = exkl_moms + moms_total
    
    invoice_number = get_next_invoice_number()
    
    invoice_data = {
        "sender": SENDER_DEFAULTS,
        "customer": data.get('customer', {}),
        "metadata": {
            "invoice_number": invoice_number,
            "invoice_date": data.get('invoice_date'),
            "due_date": data.get('due_date'),
            "betalningsvillkor": data.get('betalningsvillkor', '20 Dagar netto'),
            "drojsmalsranta": data.get('drojsmalsranta', '8 %'),
            "ocr": data.get('ocr', invoice_number.replace("-", "")),
            "var_referens": data.get('var_referens', 'Eva Fredlund'),
            "ordernummer": data.get('ordernummer', ''),
            "leveransvillkor": data.get('leveransvillkor', ''),
            "leveranssatt": data.get('leveranssatt', ''),
            "leveransdatum": data.get('leveransdatum', '')
        },
        "items": items,
        "totals": {
            "exkl_moms": exkl_moms,
            "moms_total": moms_total,
            "att_betala": att_betala
        },
        "message": data.get('message', 'Tack för beställningen.'),
        "logo_path": os.getenv("COMPANY_LOGO_PATH") or data.get('logo_path', None)
    }
    
    rendered_html = render_template('invoice_pdf.html', data=invoice_data)
    
    # Save PDF
    pdf_filename = f"Faktura_{invoice_number}.pdf"
    pdf_path = os.path.join(INVOICE_DIR, pdf_filename)
    HTML(string=rendered_html, base_url=os.path.dirname(__file__)).write_pdf(pdf_path)
    
    increment_invoice_number()
    
    return jsonify({"success": True, "download_url": f"/download/{pdf_filename}"})

@app.route('/download/<filename>')
def download_pdf(filename):
    pdf_path = os.path.join(INVOICE_DIR, filename)
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True)
    return "Not found", 404

@app.route('/customers', methods=['GET'])
def get_customers():
    return jsonify(read_json(CUSTOMERS_FILE))

@app.route('/customers', methods=['POST'])
def save_customer():
    data = request.json
    customers = read_json(CUSTOMERS_FILE)
    
    if 'id' not in data or not data['id']:
        data['id'] = str(uuid.uuid4())
        
    updated = False
    for i, c in enumerate(customers):
        if c.get('id') == data['id']:
            customers[i] = data
            updated = True
            break
            
    if not updated:
        customers.append(data)
        
    write_json(CUSTOMERS_FILE, customers)
    return jsonify({"success": True, "id": data['id']})

@app.route('/customers/<customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    customers = read_json(CUSTOMERS_FILE)
    customers = [c for c in customers if c.get('id') != customer_id]
    write_json(CUSTOMERS_FILE, customers)
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
