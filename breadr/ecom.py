#!/usr/bin/env python
# coding: utf-8
from flask import Flask, render_template, url_for, request, redirect, flash, session
import mysql.connector

app = Flask(__name__)
app.secret_key = "0ul9oiewdsrukoiwsze"

'''
db = mysql.connector.connect(
    host="130.240.200.70",
    port="51322",
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


items = [
    {
        'name':u'mjukt bröd',
        'stock': 56,
        'desc':u'det här brödet är inte hårt',
        'ID':1
    },
    {
        'name':u'hårt bröd',
        'stock': 999,
        'desc':u'det här brödet är hårt',
        'ID':2
    },
    {
        'name':u'gammalt bröd',
        'stock': 1,
        'desc':u'köp på egen risk',
        'ID':3
    }
]

@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', items=items)

@app.route("/register", methods=['GET','POST'])
def register():
    if 'id' in session:
        return redirect(url_for('home'))
    
    if request.method =='POST':
        f = request.form
        sql = "insert into users (email, pWord) values (%s, %s);"
        val = (f['email'], f['pass'])
        try:
            print(sql, val)
            c.execute(sql, val)
            db.commit()
            
        except mysql.connector.Error as err:
            return render_template('register.html', error=err)#SKICKA INTE ERR UTAN ETT BÄTTRE MEDDELANDE
                      
        flash('User successfully created! customer id: {}'.format(c.lastrowid))
        return redirect(url_for('login'))
        
    return render_template('register.html', title='Ooh new member')



@app.route("/login", methods=['GET','POST'])
def login():
    if 'id' in session:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        femail = request.form['email']
        fpassw = request.form['pass']
        sql = "select pWord, ID from users where email = %s;"
        c.execute(sql, (femail,))
        
        result = c.fetchone()
        if result:
            if result[0] == fpassw:
                flash('Successfully logged in')
                session['ID'] = result[1]
                return redirect(url_for('home'))
                                
            else:
                return render_template('login.html', passwmsg='wrong password')

        else:
            return render_template('login.html', emailwmsg='wrong email')
        
        
        
    return render_template('login.html')




@app.route("/product/<int:productID>")
def product(productID):
    for item in items:
        if item['ID'] == productID:
            return render_template('product.html', product=item)
    return "{} is not a valid product ID".format(productID)

@app.route("/logout")
def logout():
    session.pop('ID', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug = True)

