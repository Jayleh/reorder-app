import asyncio
import binascii
import hmac
import hashlib
import datetime as dt
import aiohttp
import pandas as pd
import datedelta
from reorder.config import api_id, api_key


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


async def fetch(session, url):
    url, headers, params = configure_request(url)
    async with session.get(url, headers=headers, params=params) as resp:
        return await resp.json(content_type=None)


async def splice_stock(brand, stock_on_hand):

    stock_data = []

    if brand == "AnteAGE":
        product_groups = ['|AnteAGE Home', '|AnteAGE Pro', '|AnteAGE MD']
    elif brand == "CytoPro":
        product_groups = ['|CytoPro - Pilica']
    elif brand == "ProCell":
        product_groups = ['|ProCell']
    elif brand == "SkinGen":
        product_groups = ['|SkinGen']
    elif brand == "Venus":
        product_groups = ['|Venus Skin']

    for response in stock_on_hand:

        for item in response["Items"]:

            if item["ProductGroupName"] in product_groups:

                stock_data.append({
                    "product_code": item["ProductCode"],
                    "description": item["ProductDescription"],
                    "stock_on_hand": item["QtyOnHand"],
                    "allocated_quantity": item["AllocatedQty"]
                })

    return stock_data


async def get_stock_urls(session, url):
    async with aiohttp.ClientSession() as session:
        data = await fetch(session, url)

        num_pages = data["Pagination"]["NumberOfPages"]

        partial_url = 'https://api.unleashedsoftware.com/StockOnHand/'
        my_list = [f"{partial_url}{i}?pageSize=200" for i in range(1, num_pages + 1)]

        return my_list


async def run_stock(brand):
    url = f"https://api.unleashedsoftware.com/StockOnHand/1?pageSize=200"
    async with aiohttp.ClientSession() as session:
        urls = await get_stock_urls(session, url)
        # print(urls)

        tasks = [asyncio.ensure_future(fetch(session, url)) for url in urls]
        stock_on_hand = await asyncio.gather(*tasks)

        stock_data = await splice_stock(brand, stock_on_hand)

        return stock_data


def get_stock(brand):
    # loop = asyncio.get_event_loop()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    stock_data = loop.run_until_complete(run_stock(brand))
    loop.close()

    print("get_stock completed")
    return stock_data


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
            completed_date = item["CompletedDate"]

            for line in item["SalesOrderLines"]:
                product_code = line["Product"]["ProductCode"]
                order_quantity = line["OrderQuantity"]
                sell_through.append({
                    "product_code": product_code,
                    "order_quantity": order_quantity,
                    "completed_date": completed_date
                })

    return sell_through


async def get_sales_urls(session, url, start_date, end_date):
    async with aiohttp.ClientSession() as session:
        data = await fetch(session, url)

        num_pages = data["Pagination"]["NumberOfPages"]

        partial_url = 'https://api.unleashedsoftware.com/SalesOrders/'
        my_list = [f"{partial_url}{i}?completedAfter={start_date}&completedBefore={end_date}&pageSize=200" for i in range(
            1, num_pages + 1)]

        return my_list


async def run_sell_through(num_months):
    start_date, end_date = get_date_range(num_months)
    url = f"https://api.unleashedsoftware.com/SalesOrders/1?completedAfter={start_date}&completedBefore={end_date}&pageSize=200"
    async with aiohttp.ClientSession() as session:
        urls = await get_sales_urls(session, url, start_date, end_date)
        print(urls)

        tasks = [asyncio.ensure_future(fetch(session, url)) for url in urls]
        sales_orders = await asyncio.gather(*tasks)

        sell_through = await splice_sales_orders(sales_orders)

        return sell_through


def get_sell_through(num_months):
    # loop = asyncio.get_event_loop()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    sell_through = loop.run_until_complete(run_sell_through(num_months))
    loop.close()

    print("get_sell_through completed")
    return sell_through


# Kit Bills of Materials
kit_boms = {
    "AAPRSSKT": {"AAPRSE30ML": 1, "AAPRAS30ML": 1},
    "AAPRSAKT": {"AAPRSE30ML": 1, "AAPRAC30ML": 1},
    "AAPRMFKT": {"AACL480ML": 1, "AAPRMABX": 1, "AAPRMBBX": 1, "AAPRMCBX": 1, "AARZ240ML": 1, "DVAAMNST0.25MM": 15},
    "AAPRMCKT": {"AACL480ML": 1, "AAPRMCBX": 1, "AARZ240ML": 1, "DVAAMNST0.25MM": 5},
    "AAPRMBKT": {"AACL480ML": 1, "AAPRMBBX": 1, "AARZ240ML": 1, "DVAAMNST0.25MM": 5},
    "AAPRMAKT": {"AACL480ML": 1, "AAPRMABX": 1, "AARZ240ML": 1, "DVAAMNST0.25MM": 5},
    "AAMDSAKT": {"AAMDSE30ML": 1, "AAMDAC30ML": 1},
    "AAMDSSKT": {"AAMDSE30ML": 1, "AAMDAS30ML": 1},
    "AAHMHSKT": {"AAHMHSBX": 1, "DVAAMNST0.25MM": 1}
}


def format_sell_through(sell_through):

    df = pd.DataFrame(sell_through)

    # Drop nan values
    df = df.dropna().reset_index(drop=True)

    reduced_order_quantities = []

    for i, row in df.iterrows():

        product = row["product_code"]
        product_order_quantity = row["order_quantity"]
        completed_date = row["completed_date"]

        for finished_product, children in kit_boms.items():

            if product == finished_product:

                for child, quantity in children.items():

                    added_quantities = {
                        "product_code": child,
                        "order_quantity": quantity * product_order_quantity,
                        "completed_date": completed_date
                    }

                    reduced_order_quantities.append(added_quantities)

    reduced_order_quantities_df = pd.DataFrame(reduced_order_quantities)

    # stack the DataFrames on top of each other
    concat_df = pd.concat([df, reduced_order_quantities_df], axis=0)

    for i, row in concat_df.iterrows():

        completed_date = row["completed_date"]

        converted_timestamp = format_date(completed_date)

        concat_df.at[concat_df.index[i], 'completed_date'] = converted_timestamp

    grouped_prod_date = concat_df.groupby(["product_code", "completed_date"])

    grouped_prod_date = grouped_prod_date.sum()

    prod_date_df = grouped_prod_date.reset_index()

    grouped_prod_num_months = prod_date_df.groupby(["product_code"])

    total_order_quantity = grouped_prod_num_months["order_quantity"].sum()
    avg_order_quantity = grouped_prod_num_months["order_quantity"].mean()
    max_order_quantity = grouped_prod_num_months["order_quantity"].max()

    num_months = grouped_prod_num_months["completed_date"].count()

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

    summary_df[["avg_monthly_usage", "lead_time_demand", "safety_stock", "threshold"]] = summary_df[[
        "avg_monthly_usage", "lead_time_demand", "safety_stock", "threshold"]].round()

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


def create_full_table(brand, num_months):
    stock_data = get_stock(brand)

    sell_through = get_sell_through(num_months)

    sell_through_data = format_sell_through(sell_through)

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

    merged_df = merged_df[["product_code", "description", "stock_on_hand", "threshold", "display_percentage", "allocated_quantity",
                           "order_quantity", "num_months", "avg_monthly_usage", "max_monthly_usage", "lead_time_demand", "safety_stock"]]

    kit_list = [key for key in kit_boms.keys()]

    merged_df = merged_df[~merged_df["product_code"].isin(kit_list)]

    merged_df = merged_df.sort_values(by=["display_percentage"]).reset_index(drop=True)

    merged_df = merged_df.fillna("-")

    combined_data = merged_df.to_dict(orient="records")

    return combined_data


def scrape(brand, num_months):
    data = {}

    last_update = dt.datetime.today().strftime("%Y-%m-%d %H:%M:%S.%f")
    reorder_data = create_full_table(brand, num_months)

    data["brand"] = brand
    data["months_past_sellthrough"] = num_months
    data["last_update"] = last_update
    data["reorder_data"] = reorder_data

    # print(data)

    return data


if __name__ == "__main__":
    scrape("AnteAGE", 3)
