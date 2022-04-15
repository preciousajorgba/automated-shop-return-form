from flask import Flask, render_template, request, make_response
app = Flask(__name__)

import sqlite3
import print_return 
import random


db = sqlite3.connect('finaldb')
cursor = db.cursor()
for table in ['customers', 'products', 'orders',
        'products_ordered', 'returns', 'products_returned',
        'return_reasons']:
    cursor.execute('DROP TABLE if exists %s' % table)
    db.commit()

cursor.execute('''
        CREATE TABLE customers(id INTEGER PRIMARY KEY,
                               name TEXT,
                               address TEXT,
                               zipcode TEXT,
                               city TEXT)''')
cursor.execute('''
        CREATE TABLE products(id INTEGER PRIMARY KEY,
                               name TEXT,
                               size TEXT)''')
cursor.execute('''
        CREATE TABLE orders(id INTEGER PRIMARY KEY,
                               date DATE,
                               customer_id INTEGER,
                               FOREIGN KEY(customer_id) REFERENCES customers(id))''')
cursor.execute('''
        CREATE TABLE products_ordered(id INTEGER PRIMARY KEY,
                               order_id INTEGER,
                               product_id INTEGER,
                               FOREIGN KEY(order_id) REFERENCES orders(id),
                               FOREIGN KEY(product_id) REFERENCES products(id))''')
cursor.execute('''
        CREATE TABLE returns(id INTEGER PRIMARY KEY,
                               order_id INTEGER UNIQUE,
                               FOREIGN KEY(order_id) REFERENCES orders(id))''')
cursor.execute('''
        CREATE TABLE return_reasons(id INTEGER PRIMARY KEY,
                               description TEXT)''')
for description in ['Too large', 'Too small', 'Not as expected', 'Other']:
    cursor.execute('INSERT INTO return_reasons(description) VALUES(?)',
            (description, ))
cursor.execute('''
        CREATE TABLE products_returned(id INTEGER PRIMARY KEY,
                               return_id INTEGER,
                               return_reason_id INTEGER,
                               product_order_id INTEGER,
                               FOREIGN KEY(product_order_id) REFERENCES products_ordered(id),
                               FOREIGN KEY(return_id) REFERENCES returns(id),
                               FOREIGN KEY(return_reason_id) REFERENCES return_reasons(id))''')
db.commit()

for i in range(100):
    color = random.choice(['Red', 'Green', 'Blue', 'Yellow', 'Black', 'White', 'Orange'])
    gender = random.choice(["Men's", "Women's"])
    clothing = random.choice(['Jeans', 'Shirt', 'T-Shirt', 'Cardigan', 'Skirt', 'Dress', 'Belt'])
    name = '%s %s %s' % (color, gender, clothing)
    sizes = random.choice([['S', 'M', 'L', 'XL'], ['36', '38', '40', '42']])
    for size in sizes:
        cursor.execute('INSERT INTO products(name, size) VALUES(?, ?)',
                (name, size))

cursor.execute('SELECT id FROM products')
all_product_ids = cursor.fetchall()
all_product_ids = [x for (x,) in all_product_ids]

cursor.execute('SELECT count(*) from return_reasons')
num_return_reasons = cursor.fetchone()[0]
assert num_return_reasons > 0

for i in range(10):
    first_name = random.choice(['Bright', 'Jane', 'Ade', 'Nnenna', 'Kant', 'Precious', 'Leah'])
    surname = random.choice(['Ajorgba', 'Obi', 'Balogun', 'Ahmed', 'Bedi'])
    name = '%s %s' % (first_name, surname)
    housenr = random.randint(1, 8000)
    street_name = random.choice(['Biobaku', 'Elkanemi',
        'Mariere', 'Shodeinde', 'Jaja', 'Amina', 'Nsukara',
        'Sofoluwe', '34', 'Alabado'])
    road = random.choice(['Road', 'Street', 'Avenue', 'Lane', 'Parkway'])
    zipcode = random.randint(10000, 99999)
    city = random.choice(['Yaba', 'Alimosho', 'Akoka'])
    address = '%s %s %s' % (housenr, street_name, road)

    cursor.execute('INSERT INTO customers(name, address, zipcode, city) VALUES(?, ?, ?, ?)',
            (name, address, zipcode, city))
    customer_id = cursor.lastrowid

    # each customer has between 2 and 50 orders
    for i in range(random.randint(2, 50)):
        year = random.choice([2015, 2016, 2017, 2018])
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        date = "%04d-%02d-%02d" % (year, month, day)
        cursor.execute('INSERT INTO orders(date, customer_id) VALUES(?, ?)',
                (date, customer_id))
        order_id = cursor.lastrowid
        product_order_ids = list()
        num_products_ordered = random.randint(2, 7)

        # each order has between 2 and 7 products
        for j in range(num_products_ordered):
            product_id = random.choice(all_product_ids)
            cursor.execute('INSERT INTO products_ordered(order_id, product_id) VALUES(?, ?)',
                    (order_id, product_id))
            product_order_ids.append(cursor.lastrowid)
        random.shuffle(product_order_ids)

        # each order may have some returns
        return_id = None
        for j in range(random.randint(0, num_products_ordered)):
            if not return_id:
                cursor.execute('INSERT INTO returns(order_id) VALUES (?)',
                        (order_id, ))
                return_id = cursor.lastrowid
            product_order_id = product_order_ids.pop()
            return_reason_id = random.randint(1, num_return_reasons)
            cursor.execute('''INSERT INTO products_returned(
                        return_id, return_reason_id, product_order_id) VALUES (?, ?, ?)''',
                        (return_id, return_reason_id, product_order_id))

db.commit()




def make_customer(p):
    return {'id':p[0],'name': p[1], 'address': p[2], 'zip':p[3], 'city':p[4]}

def make_product(p):
    if len(p) > 3:
        return {'id': p[0], 'name': p[1], 'size': p[2], 'product_order_id': p[3]}
    else:
        return {'id': p[0], 'name': p[1], 'size': p[2]}

def make_order(p):
    return {'id': p[0], 'date': p[1], 'customer_id': p[2]}

def make_reason(p):
    return {'id': p[0], 'description': p[1]}

def get_order_products(order_id):
    db = sqlite3.connect('finaldb')
    cursor = db.cursor()

    cursor.execute('''SELECT     products.id, products.name, products.size, products_ordered.id
                      FROM       products
                      INNER JOIN products_ordered ON products_ordered.product_id = products.id
                      INNER JOIN orders           ON orders.id                   = products_ordered.order_id
                      WHERE      orders.id = ?''', (order_id, ))
    product_list = cursor.fetchall()
    return [make_product(o) for o in product_list]

@app.route("/",methods=['GET','POST'])
def customers():
    db = sqlite3.connect('finaldb')
    cursor = db.cursor()

    cursor.execute('''SELECT   * FROM customers''')
    customer_list = cursor.fetchall()
    customer_list = [make_customer(p) for p in customer_list]
    return render_template('customers.html', customer_list=customer_list)    

@app.route("/products/", methods=['GET'])
def products():
    db = sqlite3.connect('finaldb')
    cursor = db.cursor()

    cursor.execute('''SELECT   * FROM products''')
    product_list = cursor.fetchall()
    product_list = [make_product(p) for p in product_list]
    return render_template('products.html', product_list=product_list)

@app.route("/orders.html", methods=['POST'])
def orders():
    db = sqlite3.connect('finaldb')
    cursor = db.cursor()
    the_id=request.form['customer_id']
    customer_id = request.args.get('customer_id', the_id)
    cursor.execute('''SELECT     *
                      FROM       orders
                      INNER JOIN customers ON customers.id = orders.customer_id
                      WHERE      customers.id = ?''', (customer_id, ))
    order_list = cursor.fetchall()
    order_list = [make_order(o) for o in order_list]
    return render_template('orders.html', order_list=order_list, customer_id=customer_id)

@app.route("/order/", methods=['GET'])
def order():
    db = sqlite3.connect('finaldb')
    cursor = db.cursor()

    order_id = request.args.get('order_id', 1)
    product_list = get_order_products(order_id)
    return render_template('order.html', product_list=product_list, order_id=order_id)

@app.route("/return.html", methods=['GET'])
def return_get_reason():
    db = sqlite3.connect('finaldb')
    cursor = db.cursor()

    order_id = request.args.get('order_id')
    product_list = get_order_products(order_id)
    product_list = [p for p in product_list if request.args.get(str(p['id']))]
    cursor.execute('''SELECT * FROM return_reasons''')
    reason_list = cursor.fetchall()
    reason_list = [make_reason(o) for o in reason_list]
    reason_list[0]['default'] = True
    return render_template('return.html', product_list=product_list, reason_list=reason_list, order_id=order_id)

@app.route("/print.html", methods=['POST'])
def return_print():
    # build database input
    db = sqlite3.connect('finaldb')
    cursor = db.cursor()

    order_id = request.form['order_id']
    product_list = get_order_products(order_id)
    product_list = [p for p in product_list if request.form.get(str(p['id']))]
    reasons = list()
    for p in product_list:
        reason = request.form.get(str(p['id']), 4)
        reasons.append(reason)
    product_list = zip(product_list, reasons)

    # update database
    cursor.execute('INSERT OR IGNORE INTO returns(order_id) VALUES (?)',
            (order_id, ))
    cursor.execute('SELECT id FROM returns WHERE order_id = ?', (order_id, ))
    return_id = cursor.fetchone()[0]
    cursor.execute('DELETE FROM products_returned WHERE return_id = ?', (return_id, ))
    for p, r in product_list:
        product_order_id = p['product_order_id']
        cursor.execute('''INSERT INTO products_returned(
                    return_id, return_reason_id, product_order_id) VALUES (?, ?, ?)''',
                    (return_id, r, product_order_id))
    db.commit()

    # generate and send pdf
    pdf = print_return.generate_label(return_id)
    binary_stream = pdf.output('','S').encode('latin-1')
    response = make_response(binary_stream)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=return.pdf'
    return response

db.close()