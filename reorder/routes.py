from flask import render_template, jsonify, redirect, url_for, flash, request
from reorder import app, db, mongo, bcrypt
from reorder.forms import RegistrationForm, LoginForm
from reorder.models import User
from flask_login import login_user, current_user, logout_user, login_required
from reorder.scrape_test import get_stock, get_sell_through, format_sell_through, scrape


@app.route("/")
@login_required
def home():
    # Find reorder dictionary in mongodb
    reorder = mongo.db.reorder.find_one()

    return render_template("index.html", reorder=reorder)


# Disabling route
@app.route("/register", methods=["GET", "POST"])
@login_required
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f"Account created for {form.username.data}! Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("registration.html", title="Register", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for("home"))
        else:
            flash("Login unsuccessful. Please check email and password.", "danger")
    return render_template("login.html", title="Login", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/stock-on-hand")
@login_required
def stock_on_hand():

    stock_data = get_stock()

    return jsonify(stock_data)


@app.route("/sell-through/<num_months>")
@login_required
def sales_orders(num_months):

    sell_through = get_sell_through(num_months)

    sell_through_data = format_sell_through(sell_through)

    return jsonify(sell_through_data)


@app.route("/all-data")
@login_required
def all_data():
    # Find reorder dictionary in mongodb
    reorder = mongo.db.reorder.find_one()

    data = reorder["reorder_data"]

    return jsonify(data)


@app.route("/update/<num_months>")
@login_required
def update(num_months):
    # Create reorder collection
    reorder = mongo.db.reorder

    # Call scrape function to return all reorder data
    data = scrape(num_months)

    # Update reorder collection with reorder data
    reorder.update(
        {},
        data,
        upsert=True
    )

    return redirect("/", code=302)
