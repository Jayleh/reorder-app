import datetime as dt
from flask import render_template, jsonify, redirect, url_for, flash, request
from reorder import app, db, mongo, bcrypt
from reorder.forms import RegistrationForm, LoginForm
from reorder.models import User
from flask_login import login_user, current_user, logout_user, login_required
from reorder.scrape_test import get_soh_response, splice_stock, get_sell_through, format_sell_through, scrape


def get_time_now():
    time_now = dt.datetime.today() - dt.timedelta(hours=7)
    time_now = time_now.strftime("%m/%d/%y %I:%M %p")

    return time_now


@app.route("/")
@login_required
def home():
    # Default
    brand = "AnteAGE"

    # Find reorder dictionary in mongodb
    reorder = mongo.db.reorder.find_one({"brand": brand})

    # Grab soh from mongodb
    stock_on_hand = mongo.db.reorder.find_one({"name": "stock_on_hand"})

    return render_template("index.html", reorder=reorder, soh_data=stock_on_hand)


@app.route("/<brand>")
@login_required
def table(brand):
    # Find reorder dictionary in mongodb
    reorder = mongo.db.reorder.find_one({"brand": brand})

    # Grab soh from mongodb
    stock_on_hand = mongo.db.reorder.find_one({"name": "stock_on_hand"})

    return render_template("index.html", reorder=reorder, soh_data=stock_on_hand)


@app.route("/partners")
@login_required
def partners():
    return render_template("partners.html")


@app.route("/kits")
@login_required
def kits():
    return render_template("kits.html")


@app.route("/save-kits", methods=["GET", "POST"])
@login_required
def save_kits():
    if request.method == "POST":

        main_skus = request.form["final_product"]

        print(main_skus)
    else:
        print('hi')

    return redirect(url_for('kits'), code=302)


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
    # Grab soh from mongodb
    stock_on_hand = mongo.db.reorder.find_one({"name": "stock_on_hand"})

    return jsonify(stock_on_hand["responses"])


@app.route("/stock-data/<brand>")
@login_required
def stock_data(brand):
    # Grab soh from mongodb
    stock_on_hand = mongo.db.reorder.find_one({"name": "stock_on_hand"})

    stock_data = splice_stock(brand, stock_on_hand["responses"])

    return jsonify(stock_data)


@app.route("/sell-through/<num_months>")
@login_required
def sales_orders(num_months):

    sell_through = get_sell_through(num_months)

    sell_through_data = format_sell_through(sell_through)

    return jsonify(sell_through_data)


@app.route("/all-data/<brand>/<num_months>")
@login_required
def all_data(brand, num_months):
    # Find reorder dictionary in mongodb
    reorder = mongo.db.reorder.find_one({"brand": brand, "months_past_sellthrough": num_months})

    data = {
        "brand": reorder["brand"],
        "months_past_sellthrough": reorder["months_past_sellthrough"],
        "last_update": reorder["last_update"],
        "reorder_data": reorder["reorder_data"]
    }

    return jsonify(data)


@app.route("/update/<brand>/<num_months>")
@login_required
def update(brand, num_months):
    try:
        # Create reorder collection
        reorder = mongo.db.reorder

        # Call scrape function to return all reorder data
        data = scrape(brand, num_months)

        # Replace specific document in reorder collection with data, if not found insert new collection
        reorder.replace_one(
            {"brand": brand, "months_past_sellthrough": num_months},
            data,
            upsert=True
        )

        flash("Reorder plan successfully updated.",
              "background-color: #64b5f6;")

    except Exception as e:
        print(e)
        flash("Reorder plan update was unsuccessful.",
              "background-color: #e57373;")

    return redirect(f"/{brand}", code=302)


@app.route("/update-soh")
@login_required
def update_soh():
    try:
        # Create reorder collection
        reorder = mongo.db.reorder

        # Call scrape function to return all reorder data
        stock_on_hand = get_soh_response()

        # Label collection
        stock_on_hand["name"] = "stock_on_hand"

        # Record time of update
        last_update = get_time_now()
        stock_on_hand["last_update"] = last_update

        # Replace specific document in collection with data, if not found insert new collection
        reorder.replace_one(
            {"name": "stock_on_hand"},
            stock_on_hand,
            upsert=True
        )

        flash("Stock on Hand successfully updated.",
              "background-color: #64b5f6;")

    except Exception as e:
        print(e)
        flash("Stock on Hand update was unsuccessful.",
              "background-color: #e57373;")

    return redirect(url_for('home'), code=302)
