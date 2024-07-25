#Abstract: Allows the user to search for a book via author and title. If they book
# is successfully found, it will be added to the users library where more info of it
# can be viewed. Info like the genre's associated with it and if the user has read it 
# or not.
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

#Andre 
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

#Andre
@app.route("/logout")
def logout():
    # Clear the session
    session.clear()
    return redirect("/")

#Andre
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

#Fidel
@app.route("/library")
def library():
    #Gets the user search request from the query parameters, defaults to empty if there is none.
    search_request = request.args.get('search', '').lower()
    #Filters the book list to include only the books whose title and author include the search requests.
    if search_request:
        books_found = [book for book in books if search_request in book['title'].lower() or
                        search_request in book['author'].lower()]
    else: 
        #If there is no search request, shows all books.
        books_found = books
    #Renders the 'library.html', passing the filtered or unfiltered list of books.
    return render_template('library.html', books = books_found)

#Fidel
@app.route('/remove-book', methods = ['POST'])
def remove_book():
    #Gets a book index from the form data submitted.
    book_index = int(request.form['book_index'])
    #Removes the book at that index if it's in the valid range.
    if 0 <= book_index < len(books):
        books.pop(book_index)
    #Redirects to library with updated list.
    return redirect(url_for('library'))

#Fidel
def get_book_details(title, author):
    #Searches for the book on OpenLibrary using the user specified author and title.
    search_url = f"https://openlibrary.org/search.json"
    parameters = {'title': title, 'author': author}
    #Makes a GET request to the library API with the parameters.
    response = requests.get(search_url, params = parameters)
    data = response.json()

    #If a book is found, return the details of the book.
    if data['docs']:
        book = data['docs'][0]
        return{
            'title': book.get('title', 'Unknown Title'),
            'author' : ','.join(book.get('author_name', ['Unknown Author'])),
            'genre' : ','.join(book.get('subject', ['Unknown Genre'])),
            'cover_image' : book.get('cover_i', '')
        }
    #Returns none if the book is not found.
    return None

#Fidel
@app.route('/add-book', methods = ['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        #Gets the book details from the user filled form.
        title = request.form['title']
        author = request.form['author']
        book_details = get_book_details(title, author)

        #If the book details are found, adds them to the list and redirects the user to the library.
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
            #If the book details aren't found, displays error message.
            error = "Book not found."
            return render_template('add_book.html', error = error)

    return render_template('add_book.html')
