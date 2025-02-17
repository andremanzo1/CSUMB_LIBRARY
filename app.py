from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import MySQLdb.cursors
import re
from flask_bootstrap import Bootstrap5
import os
import requests
app = Flask(__name__)
bootstrap = Bootstrap5(app)
books = [] 
app.secret_key = 'ITS_MINE'
 
app.config['MYSQL_HOST'] = os.getenv('SQLHOST')
app.config['MYSQL_USER'] = os.getenv('SQLUSER')
app.config['MYSQL_PASSWORD'] = os.getenv('SQLPASSWORD')
app.config['MYSQL_DB'] = os.getenv('SQLDB')
 
mysql = MySQL(app)
 
@app.route('/')
@app.route("/login", methods=["GET", "POST"])
def login():
    message = ""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        # Retrieve user data from the database
        # Your database query code goes here
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM python_accounts WHERE username = % s', (username, ))
        user = cursor.fetchone()
        # Check if username exists and password is correct
        if user and check_password_hash(user['password'], password):
            session["user_id"] = user['user_library_id']
            session['username'] = user['username']
            message = "Welcome home !"
            return render_template("index.html", message = message)
        else:
            message = "Invalid username or password."
            return render_template("login.html", message=message)

    return render_template("login.html")


@app.route("/logout")
def logout():
    # Clear the session
    session.clear()
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    message = ""
    if request.method == "POST":
        # Validate form data
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        if not username or not password or not email:
            message = 'Please fill out the form !'
        else:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM python_accounts WHERE username = % s', (username, ))
            account = cursor.fetchone()
            if account:
                message = 'Account already exists !'
            elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                message = 'Invalid email address !'
            elif not re.match(r'[A-Za-z0-9]+', username):
                message = 'Username must contain only characters and numbers !'
            elif not username or not password or not email:
               message = 'Please fill out the form !'
            else:
                hashed_password = generate_password_hash(password)
                cursor.execute('INSERT INTO python_accounts VALUES (NULL, % s, % s, % s)', (username, hashed_password, email, ))
                mysql.connection.commit()
                return redirect("/login")
    elif request.method == 'POST':
        message = 'Please fill out the form !'    
    return render_template("register.html", message = message)
@app.route("/home")
def home():
    return render_template('index.html')
    
@app.route("/library")
def library():
    search_request = request.args.get('search', '').lower()
    if search_request:
        books_found = [book for book in books if search_request in book['title'].lower() or
                        search_request in book['author'].lower()]
    else: 
        books_found = books
    return render_template('library.html', books = books_found)

@app.route('/remove-book', methods = ['POST'])
def remove_book():
    book_index = int(request.form['book_index'])
    if 0 <= book_index < len(books):
        books.pop(book_index)
    return redirect(url_for('library'))
    
def get_book_details(title, author):
    search_url = f"https://openlibrary.org/search.json"
    parameters = {'title': title, 'author': author}
    response = requests.get(search_url, params = parameters)
    data = response.json()

    if data['docs']:
        book = data['docs'][0]
        return{
            'title': book.get('title', 'Unknown Title'),
            'author' : ','.join(book.get('author_name', ['Unknown Author'])),
            'genre' : ','.join(book.get('subject', ['Unknown Genre'])),
            'cover_image' : book.get('cover_i', '')
        }
    return None

@app.route('/add-book', methods = ['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        book_details = get_book_details(title, author)

        if book_details:
            books.append({
                'title': book_details['title'],
                'author': book_details['author'],
                'genre': book_details['genre'],
                'cover_image': book_details['cover_image'],
                'read_status': request.form['read_status'],
            })
            return redirect(url_for('library'))
        else:
            error = "Book not found."
            return render_template('add_book.html', error = error)

    return render_template('add_book.html')
