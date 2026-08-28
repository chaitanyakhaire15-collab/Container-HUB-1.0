from flask import Flask, render_template, request, redirect
import sqlite3, os

app = Flask(__name__, template_folder='tamplates')

# --- CONFIG - EDIT HERE ---
UPI_ID = "yourupi@paytm"
BUYER_FEE = 3 # %
SELLER_FEE = 7 # %
TOKEN = 2000

def init_db():
    conn = sqlite3.connect('database.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS containers
        (id INTEGER PRIMARY KEY, title TEXT, city TEXT, size TEXT, type TEXT, price INTEGER, photo TEXT, seller_phone TEXT, status TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS deals
        (id INTEGER PRIMARY KEY, container_id INTEGER, buyer_name TEXT, buyer_phone TEXT, sale_price INTEGER, buyer_fee INTEGER, seller_fee INTEGER, buyer_pays INTEGER, seller_gets INTEGER, profit INTEGER, status TEXT)''')
    if not conn.execute("SELECT * FROM containers").fetchone():
        conn.execute("INSERT INTO containers (title,city,size,type,price,photo,seller_phone,status) VALUES (?,?,?,?,?,?,?,?)",
                     ("20ft Dry - Cargo Worthy", "Nhava Sheva", "20ft", "Dry", 185000, "https://images.unsplash.com/photo-1494412651409-8963ce7935b4?w=800", "919999999999", "Available"))
        conn.execute("INSERT INTO containers (title,city,size,type,price,photo,seller_phone,status) VALUES (?,?,?,?,?,?,?,?)",
                     ("40ft HC - IICL 5 Grade A", "Bhiwandi", "40ft", "Dry", 310000, "https://images.unsplash.com/photo-1578575437130-527eed3abbec?w=800", "919999999999", "Available"))
        conn.execute("INSERT INTO containers (title,city,size,type,price,photo,seller_phone,status) VALUES (?,?,?,?,?,?,?,?)",
                     ("40ft Reefer - Working", "Panvel", "40ft", "Reefer", 450000, "https://images.unsplash.com/photo-1605745341112-85968b19335b?w=800", "919999999999", "Available"))
        conn.commit()
    conn.close()
init_db()

@app.route('/')
def index():
    conn = sqlite3.connect('database.db')
    city = request.args.get('city','')
    size = request.args.get('size','')
    q = "SELECT * FROM containers WHERE status='Available'"
    params = []
    if city:
        q += " AND city LIKE?"
        params.append(f"%{city}%")
    if size:
        q += " AND size=?"
        params.append(size)
    containers = conn.execute(q, params).fetchall()
    conn.close()
    return render_template('index.html', containers=containers)

@app.route('/container/<int:id>')
def detail(id):
    conn = sqlite3.connect('database.db')
    c = conn.execute("SELECT * FROM containers WHERE id=?", (id,)).fetchone()
    conn.close()
    price = c[5]
    buyer_fee = int(price * BUYER_FEE / 100)
    seller_fee = int(price * SELLER_FEE / 100)
    return render_template('detail.html', c=c, price=price, buyer_fee=buyer_fee, seller_fee=seller_fee, buyer_pays=price+buyer_fee, seller_gets=price-seller_fee, profit=buyer_fee+seller_fee, token=TOKEN, upi=UPI_ID)

@app.route('/pay-token/<int:id>', methods=['POST'])
def pay_token(id):
    conn = sqlite3.connect('database.db')
    c = conn.execute("SELECT * FROM containers WHERE id=?", (id,)).fetchone()
    price = c[5]
    bf = int(price * BUYER_FEE / 100)
    sf = int(price * SELLER_FEE / 100)
    conn.execute("INSERT INTO deals (container_id,buyer_name,buyer_phone,sale_price,buyer_fee,seller_fee,buyer_pays,seller_gets,profit,status) VALUES (?,?,?,?,?,?,?,?,?,?)",
                 (id, request.form['name'], request.form['phone'], price, bf, sf, price+bf, price-sf, bf+sf, 'token_paid'))
    conn.execute("UPDATE containers SET status='Locked' WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    conn = sqlite3.connect('database.db')
    deals = conn.execute("SELECT * FROM deals ORDER BY id DESC").fetchall()
    total = sum(d[9] for d in deals) if deals else 0
    conn.close()
    return render_template('dashboard.html', deals=deals, total=total)

@app.route('/reset')
def reset():
    if os.path.exists('database.db'): os.remove('database.db')
    init_db()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
