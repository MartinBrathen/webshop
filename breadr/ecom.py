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
    passwd="D0018Epass",
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
    ID int AUTO_INCREMENT,
    PRIMARY KEY (ID)
);""")

'''
items = [
    {
        'pName':u'mjukt bröd',
        'stock': 56,
        'desc':u'det här brödet är inte hårt',
        'ID':1
    },
    {
        'pName':u'hårt bröd',
        'stock': 999,
        'desc':u'det här brödet är hårt',
        'ID':2
    },
    {
        'pName':u'gammalt bröd',
        'stock': 1,
        'desc':u'köp på egen risk',
        'ID':3
    }
]
'''

@app.route("/")
@app.route("/home")
def home():
    c.execute("""select * from Products;""")
    items = []
    keys = ('pName', 'stock', 'price', 'descr', 'pic', 'ID')
    for fitem in c.fetchall():
        items.append(dict(zip(keys, fitem)))
    print(items)
    return render_template('home.html', items=items)


@app.route("/register", methods=['GET','POST'])
def register():
    if 'id' in session:
        flash('you already have an account', 'danger')
        return redirect(url_for('home'))
    
    if request.method =='POST':
        f = request.form
        sql = "insert into Users (email, pWord, admin) values (%s, %s, %s);"
        val = (f['email'], f['pass'], 1 if f['email'] == 'admin@admin.admin' else 0)
        try:
            c.execute(sql, val)
            db.commit()
            
        except mysql.connector.Error as err:
            return render_template('register.html', error=err)#SKICKA INTE ERR UTAN ETT BÄTTRE MEDDELANDE
                      
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
        print("result: {}".format(result))
        if result:
            if result[0] == fpassw:             
                session['admin'] = result[2]
                flash('Successfully logged in{}'.format(' as admin' if result[2] == 1 else ''), 'success')
                session['ID'] = result[1]
                print("admin: {}, id: {}".format(session['admin'], session['ID']))
                
                return redirect(url_for('home'))
                                
            else:
                return render_template('login.html', passwmsg='wrong password', email = femail)

        else:
            return render_template('login.html', emailmsg='wrong email')
        
        
        
    return render_template('login.html')




@app.route("/product/<int:productID>")
def product(productID):
    '''
    for item in items:
        if item['ID'] == productID:
            return render_template('product.html', product=item)
    '''
    sql = "select * from Products where ID=%s;"
    c.execute(sql, (productID,))
    result = c.fetchone()
    if result:
        keys = ('pName', 'stock', 'price', 'descr', 'pic', 'ID')
        return render_template('product.html', product=dict(zip(keys, result)))
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

            f = request.form
            print(f)
            targets = ()
            entrys = ()
            val = ()
            for info in f:
                if f[info] != '':
                    targets += (info,)
                    entrys += ('%s',)
                    if info == 'price' or info == 'stock':
                        val += (int(f[info]),)
                    else:
                        val += (f[info],)
            sql = "insert into Products {} values {};".format(targets, entrys).replace("'", "")
            print(sql)
            print(val)
            c.execute(sql, val)
            db.commit()
            
        return render_template('addProduct.html')
    else:
        flash('you do not have access to that page', 'danger')
        return redirect(url_for('home'))



























if __name__ == '__main__':
    app.run(debug = True)

