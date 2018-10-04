from operator import itemgetter
from flask import render_template, jsonify, redirect, url_for, flash, request
from reorder import app, db, mongo, bcrypt
from reorder.forms import RegistrationForm, LoginForm
from reorder.models import User
from flask_login import login_user, current_user, logout_user, login_required
from reorder.scrape_test import (get_products_response, splice_products, sort_products,
                                 get_soh_response, initalize_stock_data, get_sales_orders,
                                 format_sell_through, get_time_now, scrape)
from reorder.kits import convert_to_kits, format_kits_dict


def replace_products(products_skus, brand, last_update):
    # Call get products function to return chosen products
    products_responses = get_products_response(products_skus)

    # Grab only the chosen products
    products = splice_products(products_skus, products_responses)

    # Alphabetize products
    products = sort_products(products)

    # Label collection
    products["name"] = "products"
    products["brand"] = brand
    products["last_update"] = last_update

    # Create reorder collection
    reorder = mongo.db.reorder

    # Replace specific doc in collection with data, if not found insert new doc
    reorder.replace_one(
        {"name": "products", "brand": brand},
        products,
        upsert=True
    )

    flash("Products successfully updated.",
          "background-color: #64b5f6;")


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
            # Grab skus from form
            products_skus = request.form.getlist("product")

            # Find products document in mongodb
            products_data = mongo.db.reorder.find_one({"name": "products", "brand": brand})

            # Record time of update
            last_update = get_time_now()

            if products_data:
                products = products_data["items"]

                # Extract product codes from the list of dictionaries
                product_codes = []

                for product in products:
                    for key, value in product.items():
                        if key == "product_code":
                            product_codes.append(value)

                removed_products_codes = [
                    code for code in product_codes if code not in products_skus]
                new_products_skus = [sku for sku in products_skus if sku not in product_codes]

                if removed_products_codes:
                    for i, product in enumerate(products):
                        if product["product_code"] in removed_products_codes:
                            # Delete product
                            del products[i]

                    print(f"Removed Products: {removed_products_codes}")
                elif new_products_skus:
                    # Call get products function to return chosen products
                    products_responses = get_products_response(new_products_skus)

                    # Grab only the chosen products
                    new_products_data = splice_products(new_products_skus, products_responses)

                    new_products = new_products_data["items"]

                    # Add new products to existing products
                    products.extend(new_products)

                    # Alphabetize products
                    products = sort_products(products)

                    # Create reorder collection
                    reorder = mongo.db.reorder

                    # Update specific document
                    reorder.update_one(
                        {"name": "products", "brand": brand},
                        {'$set': {'items': products, 'last_update': last_update}}
                    )

                if new_products_skus and removed_products_codes:
                    flash(f"Products successfully updated.\
                    Added Products: {new_products_skus}\
                    Removed Products: {removed_products_codes}",
                          "background-color: #64b5f6;")
                elif new_products_skus and not removed_products_codes:
                    flash(f"Products successfully updated.\
                    Added Products: {new_products_skus}\
                    No products have been removed.",
                          "background-color: #64b5f6;")
                elif not new_products_skus and removed_products_codes:
                    flash(f"Products successfully updated.\
                    Removed Products: {removed_products_codes}\
                    No products have been added.",
                          "background-color: #64b5f6;")
            else:
                print("New")
                # Call get products function to return chosen products
                products_responses = get_products_response(products_skus)

                # Grab only the chosen products
                products = splice_products(products_skus, products_responses)

                # Alphabetize products
                products = sort_products(products)

                # Label collection
                products["name"] = "products"
                products["brand"] = brand
                products["last_update"] = last_update

                # Create reorder collection
                reorder = mongo.db.reorder

                # Replace specific doc in collection with data, if not found insert new doc
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

    return redirect(f"products/{brand}", code=302)


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


@app.route("/save-kits/<brand>", methods=["GET", "POST"])
@login_required
def save_kits(brand):
    if request.method == "POST":
        try:
            final_products = request.form.getlist("final_product")
            component_products = request.form.getlist("component_product")

            kit_boms = convert_to_kits(final_products, component_products)

            # Create reorder collection
            reorder = mongo.db.reorder

            # Label collection
            kit_boms["name"] = "kit_boms"
            kit_boms["brand"] = brand

            # Record time of update
            last_update = get_time_now()
            kit_boms["last_update"] = last_update

            # Replace specific document in collection with data, if not found insert new collection
            reorder.replace_one(
                {"name": "kit_boms", "brand": brand},
                kit_boms,
                upsert=True
            )

            flash("Kits successfully updated.",
                  "background-color: #64b5f6;")

        except Exception as e:
            print(e)
            flash("Kit update was unsuccessful. Please check your formatting.",
                  "background-color: #e57373;")

    return redirect(f'/kits/{brand}', code=302)


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
        stock_on_hand = get_soh_response(brand)

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

    return redirect((f"/{brand}"), code=302)


@app.route("/update-sales/<brand>/<num_months>")
@login_required
def update_sales(brand, num_months):
    try:
        # Create reorder collection
        reorder = mongo.db.reorder

        # Call get get sales orders function to return sales orders data
        sales_orders_data = get_sales_orders(num_months)

        sales_orders = {"items": sales_orders_data}

        # Label collection
        sales_orders["name"] = "sales_orders"
        sales_orders["num_months"] = num_months

        # Record time of update
        last_update = get_time_now()
        sales_orders["last_update"] = last_update

        # Replace specific document in collection with data, if not found insert new collection
        reorder.replace_one(
            {"name": "sales_orders", "num_months": num_months},
            sales_orders,
            upsert=True
        )

        flash(f"Sales Orders ({num_months} months) successfully updated.",
              "background-color: #64b5f6;")

    except Exception as e:
        print(e)
        flash("Sales Orders update was unsuccessful.",
              "background-color: #e57373;")

    return redirect((f"/{brand}"), code=302)


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


@app.route("/sales_orders/<num_months>")
@login_required
def sales_orders(num_months):
    # Find reorder dictionary in mongodb
    kit_boms = mongo.db.reorder.find_one({"name": "kit_boms"})

    kits = kit_boms["items"]

    sales_orders_data = mongo.db.reorder.find_one({
        "name": "sales_orders",
        "num_months": num_months
    })

    sell_through_data = format_sell_through(sales_orders_data, kits)

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
