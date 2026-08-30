from flask import Flask, render_template, request, redirect, g
import sqlite3, os

app = Flask(__name__, template_folder='tamplates')
DB = 'hub.db'
ADMIN_PASSWORD = "admin123"

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB)
        db.execute('''CREATE TABLE IF NOT EXISTS containers
        (id INTEGER PRIMARY KEY, title TEXT, city TEXT, size TEXT, type TEXT, price INTEGER, photo TEXT, phone TEXT, status TEXT)''')
        db.execute('''CREATE TABLE IF NOT EXISTS deals
        (id INTEGER PRIMARY KEY, container_id INTEGER, buyer_name TEXT, buyer_phone TEXT, sale_price INTEGER, buyer_fee INTEGER, seller_fee INTEGER, buyer_pays INTEGER, seller_gets INTEGER, profit INTEGER, status TEXT)''')
        # Default container if empty
        if db.execute('SELECT COUNT(*) FROM containers').fetchone()[0] == 0:
            db.execute("INSERT INTO containers (title,city,size,type,price,photo,phone,status) VALUES (?,?,?,?,?,?,?,?)",
            ("20ft Dry Container - Bhiwandi","Bhiwandi","20ft","Dry",80000,"https://images.unsplash.com/photo-1494412574643-ff11b0a5c1c3","9000000001","available"))
            db.commit()
    return db

# HOME - Buyer site
@app.route('/')
def home():
    db = get_db()
    q = request.args.get('q','')
    city = request.args.get('city','')
    if q:
        cons = db.execute("SELECT * FROM containers WHERE status='available' AND (title LIKE? OR city LIKE?)", (f'%{q}%',f'%{q}%')).fetchall()
    elif city:
        cons = db.execute("SELECT * FROM containers WHERE status='available' AND city LIKE?", (f'%{city}%',)).fetchall()
    else:
        cons = db.execute("SELECT * FROM containers WHERE status='available'").fetchall()
    return render_template('index.html', containers=cons)

# DETAIL PAGE
@app.route('/detail/<int:cid>')
def detail(cid):
    db = get_db()
    c = db.execute("SELECT * FROM containers WHERE id=?", (cid,)).fetchone()
    return render_template('detail.html', c=c)

# PAY / BOOKING - 5% Token + Commission
@app.route('/pay/<int:cid>', methods=['POST'])
def pay(cid):
    db = get_db()
    c = db.execute("SELECT * FROM containers WHERE id=?", (cid,)).fetchone()
    if not c:
        return "Container not found"
    name = request.form.get('buyer_name')
    phone = request.form.get('buyer_phone')
    sale_price = int(c[5])
    buyer_fee = int(sale_price * 0.03) # 3% buyer se
    seller_fee = int(sale_price * 0.02) # 2% seller se
    buyer_pays = int(sale_price * 0.05) # total token
    seller_gets = sale_price - seller_fee
    profit = buyer_fee + seller_fee
    db.execute("INSERT INTO deals (container_id,buyer_name,buyer_phone,sale_price,buyer_fee,seller_fee,buyer_pays,seller_gets,profit,status) VALUES (?,?,?,?,?,?,?,?,?,?)",
    (cid,name,phone,sale_price,buyer_fee,seller_fee,buyer_pays,seller_gets,profit,'token_paid'))
    db.execute("UPDATE containers SET status='sold' WHERE id=?", (cid,))
    db.commit()
    return redirect(f'/my-orders?phone={phone}&success=1')

# SELLER PAGE
@app.route('/seller', methods=['GET','POST'])
def seller():
    db = get_db()
    if request.method == 'POST':
        db.execute("INSERT INTO containers (title,city,size,type,price,photo,phone,status) VALUES (?,?,?,?,?,?,?,?)",
        (request.form['title'],request.form['city'],request.form['size'],request.form['type'],int(request.form['price']),request.form['photo'],request.form['phone'],'available'))
        db.commit()
        return redirect('/seller?added=1&phone='+request.form['phone'])
    phone = request.args.get('phone','')
    my = db.execute("SELECT * FROM containers WHERE phone=?", (phone,)).fetchall() if phone else []
    return render_template('seller.html', phone=phone, my_containers=my)

# MY ORDERS
@app.route('/my-orders')
def my_orders():
    db = get_db()
    phone = request.args.get('phone','')
    deals = db.execute("SELECT * FROM deals WHERE buyer_phone=? ORDER BY id DESC", (phone,)).fetchall() if phone else []
    return render_template('my_orders.html', deals=deals, phone=phone)

# ADMIN DASHBOARD - ALAG PAGE
@app.route('/admin', methods=['GET','POST'])
def admin():
    db = get_db()
    is_admin = request.args.get('password') == ADMIN_PASSWORD or request.form.get('password') == ADMIN_PASSWORD
    if not is_admin:
        return render_template('admin_login.html')
    deals = db.execute("SELECT * FROM deals ORDER BY id DESC").fetchall()
    total = db.execute("SELECT SUM(profit) FROM deals").fetchone()[0] or 0
    total_sale = db.execute("SELECT SUM(sale_price) FROM deals").fetchone()[0] or 0
    containers = db.execute("SELECT * FROM containers ORDER BY id DESC").fetchall()
    available = db.execute("SELECT COUNT(*) FROM containers WHERE status='available'").fetchone()[0]
    sold = db.execute("SELECT COUNT(*) FROM containers WHERE status='sold'").fetchone()[0]
    return render_template('admin.html', deals=deals, total=total, total_sale=total_sale, containers=containers, available=available, sold=sold)

# ADMIN DELETE
@app.route('/admin/delete/<int:cid>')
def delete_container(cid):
    if request.args.get('password')!= ADMIN_PASSWORD:
        return "Unauthorized"
    db = get_db()
    db.execute("DELETE FROM containers WHERE id=?", (cid,))
    db.commit()
    return redirect('/admin?password=admin123')

# SHORT LINKS FIX - Not Found khatam
@app.route('/commission')
def commission_alias():
    return redirect('/admin?password=admin123')

@app.route('/buying')
def buying_alias():
    return redirect('/')

@app.teardown_appcontext
def close(e):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
