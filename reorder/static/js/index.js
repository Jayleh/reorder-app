d3.json('/all-data', (error, data) => {
    if (error) throw error;

    let $tbody = d3.select('table').append('tbody');

    data.forEach((item, index) => {

        let productCode = item["product_code"],
            description = item["description"],
            stockOnHand = item["stock_on_hand"],
            allocatedQty = item["allocated_quantity"],
            orderQty = item["order_quantity"],
            avgMonthlyUsage = item["avg_monthly_usage"],
            maxMonthlyUsage = item["max_monthly_usage"],
            leadTimeDemand = item["lead_time_demand"],
            safetyStock = item["safety_stock"],
            threshold = item["threshold"],
            indicator = item["display_percentage"];

        $tbody.append('tr')
            .html(
                `<td class="text-left"><strong>${index + 1}</strong></td><td class="text-left">${productCode}</td><td class="text-left">${description}</td><td class="text-right">${stockOnHand}</td><td class="text-right">${threshold}</td><td class="text-right">${indicator}</td><td class="text-right">${allocatedQty}</td><td class="text-right">${orderQty}</td><td class="text-right">${avgMonthlyUsage}</td><td class="text-right">${maxMonthlyUsage}</td><td class="text-right">${leadTimeDemand}</td><td class="text-right">${safetyStock}</td>`
            );
    });
});

let sel = document.getElementById('group-select');

sel.onchange = function () {
    document.getElementById("update-btn").href = this.value;
}

// TODO: learn promises, async, await in order to do color highlighting