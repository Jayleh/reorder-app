from flask import Flask, render_template, jsonify, redirect
from flask_pymongo import PyMongo
from scrape import get_stock, get_sell_through, scrape
from config import mongodb_name, mongo_uri
from rq import Queue
from worker import conn


app = Flask(__name__)

app.config['MONGO_DBNAME'] = mongodb_name
app.config["MONGO_URI"] = mongo_uri

mongo = PyMongo(app)


@app.route("/")
def home():
    # Find reorder dictionary in mongodb
    reorder = mongo.db.reorder.find_one()

    return render_template("index.html", reorder=reorder)


@app.route("/stock-on-hand")
def stock_on_hand():

    stock_data = get_stock()

    return jsonify(stock_data)


@app.route("/sell-through/<num_months>")
def sales_orders(num_months):

    sell_through_data = get_sell_through(num_months)

    return jsonify(sell_through_data)


@app.route("/all-data")
def all_data():
    # Find reorder dictionary in mongodb
    reorder = mongo.db.reorder.find_one()

    data = reorder["reorder_data"]

    return jsonify(data)


@app.route("/update/<num_months>")
def update(num_months):
    # Create reorder collection
    reorder = mongo.db.reorder

    # Call scrape function to return all reorder data
    # data = scrape(num_months)
    q = Queue(connection=conn)
    data = q.enqueue(scrape, num_months)

# Update reorder collection with reorder data
    reorder.update(
        {},
        data,
        upsert=True
    )

    return redirect("/", code=302)


if __name__ == "__main__":
    app.run(debug=True)
