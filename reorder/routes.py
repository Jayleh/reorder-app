import datetime as dt
from flask import render_template, jsonify, redirect, url_for, flash, request
from reorder import app, db, mongo, bcrypt
from reorder.forms import RegistrationForm, LoginForm
from reorder.models import User
from flask_login import login_user, current_user, logout_user, login_required
from reorder.scrape_test import (get_products_response, splice_products, get_soh_response,
                                 initalize_stock_data, get_sell_through, format_sell_through,
                                 scrape)
from reorder.kits import convert_to_kits, format_kits_dict


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


@app.route("/nav")
@login_required
def nav():
    return render_template("nav.html")


@app.route("/partners")
@login_required
def partners():
    return render_template("partners.html")


@app.route("/kits")
@login_required
def kits():
    # Default
    brand = "AnteAGE"

    # Find reorder dictionary in mongodb
    reorder = mongo.db.reorder.find_one({"name": "kit_boms", "brand": brand})

    kits = reorder["items"]

    kit_boms = format_kits_dict(kits)

    return render_template("kits.html", reorder=reorder, kit_boms=kit_boms)


@app.route("/kits/<brand>")
@login_required
def kits_partners(brand):
    # Find reorder dictionary in mongodb
    reorder = mongo.db.reorder.find_one({"name": "kit_boms", "brand": brand})

    kits = reorder["items"]

    kit_boms = format_kits_dict(kits)

    return render_template("kits.html", reorder=reorder, kit_boms=kit_boms)


@app.route("/save-kits", methods=["GET", "POST"])
@login_required
def save_kits():
    if request.method == "POST":
        try:
            final_products = request.form.getlist("final_product")
            component_products = request.form.getlist("component_product")

            kit_boms = convert_to_kits(final_products, component_products)

            # Create reorder collection
            reorder = mongo.db.reorder

            # Label collection
            kit_boms["name"] = "kit_boms"

            # Record time of update
            last_update = get_time_now()
            kit_boms["last_update"] = last_update

            # Replace specific document in collection with data, if not found insert new collection
            reorder.replace_one(
                {"name": "kit_boms"},
                kit_boms,
                upsert=True
            )

            flash("Kits successfully updated.",
                  "background-color: #64b5f6;")

        except Exception as e:
            print(e)
            flash("Kit update was unsuccessful. Please check your formatting.",
                  "background-color: #e57373;")

    return redirect(url_for('kits'), code=302)


@app.route("/products")
@login_required
def products():
    # Default
    brand = "AnteAGE"

    # Find reorder dictionary in mongodb
    reorder = mongo.db.reorder.find_one({"name": "products", "brand": brand})

    products = reorder["items"]

    return render_template("products.html", reorder=reorder, products=products)


@app.route("/products/<brand>")
@login_required
def products_partners(brand):
    # Find reorder dictionary in mongodb
    reorder = mongo.db.reorder.find_one({"name": "products", "brand": brand})

    products = reorder["items"]

    return render_template("products.html", reorder=reorder, products=products)


@app.route("/save-products/<brand>", methods=["GET", "POST"])
@login_required
def save_products(brand):
    if request.method == "POST":
        try:
            products_skus = request.form.getlist("product")

            # Create reorder collection
            reorder = mongo.db.reorder

            # Call get products function to return chosen products
            products_responses = get_products_response(products_skus)

            # Grab only the chosen products
            products = splice_products(products_skus, products_responses)

            # Label collection
            products["name"] = "products"
            products["brand"] = brand

            # Record time of update
            last_update = get_time_now()
            products["last_update"] = last_update

            # Replace specific document in collection with data, if not found insert new collection
            reorder.replace_one(
                {"name": "products", "brand": brand},
                products,
                upsert=True
            )

            flash("Products successfully updated.",
                  "background-color: #64b5f6;")

        except Exception as e:
            print(e)
            flash("Products update was unsuccessful.",
                  "background-color: #e57373;")

    return redirect(url_for('products'), code=302)


@app.route("/stock-on-hand")
@login_required
def stock_on_hand():
    # Grab soh from mongodb
    stock_on_hand = mongo.db.reorder.find_one({"name": "stock_on_hand"})

    return jsonify(stock_on_hand["responses"])


@app.route("/stock-data/<brand>")
@login_required
def stock_data(brand):
    stock_data = initalize_stock_data(brand)

    return jsonify(stock_data)


@app.route("/sell-through/<num_months>")
@login_required
def sales_orders(num_months):
    # Find reorder dictionary in mongodb
    reorder = mongo.db.reorder.find_one({"name": "kit_boms"})

    kits = reorder["items"]

    sell_through = get_sell_through(num_months)

    sell_through_data = format_sell_through(sell_through, kits)

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

        # Replace specific doc in reorder collection with data, if not found insert new collection
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


@app.route("/update-soh/<brand>")
@login_required
def update_soh(brand):
    try:
        # Create reorder collection
        reorder = mongo.db.reorder

        # Call get stock on hand response function to return soh for products
        stock_on_hand = get_soh_response()

        # Label collection
        stock_on_hand["name"] = "stock_on_hand"
        stock_on_hand["brand"] = brand

        # Record time of update
        last_update = get_time_now()
        stock_on_hand["last_update"] = last_update

        # Replace specific document in collection with data, if not found insert new collection
        reorder.replace_one(
            {"name": "stock_on_hand", "brand": brand},
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
