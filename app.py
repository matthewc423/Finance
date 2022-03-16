import os
import cs50
import flask
import flask_session

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    table = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", "purchases")
    if len(table) != 1:
        db.execute("CREATE TABLE purchases (id INTEGER, username TEXT NOT NULL, symbol TEXT NOT NULL, price TEXT NOT NULL, shares INTEGER, year INTEGER, month INTEGER, day INTEGER, hour INTEGER, minute INTEGER, second INTEGER, PRIMARY KEY(id))")

    tableindex = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", "stocks")
    if len(tableindex) != 1:
        db.execute("CREATE TABLE stocks (id INTEGER, username TEXT NOT NULL, symbol TEXT NOT NULL, shares INTEGER, PRIMARY KEY(id))")

    user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
    transactions = db.execute("SELECT * FROM stocks WHERE username = ?", user[0]["username"])

    stockprices = []
    totalvalues = []
    totalvaluestocks = user[0]["cash"]

    for transaction in transactions:
        price = lookup(transaction["symbol"])["price"]
        stockprices.append(usd(price))
        totalvalue = price * transaction["shares"]
        totalvalues.append(usd(totalvalue))
        totalvaluestocks += totalvalue

    return render_template("index.html", transactions=transactions, stockprices=stockprices, cash=usd(user[0]["cash"]), totalvalues=totalvalues, totalvaluestocks=usd(totalvaluestocks), tlength=len(transactions))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":

        symbol = request.form.get("symbol")
        stock = lookup(symbol)

        if not symbol or stock == None:
            return apology("Invalid stock symbol", 400)

        shares = request.form.get("shares")

        if not shares.isnumeric() or int(shares) <= 0:
            return apology("Inputted shares not a positive integer", 400)
        shares = int(shares)

        user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        if (stock["price"] * shares > user[0]["cash"]):
            return apology("Not enough money to buy", 403)

        db.execute("UPDATE users SET cash = ? WHERE id = ?", user[0]["cash"] - stock["price"] * shares, session["user_id"])

        # inserts into history
        now = datetime.now()
        db.execute("INSERT INTO purchases (username, symbol, shares, price, year, month, day, hour, minute, second) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", user[0]["username"], stock["symbol"], shares, usd(
            stock["price"]), now.year, "{:02d}".format(now.month), "{:02d}".format(now.day), "{:02d}".format(now.hour), "{:02d}".format(now.minute), "{:02d}".format(now.second))
        
        # updates index
        exists = db.execute("SELECT * FROM stocks WHERE symbol = ? AND username = ?", stock["symbol"], user[0]["username"])
        if len(exists) == 1:
            db.execute("UPDATE stocks SET shares = ? WHERE id = ?", exists[0]["shares"] + shares, exists[0]["id"])
        else:
            db.execute("INSERT INTO stocks (username, symbol, shares) VALUES (?, ?, ?)", 
                       user[0]["username"], stock["symbol"], shares)

        return redirect("/")
    else:
        return render_template("buy.html")


@app.route("/cash", methods=["GET", "POST"])
@login_required
def cash():
    """Add cash to account"""

    if request.method == "POST":
        user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        cash = int(request.form.get("cash"))
        if not cash:
            return apology("Invalid amount", 403)
        
        db.execute("UPDATE users SET cash = ? WHERE id = ?", user[0]["cash"] + cash, user[0]["id"])

        return redirect("/")
    else:
        return render_template("cash.html")
    
    
@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
    transactions = db.execute("SELECT * FROM purchases WHERE username = ?", user[0]["username"])

    return render_template("history.html", transactions=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    if request.method == "POST":
        symbol = request.form.get("symbol")

        stock = lookup(symbol)

        if not symbol or stock == None:
            return apology("Invalid stock symbol", 400)

        return render_template("quoted.html", stock=stock, price=usd(stock["price"]))
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if not request.form.get("username"):
            return apology("must provide username", 400)

        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure confirmation was submitted
        elif not request.form.get("confirmation"):
            return apology("must confirm password", 400)

        if password != request.form.get("confirmation"):
            return apology("passwords must match", 400)
        
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        if len(rows) == 1:
            return apology("username already exists", 400)

        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, generate_password_hash(password))

        newuser = db.execute("SELECT * FROM users WHERE username = ?", username)

        session["user_id"] = newuser[0]["id"]

        return redirect("/")
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":

        user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        symbol = request.form.get("symbol")

        if symbol == "Choose stock":
            return apology("Invalid stock chosen", 400)

        sharessold = int(request.form.get("shares"))
        currentshares = db.execute("SELECT * FROM stocks WHERE symbol = ? AND username = ?", symbol, user[0]["username"])

        if sharessold > currentshares[0]["shares"]:
            return apology("Do not own enough shares to sell", 400)

        elif sharessold == currentshares[0]["shares"]:
            db.execute("DELETE FROM stocks WHERE id = ?", currentshares[0]["id"])

        else:
            db.execute("UPDATE stocks SET shares = ? WHERE id = ?", currentshares[0]["shares"] - sharessold, currentshares[0]["id"])

        stock = lookup(symbol)
        db.execute("UPDATE users SET cash = ? WHERE id = ?", user[0]["cash"] + stock["price"] * sharessold, session["user_id"])

        # inserts into history
        now = datetime.now()
        db.execute("INSERT INTO purchases (username, symbol, shares, price, year, month, day, hour, minute, second) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", user[0]["username"], stock["symbol"], sharessold * -1, usd(
            stock["price"]), now.year, "{:02d}".format(now.month), "{:02d}".format(now.day), "{:02d}".format(now.hour), "{:02d}".format(now.minute), "{:02d}".format(now.second))

        return redirect("/")

    else:
        user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])

        symbols = db.execute("SELECT symbol FROM stocks WHERE username = ?", user[0]["username"])
        return render_template("sell.html", symbols=symbols)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
