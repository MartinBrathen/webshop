#!/usr/bin/env python
# coding: utf-8
from flask import Flask, render_template, url_for, request, redirect, flash, session
import mysql.connector
import requests
import random
import hashlib

app = Flask(__name__)
app.secret_key = "0ul9oiewdsrukoiwsze"  # generera säker nyckel

'''
db = mysql.connector.connect(
    host="130.240.200.70",
    port=51322,
    user="root",
    passwd="D0018Epassword",
    database="webshopDB"
)
'''
db = mysql.connector.connect(
    host="localhost",
    port=3306,
    user="root",
    passwd="D0018Epassword",
    database="webshopDB"
)

c = db.cursor()

c.execute("CREATE DATABASE IF NOT EXISTS webshopDB")

c.execute("""CREATE TABLE IF NOT EXISTS Users(
    fName varchar(32),
    lName varchar(32),
    email varchar(64) NOT NULL,
    pWord varchar(64) NOT NULL,
    adress varchar(64),
    country varchar(32),
    phone varchar(32),
    admin bit,
    ID int AUTO_INCREMENT,
    PRIMARY KEY (ID),
    UNIQUE (email)
);""")

c.execute("""CREATE TABLE IF NOT EXISTS Products(
    pName varchar(32),
    stock int,
    price int,
    descr varchar(255),
    pic varchar(255),
    discontinued bit DEFAULT 0,
    ID int AUTO_INCREMENT,
    PRIMARY KEY (ID)
);""")

c.execute("""CREATE TABLE IF NOT EXISTS Basket(
    userID int,
    productID int,
    amount int,
    CHECK (amount > 0),
    PRIMARY KEY (userID,productID),
    FOREIGN KEY (userID) REFERENCES Users(ID),
    FOREIGN KEY (productID) REFERENCES Products(ID)
);""")

c.execute("""CREATE TABLE IF NOT EXISTS Orders(
    id int auto_increment,
    orderStatus varchar(32) DEFAULT 'Pending',
    orderDate DATE,
    userID int,
    PRIMARY KEY (id),
    FOREIGN KEY (userID) REFERENCES Users(ID)
);""")

c.execute("""CREATE TABLE IF NOT EXISTS Transactions(
    productID int,
    amount int,
    id int auto_increment,
    orderID int,
    cost int,
    PRIMARY KEY (id),
    FOREIGN KEY (orderID) REFERENCES Orders(id),
    FOREIGN KEY (productID) REFERENCES Products(ID)
);""")

c.execute("""CREATE TABLE IF NOT EXISTS Ratings(
    rating bit,
    userID int,
    productID int,
    PRIMARY KEY(userID,productID),
    FOREIGN KEY (userID) REFERENCES Users(ID),
    FOREIGN KEY (productID) REFERENCES Products(ID)
);""")

c.execute("""CREATE TABLE IF NOT EXISTS Comments(
    commentS varchar(256),
    userID int,
    productID int,
    id int AUTO_INCREMENT,
    tStamp TIMESTAMP DEFAULT current_timestamp,
    PRIMARY KEY (ID),
    FOREIGN KEY (userID) REFERENCES Users(ID),
    FOREIGN KEY (productID) REFERENCES Products(ID)
);""")

c.close()


@app.route("/")
@app.route("/home", methods=['GET', 'POST'])
def home():
    limit = 100
    meme = requests.get('https://www.reddit.com/r/dankmemes/search.json?q=a&sort=new&restrict_sr=1&limit={}'.format(
        limit), headers={'User-agent': 'your bot 0.1'}).json()
    meme = meme['data']['children'][random.randrange(limit)]['data']
    product_name = ''
    discontinued = 0
    in_stock = 0
    print("request.method = {}".format(request.method))
    if request.method == 'GET':
        print(request.args)
        if request.args.get('discontinued') == 'on':
            discontinued = 1

        if request.args.get('in_stock') == 'on':
            in_stock = 1

        if request.args.get('product_name') != None:
            product_name = request.args.get('product_name')

    print(product_name, discontinued, in_stock)
    cur = db.cursor()
    cur.execute("""select * from Products where (discontinued = {} or discontinued = 0) and pName like '%{}%' and stock >= {};""".format(
        discontinued, product_name, in_stock))

    items = []
    keys = ('pName', 'stock', 'price', 'descr', 'pic', 'discontinued', 'ID')
    for fitem in cur.fetchall():
        items.append(dict(zip(keys, fitem)))
    cur.close()
    return render_template('home.html', items=items, query=request.args, meme=meme)


@app.route("/register", methods=['GET', 'POST'])
def register():
    if 'id' in session:
        flash('you already have an account', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        f = request.form
        if f['pass1'] != f['pass2']:
            return redirect(url_for('register', pass_msg="Passwords don't match", email=f['email']))
        db.reconnect()
        cur = db.cursor()
        cur.execute("select * from Users where email = %s;", (f['email'],))
        if cur.fetchone():
            return redirect(url_for('register', email_msg="email already taken"))
        sql = "insert into Users (email, pWord, admin) values (%s, %s, %s);"

        # sha224 hash of password
        pass1 = hashlib.sha224(f['pass1']).hexdigest()
        val = (f['email'], pass1, 1 if f['email']
               == 'admin@admin.admin' else 0)
        cur.execute(sql, val)
        db.commit()

        flash('User successfully created! customer id: {}'.format(
            cur.lastrowid), 'success')
        cur.close()
        return redirect(url_for('login', email=f['email']))
    msg = request.args
    return render_template('register.html', title='Ooh new member', msg=msg)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if 'ID' in session:
        flash('you are already logged in', 'danger')
        return redirect(url_for('home'))

    elif request.method == 'POST':
        femail = request.form['email']
        fpassw = hashlib.sha224(request.form['pass']).hexdigest()
        sql = "select pWord, ID, admin from Users where email = %s;"
        db.reconnect()
        cur = db.cursor()
        cur.execute(sql, (femail,))
        result = cur.fetchone()
        # email finns
        if result:
            result = dict(zip(('pass', 'ID', 'admin'), result))
            # password är rätt
            if result['pass'] == fpassw:
                session['admin'] = result['admin']
                flash('Successfully logged in{}'.format(
                    ' with admin privileges' if result['admin'] == 1 else ''), 'success')
                session['ID'] = result['ID']
                update_basket()
                return redirect(url_for('home'))
            # fel password
            else:
                return redirect(url_for('login', passw_msg='wrong password', email=femail))
        # fel email
        else:
            return redirect(url_for('login', email_msg='wrong email'))

    msg = request.args
    return render_template('login.html', msg=msg)


@app.route("/order_manager", methods=['GET', 'POST'])
def order_manager():
    if 'ID' in session and session['admin'] == 1:
        db.reconnect()
        if request.method == 'POST':
            form = request.form
            print(form)
            # update status
            if 'update' in form:
                cur = db.cursor()
                cur.execute("update Orders set orderStatus = %s where id = %s;", (form['status'], form['order_ID']))
                db.commit()
                cur.close()
                redirect(url_for('order_manager', **request.args))

        res = request.args
        print(res)
        sql_where=" where FALSE"
        if 'Pending' in res:
            sql_where += " or orderStatus = 'Pending'"

        if 'Shipped' in res:
            sql_where += " or orderStatus = 'Shipped'"
        
        if 'Processing' in res:
            sql_where += " or orderStatus = 'Processing'"

        if 'Completed' in res:
            sql_where += " or orderStatus = 'Completed'"
               


        sql = "select id, orderStatus, orderDate, userID from Orders" + sql_where + ";"
        cur = db.cursor()
        cur.execute(sql)
        orders = []
        order_keys=('id', 'orderStatus', 'orderDate', 'userID')
        for order in cur.fetchall():
            orders.append(dict(zip(order_keys, order)))
        cur.close()
        return render_template('order_manager.html', orders=orders, filtered = res)
    else:
        flash("Access denied! You need admin privileges to manage orders", 'danger')
        return redirect(url_for('home'))

@app.route("/order/<int:orderID>")
def order(orderID):
    order_keys=('id', 'orderStatus', 'orderDate', 'userID')
    db.reconnect()
    cur  = db.cursor()
    cur.execute("select id, orderStatus, orderDate, userID from Orders where id = %s;", (orderID,))
    order = cur.fetchone()
    cur.close()
    if order:
        order = dict(zip(order_keys, order))
        if 'ID' in session and (order.get('userID') == session['ID'] or session['admin'] == 1):
            # access granted ( to order user and admin)
            transaction_keys = 'productID', 'amount', 'cost'
            sql = """select productID, amount, cost 
            from Transactions 
            where orderID = %s;
            """
            val = (orderID,)
            cur = db.cursor()
            cur.execute(sql, val)
            transactions = []
            for transaction in cur.fetchall():
                transactions.append(dict(zip(transaction_keys, transaction)))
            cur.close()
            return render_template('order.html', order = order, transactions = transactions)
            
        else:
            # access denied
            flash("Access denied! This is not your order",'danger')
        return redirect(url_for('home'))
    else:
        # not a valid page
        flash("no order with id: {}, exists".format(orderID),'danger')
        return redirect(url_for('home'))
    



@app.route("/product/<int:productID>", methods=['GET', 'POST'])
def product(productID):
    sql = "select * from Products where ID=%s;"
    db.reconnect()
    cur = db.cursor()
    cur.execute(sql, (productID,))
    product = cur.fetchone()
    cur.close()
	
    if product:
        keys = ('pName', 'stock', 'price', 'descr', 'pic', 'discontinued', 'ID')

        product=dict(zip(keys, product))
        tot_rating = 0
        my_rating = None
        userID = None
        if 'ID' in session:
            userID = session['ID']

        sql="select rating, userID from Ratings where productID = %s"
        cur = db.cursor()
        cur.execute(sql, (productID,))
        ratings = cur.fetchall()
        cur.close()
        for rating, ID in ratings:
            if rating != None:
                tot_rating += 2*rating-1
                
            if ID == userID:
                my_rating = rating

        getCommentData_sql = "select commentS, tStamp, email, Comments.ID from Comments, Users where Users.ID = Comments.userID and productID = %s order by tStamp desc;"
        cur = db.cursor()
        cur.execute(getCommentData_sql, (productID,))
        comments = []
        keys = ('commentS', 'tStamp', 'email', 'id')
        for comment in cur.fetchall():
            comments.append(dict(zip(keys, comment)))
        cur.close()
		
        if 'ID' in session:  
            if request.method == 'POST':
                vote_sql = """insert into Ratings (rating, userID, productID) values (%s, %s, %s) 
                    on duplicate key update rating = %s;""" 
                cur = db.cursor()
                if 'up' in request.form:
                    # updoot code
                    my_rating = None if my_rating == 1 else 1
                    val=(1, session['ID'], productID, my_rating)
                    cur.execute(vote_sql,val)
                    db.commit()
                    return redirect(url_for('product', productID=productID))

                elif 'down' in request.form:
                    # downdoot code
                    my_rating = None if my_rating == 0 else 0
                    val=(0, session['ID'], productID, my_rating)
                    cur.execute(vote_sql,val)
                    db.commit()
                    return redirect(url_for('product', productID=productID))

                elif 'buy' in request.form:
                    # place in cart code
                    f = request.form
                    quantity = int(dict(f)['quantity'][0])
                    if quantity != 0:
                        sql = """insert into Basket (userID, productID, amount) values (%s, %s, %s) 
                        on duplicate key update amount = amount + %s;"""
                        val = (session['ID'], productID, quantity, quantity)
                        cur.execute(sql, val)
                        db.commit()
                        update_basket()
                        flash("{} {} items to the basket".format('added' if quantity > 0 else 'removed', abs(quantity)), 'success')
                    return redirect(url_for('product', productID=productID))

                elif 'comment' in request.form:
                    comment = request.form['comment']
                    sql = """insert into Comments (commentS, userID, productID) values (%s, %s, %s);"""
                    val = (comment, session['ID'], productID)
                    cur.execute(sql, val)
                    db.commit()
                    return redirect(url_for('product', productID=productID))

                elif 'edit' in request.form:
                    res = parseForm(request.form)
                    print(res.get("discontinued"))
                    sql="""update Products
                    set pName = %s,
                    stock = %s,
                    price = %s,
                    descr = %s,
                    pic = %s,
                    discontinued = %s
                    where ID = %s;"""
                    val = (res['name'], res['stock'], res['price'], res['description'], res['pic'], 0 if res.get('discontinued') ==  None else 1, productID)
                    cur.execute(sql,val)
                    db.commit()
                    flash("Changes committed!", 'success')
                    return redirect(url_for('product', productID=productID))
                
                elif 'delete' in request.form:
                    cur.execute("""update Comments set commentS = "DELETED" where ID = %s;""", (request.form.get('comment_ID'),))
                    db.commit()
                    return redirect(url_for('product', productID=productID))
                cur.close()
        return render_template('product.html', product=product, rating = tot_rating, my_rating = my_rating, comments = comments)
    else:
        return "{} is not a valid product ID".format(productID)

@app.route("/logout")
def logout():
    if 'ID' in session:
        session.pop('ID', None)
        session.pop('admin', None)
        flash("You are now logged out", 'success')
    else:
        flash("You are already logged out", 'warning')
    return redirect(url_for('home'))

@app.route("/addProduct", methods=['GET','POST'])
def addProduct():
    # endast admin får vara på denna sida
    if 'ID' in session and session['admin'] == 1:
        if request.method == 'POST':
            f = parseForm(request.form)
            sql = """insert into Products(pName, stock, price, descr, pic) values (%s, %s, %s, %s, %s);"""
            val = (f['pName'], f['stock'], f['price'], f['descr'], f['pic'])
            db.reconnect()
            cur = db.cursor()
            cur.execute(sql, val)
            db.commit()
            cur.close()
            flash("New product '{}' added, you can edit data on product page".format(f['pName']), 'success')
            return redirect('addProduct')
            
        return render_template('addProduct.html')
    else:
        flash('you do not have access to that page', 'danger')
        return redirect(url_for('home'))

@app.route("/basket", methods=['GET','POST'])
def basket():
    grandTotal = 0
    items = []
    if 'ID' in session:
        val = session['ID']
        
        sql = """SELECT Basket.userID, Basket.amount, Products.ID, Products.price, Products.pName FROM Basket INNER JOIN Products ON Basket.productID=Products.ID WHERE Basket.userID = %s;"""
        db.reconnect()
        cur  = db.cursor()
        cur.execute(sql,(val,))
        
        keys = ('userID', 'amount', 'productID', 'productPrice', 'productName')
        for fitem in cur.fetchall():
            grandTotal = grandTotal + fitem[1]*fitem[3]
            items.append(dict(zip(keys, fitem)))
        cur.close()

      
        if request.method == 'POST':
            cur = db.cursor()
            if 'update' in request.form:
                newAmount = request.form['amount']
                
                cur.execute("""SELECT Products.stock FROM Products WHERE Products.ID=%s""", (request.form['update'],))
                inStock=cur.fetchone()[0]
                if int(inStock) >= int(newAmount) > 0:
                    cur.execute("UPDATE Basket SET Basket.amount=%s WHERE Basket.userID=%s AND Basket.productID=%s;",(newAmount, session['ID'], request.form['update']))
                    db.commit()
                elif int(newAmount) <= 0:
                    cur.execute("DELETE FROM Basket WHERE Basket.userID=%s AND Basket.productID=%s;",(session['ID'],request.form['update']))
                    db.commit()  
                update_basket()
                cur.close()
                return redirect(url_for('basket'))
            elif 'delete' in request.form:
                cur.execute("DELETE FROM Basket WHERE Basket.userID=%s AND Basket.productID=%s;",(session['ID'],request.form['delete']))
                db.commit()
                update_basket()
                cur.close()
                return redirect(url_for('basket'))
            elif 'checkout' in request.form:
                cur.close()
                return redirect(url_for('checkout'))
            cur.close()
			
    return render_template('basket.html', items = items, grandTotal = grandTotal)

@app.route("/checkout", methods=['GET','POST',''])
def checkout():

    grandTotal = 0
    totalAmount = 0
    items = []
    sufficientInfo = False
    if 'ID' in session:
        idTuple = (session['ID'],)

        sql = """SELECT sum(Basket.amount*Products.price),sum(Basket.amount) FROM Basket INNER JOIN Products ON Basket.productID=Products.ID WHERE Basket.userID = %s;"""
        db.reconnect()
        cur = db.cursor()
        cur.execute(sql,idTuple)
        tmp = cur.fetchone()
        print("first test")

        cur.close()

        if not tmp[1]:
            flash('You have no items in cart', 'danger')
            return redirect(url_for('basket'))
        print('first and a half')

        grandTotal = tmp[0]
        totalAmount = tmp[1]

        sql = """SELECT sum(Basket.amount) FROM Basket INNER JOIN Products ON Basket.productID=Products.ID WHERE Basket.userID = %s AND Basket.amount > Products.stock;"""
        cur = db.cursor()
        cur.execute(sql,idTuple)
        print('do i get this far?')
        tmp = cur.fetchone()[0]
        cur.close()

        print('second test')
		
        if tmp:
            flash('Quantity of one of more items exceed our current stock for said item', 'danger')
            return redirect(url_for('basket'))

        print('third test')

        sql = """SELECT Users.fName, Users.lName, Users.adress, Users.country, Users.phone, Users.email FROM Users WHERE ID = %s"""
        cur = db.cursor()
        cur.execute(sql,idTuple)
        keys = ('userFName', 'userLName', 'userAdress', 'userCountry', 'userPhone', 'userEmail')
        user = (dict(zip(keys,cur.fetchone())))
        cur.close()
        if (user.get('userFName') and user.get('userLName') and user.get('userAdress') and user.get('userCountry') and user.get('userEmail')):
            sufficientInfo = True

        if request.method == 'POST':
            db.reconnect()
            if 'order' in request.form and totalAmount > 0:


                sql = """SELECT sum(Basket.amount) FROM Basket INNER JOIN Products ON Basket.productID=Products.ID WHERE Basket.userID = %s AND Basket.amount > Products.stock;"""
                cur = db.cursor()
                cur.execute(sql,idTuple)
                tmp = cur.fetchone()[0]
				
                if tmp:
                    flash('Quantity of one of more items exceed our current stock for said item', 'danger')
                    return redirect(url_for('basket'))

                cur.execute("INSERT INTO Orders (id, orderDate,userID) VALUES (NULL,CURRENT_DATE,%s);",(session['ID'],))
                cur.execute("SELECT LAST_INSERT_ID()")
                orderID = cur.fetchone()[0]

                sql = """SELECT Basket.amount, Products.ID, Products.price, Products.stock FROM Basket INNER JOIN Products 
                ON Basket.productID=Products.ID WHERE Basket.userID = %s;"""
                cur.execute(sql,idTuple)
                items = cur.fetchall()
                for item in items:
                    cost = int(item[2])*int(item[0])
                    cur.execute("""INSERT INTO Transactions (productID,amount,orderID,cost) VALUES (%s,%s,%s,%s)""",(item[1],item[0],orderID,cost))
                    newStock = int(item[3]) - int(item[0])
                    cur.execute("""UPDATE Products SET Products.stock = %s WHERE Products.ID = %s""",(newStock,item[1]))


                cur.execute("DELETE FROM Basket WHERE Basket.userID=%s;",(session['ID'],))
                db.commit()
                cur.close()
                flash('Order has been placed', 'success')
                update_basket()
                return redirect(url_for('home'))
            elif 'basket' in request.form:
                return redirect(url_for('basket'))
            elif 'account' in request.form:
                # return redirect(url_for('account'))
                print("not done")




    return render_template('checkout.html', grandTotal = grandTotal, user = user, sufficientInfo = sufficientInfo)

@app.route("/add_admin", methods=['GET','POST'])
def add_admin():
    # endast admin får vara på denna sida
    if 'ID' in session and session['admin'] == 1:

        if request.method == 'POST':
            f = parseForm(request.form)
            sql = """select email, admin, ID from Users where email = %s;"""
            val = (f.get('email'),)
            cur = db.cursor()
            cur.execute(sql, val)
            res = cur.fetchone()
            cur.close()
            if res:
                res = dict(zip(('email', 'admin', 'ID'), res))
                if res.get('ID') == session['ID']:
                    return redirect(url_for('add_admin', email_msg="you cant remove your own privilege"))
                admin = 1 if (res.get('admin') == 0 or res.get('admin') == None) else 0
                sql = """update Users set admin = %s where email = %s;"""
                cur = db.cursor()
                cur.execute(sql, (admin, res.get('email')))
                db.commit()
                cur.close()
                flash("Admin privilege {} user with email: {}".format("given to" if admin == 1 else "removed from", f.get('email')), 'success')
                return redirect('add_admin')
            else:
                print("det fanns inte")
                return redirect(url_for('add_admin', email_msg="no such email found"))
			
			
            return redirect('add_admin')
        msg = request.args
        print("msg: {}".format(msg))
        return render_template('add_admin.html', msg = msg)
    else:
        flash('you do not have access to that page', 'danger')
        return redirect(url_for('home'))


# returns a werkzeug.MultiDict where values of 'NULL' 'None' '' are actually None.
# use when you want sql to recieve a null(nil None NULL) value instead of a string
# maybe add so strings of numbers become ints; SQL autocasts strings to int
def parseForm(form):
    c = form.copy()
    for key in c:
        if c.get(key) == 'None' or c.get(key) == 'NULL' or c.get(key) == '':
            c[key] = None
    return c

def update_basket(userID = None):
    if userID == None:
        userID = session['ID']
    sql = """select amount from Basket where userID = %s"""
    cur = db.cursor()
    cur.execute(sql, (userID,))
    total_in_basket = 0
    for amount in cur.fetchall():
        total_in_basket += amount[0]
    cur.close()
    session['basket'] = total_in_basket
























if __name__ == '__main__':
    app.run(debug = True)

