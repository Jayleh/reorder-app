import datetime as dt
import pandas as pd
from config import api_id, api_key
from api import UnleashedApi


def get_stock():

    # Unleashed api base url
    api_url = "https://api.unleashedsoftware.com"

    # Authorize and connect to api
    auth = UnleashedApi(api_url, api_id, api_key)

    stock_data = []

    product_groups = ['|AnteAGE Home', '|AnteAGE Pro', '|AnteAGE MD']

    # Paginate through arbitrary large number
    for x in range(100):

        # Get response
        stock_on_hand = auth.get_request(method=f"StockOnHand/{x+1}?pageSize=500").json()

        for item in stock_on_hand["Items"]:

            if item["ProductGroupName"] in product_groups:

                stock_data.append({
                    "product_code": item["ProductCode"],
                    "description": item["ProductDescription"],
                    "stock_on_hand": item["QtyOnHand"],
                    "allocated_quantity": item["AllocatedQty"]
                })

        # Break loop if item_count hits max number of orders
        if stock_on_hand["Pagination"]["PageNumber"] == stock_on_hand["Pagination"]["NumberOfPages"]:
            break

    return stock_data


def format_date(string):
    unix_timestamp = int(''.join(list(filter(str.isdigit, string))))
    timestamp = pd.to_datetime(unix_timestamp, unit='ms')
    converted_timestamp = timestamp.strftime('%Y-%m')

    return converted_timestamp


def get_date_range(num_months):

    today = dt.datetime.today()

    days = round(int(num_months) * 30.41666666666667)

    calc_start_date = today - dt.timedelta(days=days)

    start_date = dt.datetime(calc_start_date.year, calc_start_date.month, 1) - dt.timedelta(days=1)

    start_date = str(start_date)[:10]

    end_date = f"{str(today)[:7]}-01"

    # print(start_date, end_date)

    return start_date, end_date


def get_sell_through(num_months):

    # Unleashed api base url
    api_url = "https://api.unleashedsoftware.com"

    # Authorize and connect to api
    auth = UnleashedApi(api_url, api_id, api_key)

    sell_through = []

    start_date, end_date = get_date_range(num_months)

    # Paginate through arbitrary large number
    for x in range(100):

        # Get response
        sales_orders = auth.get_request(
            method=f"SalesOrders/{x+1}?completedAfter={start_date}&completedBefore={end_date}&pageSize=400").json()

        for item in sales_orders["Items"]:

            completed_date = item["CompletedDate"]

            for line in item["SalesOrderLines"]:

                product_code = line["Product"]["ProductCode"]
                order_quantity = line["OrderQuantity"]

                sell_through.append({
                    "product_code": product_code,
                    "order_quantity": order_quantity,
                    "completed_date": completed_date
                })

        # Break loop if item_count hits max number of orders
        if sales_orders["Pagination"]["PageNumber"] == sales_orders["Pagination"]["NumberOfPages"]:
            break

    df = pd.DataFrame(sell_through)

    for i, row in df.iterrows():

        completed_date = row["completed_date"]

        converted_timestamp = format_date(completed_date)

        df.at[df.index[i], 'completed_date'] = converted_timestamp

    grouped_prod_date = df.groupby(["product_code", "completed_date"])

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


def get_percentage(stock_on_hand, threshold, lead_time_demand):

    reorder_percentage = (stock_on_hand - threshold) / lead_time_demand * 100

    if reorder_percentage < 0:

        stock_percentage = (stock_on_hand - threshold) / threshold * 100

        return stock_percentage
    else:
        return reorder_percentage


def create_full_table(num_months):
    stock_data = get_stock()

    stock_df = pd.DataFrame(stock_data)

    sell_through_data = get_sell_through(num_months)

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

    # Hard coded kit bills of materials
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

    reduced_order_quantities = []

    for i, row in merged_df.iterrows():

        product = row["product_code"]
        product_order_quantity = row["order_quantity"]

        for finished_product, children in kit_boms.items():

            if product == finished_product:

                for child, quantity in children.items():

                    added_quantities = {
                        "product_code": child,
                        "order_quantity": quantity * product_order_quantity
                    }

                    reduced_order_quantities.append(added_quantities)

    reduced_order_quantities_df = pd.DataFrame(reduced_order_quantities)

    reduced_grouped_df = reduced_order_quantities_df.groupby(["product_code"]).sum()

    reduced_grouped_df = reduced_grouped_df.reset_index()

    for i, row in merged_df.iterrows():

        merged_code = row["product_code"]
        merged_order_quantity = row["order_quantity"]

        for j, line in reduced_grouped_df.iterrows():

            reduced_code = line["product_code"]
            reduced_order_quantity = line["order_quantity"]

            if merged_code == reduced_code:

                new_quantity = merged_order_quantity + reduced_order_quantity

                merged_df.at[merged_df.index[i], 'order_quantity'] = new_quantity

    kit_list = [key for key in kit_boms.keys()]

    merged_df = merged_df[~merged_df["product_code"].isin(kit_list)]

    merged_df = merged_df.sort_values(by=["display_percentage"]).reset_index(drop=True)

    merged_df = merged_df.fillna("-")

    combined_data = merged_df.to_dict(orient="records")

    return combined_data


def scrape(num_months):
    data = {}

    last_update = dt.datetime.today().strftime("%Y-%m-%d %H:%M:%S.%f")
    reorder_data = create_full_table(num_months)

    data["months_past_sellthrough"] = num_months
    data["last_update"] = last_update
    data["reorder_data"] = reorder_data

    return data
