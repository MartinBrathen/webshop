#!/usr/bin/env python
# coding: utf-8
from flask import Flask, render_template
app = Flask(__name__)

items = [
    {
        'name':u'mjukt bröd',
        'stock': 56,
        'desc':u'det här brödet är inte hårt'
    },
    {
        'name':u'hårt bröd',
        'stock': 999,
        'desc':u'det här brödet är hårt'
    },
    {
        'name':u'gammalt bröd',
        'stock': 1,
        'desc':u'köp på egen risk'
    }
]

@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', items=items)

@app.route("/register")
def register():
    return render_template('register.html', title='Ooh new member')

@app.route("/login")
def login():
    return render_template('login.html')


if __name__ == '__main__':
    app.run(debug = True)
