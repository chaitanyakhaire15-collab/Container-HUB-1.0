from flask import Flask, render_template, request, redirect, g
import sqlite3, os

app = Flask(__name__, template_folder='tamplates')
DB = 'hub.db'

# TUMHARA PAISA YAHAN AYEGA
RAZORPAY_KEY_ID = "rzp_test_xxxxxx" # Yaha apna Key ID daalo
MY_UPI_ID = "your-upi@paytm" # Backup ke liye

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB)
        db.execute('''CREATE TABLE IF NOT EXISTS containers
        (id INTEGER PRIMARY KEY, title TEXT, city TEXT, size TEXT, type TEXT, price INTEGER, photo TEXT, phone TEXT, status TEXT)''')
        db.execute('''CREATE TABLE IF NOT EXISTS deals
        (id INTEGER PRIMARY KEY, container_id INTEGER, buyer_name TEXT, buyer_phone TEXT, sale_price INTEGER, token INTEGER, status TEXT)''')
        if db.execute('SELECT COUNT(*) FROM containers').fetchone()[0] == 0:
            db.execute("INSERT INTO containers (title,city,size,type,price,photo,phone,status) VALUES (?,?,?,?,?,?,?,?)",
            ("20ft Container Bhiwandi","Bhiwandi","20ft","Dry",80000,"https://images.unsplash.com/photo-1494412574643-ff11b0a5c1c3","9000000001","available"))
            db.commit()
    return db

@app.route('/')
def home():
    db = get_db()
    q = request.args.get('q','')
    cons = db.execute("SELECT * FROM containers WHERE status='available' AND (title LIKE? OR city LIKE?)", (f'%{q}%',f'%{q}%')).fetchall() if q else db.execute("SELECT * FROM containers WHERE status='available'").fetchall()
    return render_template('index.html', containers=cons)

@app.route('/detail/<int:cid>')
def detail(cid):
    db = get_db()
    c = db.execute("SELECT * FROM containers WHERE id=?", (cid,)).fetchone()
    return render_template('detail.html', c=c, razorpay_key=RAZORPAY_KEY_ID)

@app.route('/pay/<int:cid>', methods=['POST'])
def pay(cid):
    db = get_db()
    c = db.execute("SELECT * FROM containers WHERE id=?", (cid,)).fetchone()
    name = request.form.get('buyer_name')
    phone = request.form.get('buyer_phone')
    price = int(c[5])
    token = int(price * 0.05) # 5% tumhara commission

    db.execute("INSERT INTO deals (container_id,buyer_name,buyer_phone,sale_price,token,status) VALUES (?,?,?,?,?,?)",
    (cid,name,phone,price,token,'paid'))
    db.execute("UPDATE containers SET status='sold' WHERE id=?", (cid,))
    db.commit()
    return redirect(f'/my-orders?phone={phone}&success=1')

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

@app.route('/my-orders')
def my_orders():
    db = get_db()
    phone = request.args.get('phone','')
    deals = db.execute("SELECT * FROM deals WHERE buyer_phone=? ORDER BY id DESC", (phone,)).fetchall() if phone else []
    return render_template('my_orders.html', deals=deals, phone=phone)

# Admin routes DELETED

@app.teardown_appcontext
def close(e):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
