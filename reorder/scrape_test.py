from operator import itemgetter
import asyncio
import binascii
import hmac
import hashlib
import datetime as dt
import aiohttp
import pandas as pd
import datedelta
from reorder import mongo, api_id, api_key


def configure_request(url):

    parts = url.split('?')
    if len(parts) > 1:
        query = parts[1]
    else:
        query = ""

    query = query.encode("utf-8")

    hashed = hmac.new(api_key, query, hashlib.sha256)
    signature = binascii.b2a_base64(hashed.digest())[:-1]

    signature = signature.decode("utf-8")

    headers = {
        'content-type': 'application/json',
        'accept': 'application/json',
        'api-auth-signature': signature,
        'api-auth-id': api_id
    }
    params = {}

    return url, headers, params


def get_time_now():
    time_now = dt.datetime.today() - dt.timedelta(hours=7)
    time_now = time_now.strftime("%m/%d/%y %I:%M %p")

    return time_now


async def fetch(session, url):
    url, headers, params = configure_request(url)
    async with session.get(url, headers=headers, params=params) as resp:
        return await resp.json()


def get_products_urls(product_skus):
    products_urls = [
        f"https://api.unleashedsoftware.com/Products?productCode={sku}" for sku in product_skus]

    return products_urls


def sort_products(products):
    sorted_products = sorted(products, key=itemgetter('product_code'))

    return sorted_products


def splice_products(products_skus, products_responses):
    products = []

    for response in products_responses["responses"]:

        for item in response["Items"]:

            if item["ProductCode"] in products_skus:

                products.append({
                    "product_code": item["ProductCode"],
                    "description": item["ProductDescription"],
                    "guid": item["Guid"]
                })

    product_dict = {"items": products}

    return product_dict


async def run_products(product_skus):
    urls = get_products_urls(product_skus)

    async with aiohttp.ClientSession() as session:
        tasks = [asyncio.ensure_future(fetch(session, url)) for url in urls]
        products = await asyncio.gather(*tasks)

        # Stock on hand dictionary
        products_dict = {"responses": products}

        return products_dict


def get_products_response(products_skus):
    # loop = asyncio.get_event_loop()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    products_dict = loop.run_until_complete(run_products(products_skus))
    loop.close()

    print("get_products_response completed")
    return products_dict


def get_stock_query(brand):
    # Grab products from mongodb
    products = mongo.db.reorder.find_one({"name": "products", "brand": brand})

    guid_list = []

    for product in products["items"]:
        guid = product["guid"]

        guid_list.append(f"{guid}")

    query = ",".join(guid_list)

    print(query)

    return query


async def run_stock(brand):
    query = get_stock_query(brand)

    url = f"https://api.unleashedsoftware.com/StockOnHand?productId={query}&pageSize=1000"
    async with aiohttp.ClientSession() as session:
        task = asyncio.ensure_future(fetch(session, url))

        stock_on_hand = await task

        stock_data = stock_on_hand["Items"]

        # Stock on hand dictionary
        soh_dict = {"items": stock_data}

        # stock_data = await splice_stock(brand, stock_on_hand)

        return soh_dict


def get_soh_response(brand):
    # loop = asyncio.get_event_loop()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    stock_on_hand = loop.run_until_complete(run_stock(brand))
    loop.close()

    print("get_soh_response completed")
    return stock_on_hand


def get_date_range(num_months):

    num_months = int(num_months)

    today = dt.datetime.now()

    calc_start_date = today - datedelta.datedelta(months=num_months)

    start_date = dt.datetime(calc_start_date.year, calc_start_date.month, 1) - datedelta.DAY

    start_date = str(start_date)[:10]

    end_date = f"{str(today)[:7]}-01"

    return start_date, end_date


async def splice_sales_orders(sales_orders):

    sell_through = []

    for response in sales_orders:

        for item in response["Items"]:
            order_date = item["OrderDate"]

            for line in item["SalesOrderLines"]:
                product_code = line["Product"]["ProductCode"]
                order_quantity = line["OrderQuantity"]
                sell_through.append({
                    "product_code": product_code,
                    "order_quantity": order_quantity,
                    "order_date": order_date
                })

    return sell_through


async def get_sales_urls(session, url, start_date, end_date):
    async with aiohttp.ClientSession() as session:
        data = await fetch(session, url)

        num_pages = data["Pagination"]["NumberOfPages"]

        partial_url = 'https://api.unleashedsoftware.com/SalesOrders/'
        my_list = [f"{partial_url}{i}?startDate={start_date}&endDate={end_date}&pageSize=200" for i in range(
            1, num_pages + 1)]

        return my_list


async def run_sales_orders(num_months):
    start_date, end_date = get_date_range(num_months)
    url = f"https://api.unleashedsoftware.com/SalesOrders/1?startDate={start_date}&endDate={end_date}&pageSize=200"
    async with aiohttp.ClientSession() as session:
        urls = await get_sales_urls(session, url, start_date, end_date)
        print(urls)

        tasks = [asyncio.ensure_future(fetch(session, url)) for url in urls]
        sales_orders = await asyncio.gather(*tasks)

        sales_orders_data = await splice_sales_orders(sales_orders)

        return sales_orders_data


def get_sales_orders(num_months):
    # loop = asyncio.get_event_loop()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    sales_orders_data = loop.run_until_complete(run_sales_orders(num_months))
    loop.close()

    print("get_sales_orders completed")
    return sales_orders_data


def format_sell_through(sales_orders_data, kits):
    df = pd.DataFrame(sales_orders_data)

    # Make sure order quantity is numeric, cell isn't convert to NaN
    df["order_quantity"] = pd.to_numeric(df["order_quantity"], errors="coerce")

    # Drop NaN values
    df = df.dropna(subset=["order_quantity"]).reset_index(drop=True)

    reduced_order_quantities = []

    for i, row in df.iterrows():

        product = row["product_code"]
        product_order_quantity = row["order_quantity"]
        order_date = row["order_date"]

        for finished_product, children in kits.items():

            if product == finished_product:

                for child, quantity in children.items():

                    added_quantities = {
                        "product_code": child,
                        "order_quantity": quantity * product_order_quantity,
                        "order_date": order_date
                    }

                    reduced_order_quantities.append(added_quantities)

    reduced_order_quantities_df = pd.DataFrame(reduced_order_quantities)

    # stack the DataFrames on top of each other
    concat_df = pd.concat([df, reduced_order_quantities_df], axis=0)

    for i, row in concat_df.iterrows():

        order_date = row["order_date"]

        converted_timestamp = format_date(order_date)

        concat_df.at[concat_df.index[i], "order_date"] = converted_timestamp

    grouped_prod_date = concat_df.groupby(["product_code", "order_date"])

    grouped_prod_date = grouped_prod_date.sum()

    prod_date_df = grouped_prod_date.reset_index()

    grouped_prod_num_months = prod_date_df.groupby(["product_code"])

    total_order_quantity = grouped_prod_num_months["order_quantity"].sum()
    avg_order_quantity = grouped_prod_num_months["order_quantity"].mean()
    max_order_quantity = grouped_prod_num_months["order_quantity"].max()

    num_months = grouped_prod_num_months["order_date"].count()

    summary_df = pd.DataFrame({"order_quantity": total_order_quantity,
                               "num_months": num_months,
                               "avg_monthly_usage": avg_order_quantity,
                               "max_monthly_usage": max_order_quantity})

    summary_df = summary_df.reset_index()

    summary_df = summary_df[["product_code", "order_quantity",
                             "num_months", "avg_monthly_usage", "max_monthly_usage"]]

    summary_df["lead_time_demand"] = summary_df["avg_monthly_usage"] * 2
    summary_df["safety_stock"] = (summary_df["max_monthly_usage"] *
                                  2.75) - summary_df["lead_time_demand"]
    summary_df["threshold"] = summary_df["lead_time_demand"] + summary_df["safety_stock"]

    summary_df[["avg_monthly_usage", "lead_time_demand", "safety_stock", "threshold"]] = \
        summary_df[["avg_monthly_usage", "lead_time_demand", "safety_stock", "threshold"]].round()

    sell_through_data = summary_df.to_dict(orient="records")

    return sell_through_data


def format_date(string):
    unix_timestamp = int(''.join(list(filter(str.isdigit, string))))
    timestamp = pd.to_datetime(unix_timestamp, unit='ms')
    converted_timestamp = timestamp.strftime('%Y-%m')

    return converted_timestamp


def get_percentage(stock_on_hand, threshold, lead_time_demand):

    reorder_percentage = (stock_on_hand - threshold) / lead_time_demand * 100

    if reorder_percentage < 0:

        stock_percentage = (stock_on_hand - threshold) / threshold * 100

        return stock_percentage
    else:
        return reorder_percentage


def initalize_stock_data(brand):
    # Grab soh from mongodb
    stock_on_hand = mongo.db.reorder.find_one({"name": "stock_on_hand", "brand": brand})

    stock_data = []

    for product in stock_on_hand["items"]:

        stock_data.append({
            "product_code": product["ProductCode"],
            "description": product["ProductDescription"],
            "stock_on_hand": product["QtyOnHand"],
            "allocated_quantity": product["AllocatedQty"]
        })

    return stock_data


def initialize_sales_data(num_months):
    # Grab soh from mongodb
    sales_orders = mongo.db.reorder.find_one(
        {"name": "sales_orders", "num_months": num_months})

    sales_orders_data = sales_orders["items"]

    return sales_orders_data


def initialize_kits(brand):
    # Find reorder dictionary in mongodb
    reorder = mongo.db.reorder.find_one({"name": "kit_boms", "brand": brand})

    kits = reorder["items"]

    return kits


def create_full_table(brand, num_months):
    # Grab all data from documents need to calculate sell through
    stock_data = initalize_stock_data(brand)
    sales_orders_data = initialize_sales_data(num_months)
    kits = initialize_kits(brand)

    sell_through_data = format_sell_through(sales_orders_data, kits)

    stock_df = pd.DataFrame(stock_data)

    sell_through_df = pd.DataFrame(sell_through_data)

    merged_df = pd.merge(stock_df, sell_through_df, how="left")

    merged_df["order_quantity"] = merged_df["order_quantity"].fillna(0)

    for i, row in merged_df.iterrows():

        stock_on_hand = row["stock_on_hand"]
        threshold = row["threshold"]
        lead_time_demand = row["lead_time_demand"]

        display_percentage = get_percentage(stock_on_hand, threshold, lead_time_demand)

        merged_df.at[merged_df.index[i], 'display_percentage'] = display_percentage

    merged_df["display_percentage"] = merged_df["display_percentage"].round()

    merged_df = merged_df[["product_code", "description", "stock_on_hand", "threshold",
                           "display_percentage", "allocated_quantity", "order_quantity",
                           "num_months", "avg_monthly_usage", "max_monthly_usage",
                           "lead_time_demand", "safety_stock"]]

    # kit_list = [key for key in kits.keys()]

    # merged_df = merged_df[~merged_df["product_code"].isin(kit_list)]

    merged_df = merged_df.sort_values(by=["display_percentage"]).reset_index(drop=True)

    merged_df = merged_df.fillna("-")

    combined_data = merged_df.to_dict(orient="records")

    return combined_data


def scrape(brand, num_months):
    # Instantiate data dictionary
    data = {}

    last_update = get_time_now()
    reorder_data = create_full_table(brand, num_months)

    data["brand"] = brand
    data["months_past_sellthrough"] = num_months
    data["last_update"] = last_update
    data["reorder_data"] = reorder_data

    # print(data)

    return data


if __name__ == "__main__":
    scrape("AnteAGE", 3)
