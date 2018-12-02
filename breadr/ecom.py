#!/usr/bin/env python
# coding: utf-8
from flask import Flask, render_template, url_for, request, redirect, flash, session
import mysql.connector

app = Flask(__name__)
app.secret_key = "0ul9oiewdsrukoiwsze" #generera säker nyckel

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
    #passwd="D0018Epass",
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
    PRIMARY KEY (userID,productID),
    FOREIGN KEY (userID) REFERENCES Users(ID),
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
    comment varchar(256),
    userID int,
    productID int,
    ID int AUTO_INCREMENT,
    tStamp TIMESTAMP DEFAULT current_timestamp,
    PRIMARY KEY (ID),
    FOREIGN KEY (userID) REFERENCES Users(ID),
    FOREIGN KEY (productID) REFERENCES Products(ID)
);""")

@app.route("/")
@app.route("/home")
def home():
    c.execute("""select * from Products where discontinued = 0;""")
    items = []
    keys = ('pName', 'stock', 'price', 'descr', 'pic', 'discontinued', 'ID')
    for fitem in c.fetchall():
        items.append(dict(zip(keys, fitem)))
    return render_template('home.html', items=items)


@app.route("/register", methods=['GET','POST'])
def register():
    if 'id' in session:
        flash('you already have an account', 'danger')
        return redirect(url_for('home'))
    
    if request.method =='POST':
        f = request.form
        c.execute("select * from Users where email = %s;", (f['email'],))
        if c.fetchone():
            return render_template('register.html', error="email already taken")
        sql = "insert into Users (email, pWord, admin) values (%s, %s, %s);"
        val = (f['email'], f['pass'], 1 if f['email'] == 'admin@admin.admin' else 0)
        c.execute(sql, val)
        db.commit()                   
        flash('User successfully created! customer id: {}'.format(c.lastrowid), 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html', title='Ooh new member')



@app.route("/login", methods=['GET','POST'])
def login():
    if 'ID' in session:
        flash('you are already logged in', 'danger')
        return redirect(url_for('home'))
        
    elif request.method == 'POST':
        femail = request.form['email']
        fpassw = request.form['pass']
        sql = "select pWord, ID, admin from Users where email = %s;"
        c.execute(sql, (femail,))
        
        result = c.fetchone()#gör solution med dict
        print(result)
        if result:
            if result[0] == fpassw:             
                session['admin'] = result[2]
                flash('Successfully logged in{}'.format(' as admin' if result[2] == 1 else ''), 'success')
                session['ID'] = result[1]

                
                return redirect(url_for('home'))
                                
            else:
                return render_template('login.html', passwmsg='wrong password', email = femail)

        else:
            return render_template('login.html', emailmsg='wrong email')
        
        
        
    return render_template('login.html')




@app.route("/product/<int:productID>", methods=['GET', 'POST'])
def product(productID):
    sql = "select * from Products where ID=%s;"
    c.execute(sql, (productID,))
    product = c.fetchone()
    
    if product:
        keys = ('pName', 'stock', 'price', 'descr', 'pic', 'discontinued', 'ID')

        product=dict(zip(keys, product))
        tot_rating = 0
        my_rating = None
        userID = None
        if 'ID' in session:
            userID = session['ID']

        sql="select rating, userID from Ratings where productID = %s"
        c.execute(sql, (productID,))
        ratings = c.fetchall()
        for rating, ID in ratings:
            if rating != None:
                tot_rating += 2*rating-1
                
            if ID == userID:
                my_rating = rating

        getCommentData_sql = "select commentS, tStamp, email, Comments.ID from Comments, Users where Users.ID = Comments.userID and productID = %s order by tStamp desc;"
        c.execute(getCommentData_sql, (productID,))
        comments = []
        keys = ('commentS', 'tStamp', 'email', 'id')
        for comment in c.fetchall():
            comments.append(dict(zip(keys, comment)))

        if 'ID' in session:  
            if request.method == 'POST':
                vote_sql = """insert into Ratings (rating, userID, productID) values (%s, %s, %s) 
                    on duplicate key update rating = %s;""" 

                if 'up' in request.form:
                    #updoot code
                    my_rating = None if my_rating == 1 else 1
                    val=(1, session['ID'], productID, my_rating)
                    c.execute(vote_sql,val)
                    db.commit()
                    return redirect(url_for('product', productID=productID))

                elif 'down' in request.form:
                    #downdoot code
                    my_rating = None if my_rating == 0 else 0
                    val=(0, session['ID'], productID, my_rating)
                    c.execute(vote_sql,val)
                    db.commit()
                    return redirect(url_for('product', productID=productID))

                elif 'buy' in request.form:
                    #place in cart code
                    f = request.form
                    quantity = int(dict(f)['quantity'][0])
                    sql = """insert into Basket (userID, productID, amount) values (%s, %s, %s) 
                    on duplicate key update amount = amount + %s;"""
                    val = (session['ID'], productID, quantity, quantity)
                    c.execute(sql, val)
                    db.commit()
                    return redirect(url_for('product', productID=productID))

                elif 'comment' in request.form:
                    comment = request.form['comment']
                    sql = """insert into Comments (commentS, userID, productID) values (%s, %s, %s);"""
                    val = (comment, session['ID'], productID)
                    c.execute(sql, val)
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
                    c.execute(sql,val)
                    db.commit()
                    return redirect(url_for('product', productID=productID))
                
                elif 'delete' in request.form:
                    c.execute("""update Comments set commentS = "DELETED" where ID = %s;""", (request.form.get('comment_ID'),))
                    db.commit()
                    return redirect(url_for('product', productID=productID))

        return render_template('product.html', product=product, rating = tot_rating, my_rating = my_rating, comments = comments)
    else:
        return "{} is not a valid product ID".format(productID)

@app.route("/logout")
def logout():
    session.pop('ID', None)
    session.pop('admin', None)
    return redirect(url_for('home'))

@app.route("/addProduct", methods=['GET','POST'])
def addProduct():
    #endast admin får vara på denna sida
    if 'ID' in session and session['admin'] == 1:
        if request.method == 'POST':
            f = parseForm(request.form)
            sql = """insert into Products(pName, stock, price, descr, pic) values (%s, %s, %s, %s, %s);"""
            val = (f['pName'], f['stock'], f['price'], f['descr'], f['pic'])
            c.execute(sql, val)
            db.commit()
            
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
        c.execute(sql,(val,))
        
        keys = ('userID', 'amount', 'productID', 'productPrice', 'productName')
        for fitem in c.fetchall():
            grandTotal = grandTotal + fitem[1]*fitem[3]
            items.append(dict(zip(keys, fitem)))
    

      
        if request.method == 'POST':
            if 'update' in request.form:
                newAmount = request.form['amount']
                if int(newAmount) > 0:
                    c.execute("UPDATE Basket SET Basket.amount=%s WHERE Basket.userID=%s AND Basket.productID=%s;",(newAmount,session['ID'],request.form['update']))
                    db.commit()
                elif int(newAmount) <= 0:
                    c.execute("DELETE FROM Basket WHERE Basket.userID=%s AND Basket.productID=%s;",(session['ID'],request.form['update']))
                    db.commit()   
                return redirect(url_for('basket'))
            elif 'delete' in request.form:
                c.execute("DELETE FROM Basket WHERE Basket.userID=%s AND Basket.productID=%s;",(session['ID'],request.form['delete']))
                db.commit()
                return redirect(url_for('basket'))
            elif 'checkout' in request.form:
                return redirect(url_for('checkout'))
    
    return render_template('basket.html', items = items, grandTotal = grandTotal)

@app.route("/checkout", methods=['GET','POST',''])
def checkout():

    grandTotal = 0
    items = []
    sufficientInfo = False
    if 'ID' in session:
        val = session['ID']
        
        sql = """SELECT Basket.userID, Basket.amount, Products.ID, Products.price, Products.pName FROM Basket INNER JOIN Products ON Basket.productID=Products.ID WHERE Basket.userID = %s;"""
        c.execute(sql,(val,))
        
        keys = ('userID', 'amount', 'productID', 'productPrice', 'productName')
        for fitem in c.fetchall():
            grandTotal = grandTotal + fitem[1]*fitem[3]
            items.append(dict(zip(keys, fitem)))

        sql = """SELECT Users.fName, Users.lName, Users.adress, Users.country, Users.phone, Users.email FROM Users WHERE ID = %s"""
        c.execute(sql,(val,))
        keys = ('userFName', 'userLName', 'userAdress', 'userCountry', 'userPhone', 'userEmail')
        user = (dict(zip(keys,c.fetchone())))
        if (user.get('userFName') and user.get('userLName') and user.get('userAdress') and user.get('userCountry') and user.get('userEmail')):
            sufficientInfo = True

        if request.method == 'POST':
            print(request.form)
            if 'order' in request.form:
                c.execute("INSERT INTO Orders (id, orderDate,userID) VALUES (NULL,CURRENT_DATE,%s);",(session['ID'],))
                db.commit()
                c.execute("SELECT LAST_INSERT_ID()")
                orderID = c.fetchone()
                print('hej')
                for item in items:
                    cost = int(item.get('productPrice'))*int(item.get('amount'))
                    print(cost)
                    print(item.get('productID'))
                    print(item.get('amount'))
                    print(orderID[0])
                    c.execute("INSERT INTO Transactions (productID,amount,orderID,cost) VALUES (%s,%s,%s,%s)",(item.get('productID'),item.get('amount'),orderID[0],cost))
                    db.commit()
                c.execute("DELETE FROM Basket WHERE Basket.userID=%s;",(session['ID'],))
                db.commit()
                flash('Order has been placed', 'danger')
                return redirect(url_for('home'))
            elif 'basket' in request.form:
                return redirect(url_for('basket'))
            elif 'account' in request.form:
                #return redirect(url_for('account'))
                print("not done")




    return render_template('checkout.html', items = items, grandTotal = grandTotal, user = user, sufficientInfo = sufficientInfo)




#returns a werkzeug.MultiDict where values of 'NULL' 'None' '' are actually None.
#use when you want sql to recieve a null(nil None NULL) value instead of a string
def parseForm(form):
    c = form.copy()
    for key in c:
        if c.get(key) == 'None' or c.get(key) == 'NULL' or c.get(key) == '':
            c[key] = None
    return c
























if __name__ == '__main__':
    app.run(debug = True)

