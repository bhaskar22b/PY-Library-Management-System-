import os
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy


# Configure Flask for Vercel or local development
IS_VERCEL = bool(os.environ.get("VERCEL"))

app = Flask(
    __name__,
    instance_path=(
        "/tmp/instance"
        if IS_VERCEL
        else os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance")
    )
)

if IS_VERCEL:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////tmp/library.db"
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///library.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)




# --------------------------------------------------
# Database Models
# --------------------------------------------------

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    quantity = db.Column(db.Integer, default=1)
    available_quantity = db.Column(db.Integer, default=1)


class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)


class Issue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, nullable=False)
    member_id = db.Column(db.Integer, nullable=False)
    returned = db.Column(db.Boolean, default=False, nullable=False)

    book = db.relationship(
        "Book",
        primaryjoin="foreign(Issue.book_id) == Book.id",
        viewonly=True
    )

    member = db.relationship(
        "Member",
        primaryjoin="foreign(Issue.member_id) == Member.id",
        viewonly=True
    )


# --------------------------------------------------
# Create Database Tables
# --------------------------------------------------

with app.app_context():
    db.create_all()


# --------------------------------------------------
# Shared Dashboard Function
# --------------------------------------------------

def render_dashboard(username="admin"):
    total_books = Book.query.count()
    total_members = Member.query.count()

    # Count only books that have not been returned.
    total_issued = Issue.query.filter_by(returned=False).count()

    # Count completed return records.
    total_returned = Issue.query.filter_by(returned=True).count()

    return render_template(
        "dashboard.html",
        name=username,
        total_books=total_books,
        total_members=total_members,
        total_issued=total_issued,
        total_returned=total_returned
    )


# --------------------------------------------------
# Login Page
# --------------------------------------------------

@app.route("/")
def home():
    return render_template("login.html")


# --------------------------------------------------
# Login Processing
# --------------------------------------------------

@app.route("/submit", methods=["POST"])
def submit():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    # Demonstration credentials only.
    if username == "admin" and password == "1234":
        return render_dashboard(username)

    return render_template("error.html")


# --------------------------------------------------
# Dashboard
# --------------------------------------------------

@app.route("/dashboard")
def dashboard():
    return render_dashboard()


# --------------------------------------------------
# Add Book
# --------------------------------------------------

@app.route("/add-book", methods=["GET", "POST"])
def add_book():
    if request.method == "POST":
        title = request.form["title"].strip()
        author = request.form["author"].strip()
        category = request.form["category"].strip()
        quantity = int(request.form["quantity"])

        if not title or not author or quantity < 1:
            return "Please enter a valid title, author and quantity.", 400

        new_book = Book(
            title=title,
            author=author,
            category=category,
            quantity=quantity,
            available_quantity=quantity
        )

        db.session.add(new_book)
        db.session.commit()

        return render_template("successBookAdd.html")

    return render_template("add_book.html")


# --------------------------------------------------
# Add Member
# --------------------------------------------------

@app.route("/add-member", methods=["GET", "POST"])
def add_member():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip()
        phone = request.form["phone"].strip()

        if not name or not email or not phone:
            return "Please complete all member fields.", 400

        new_member = Member(
            name=name,
            email=email,
            phone=phone
        )

        db.session.add(new_member)
        db.session.commit()

        return render_template("successMemberAdd.html")

    return render_template("add_member.html")


# --------------------------------------------------
# View Books
# --------------------------------------------------

@app.route("/books")
def books():
    all_books = Book.query.order_by(Book.title.asc()).all()

    return render_template(
        "books.html",
        books=all_books
    )


# --------------------------------------------------
# View Members
# --------------------------------------------------

@app.route("/members")
def members():
    all_members = Member.query.order_by(Member.name.asc()).all()

    return render_template(
        "info_members.html",
        members=all_members
    )


# --------------------------------------------------
# Issue Book
# --------------------------------------------------

@app.route("/issue-book", methods=["GET", "POST"])
def issue_book():
    books = Book.query.order_by(Book.title.asc()).all()
    members = Member.query.order_by(Member.name.asc()).all()

    if request.method == "POST":
        try:
            book_id = int(request.form["book_id"])
            member_id = int(request.form["member_id"])
        except (ValueError, KeyError):
            return "Please select a valid book and member.", 400

        book = db.session.get(Book, book_id)
        member = db.session.get(Member, member_id)

        if book is None or member is None:
            return "The selected book or member could not be found.", 404

        if book.available_quantity <= 0:
            return "This book is currently unavailable.", 400

        new_issue = Issue(
            book_id=book_id,
            member_id=member_id
        )

        db.session.add(new_issue)
        book.available_quantity -= 1
        db.session.commit()

        return render_template("successIssueBook.html")

    return render_template(
        "issue_book.html",
        books=books,
        members=members
    )


# --------------------------------------------------
# View Issue and Return Records
# --------------------------------------------------

@app.route("/issued-books")
def issued_books():
    all_issued_books = Issue.query.order_by(Issue.id.desc()).all()

    return render_template(
        "issued_books.html",
        issued_books=all_issued_books
    )


# --------------------------------------------------
# Return Book
# --------------------------------------------------

@app.route("/return-book/<int:issue_id>")
def return_book(issue_id):
    issue = db.session.get(Issue, issue_id)

    if issue is None:
        return "Issue record not found.", 404

    if issue.returned:
        return render_template("alreadyReturned.html")

    book = db.session.get(Book, issue.book_id)

    if book is None:
        return "The associated book could not be found.", 404

    issue.returned = True
    book.available_quantity += 1

    db.session.commit()

    return render_template("successReturnBook.html")


# --------------------------------------------------
# Run Application
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
