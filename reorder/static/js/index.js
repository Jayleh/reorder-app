function changeMonths(numMonths) {
    let $brand = d3.select('#brand').html();
    $numMonths = d3.select('#num-months'),
        $tbody = d3.select('table tbody'),
        $lastUpdate = d3.select('div#update-time > p');

    d3.json(`/all-data/${$brand}/${numMonths}`, (error, data) => {
        if (error) throw error;

        $numMonths
            .html(
                `${data['months_past_sellthrough']}`
            )

        $lastUpdate.selectAll('em').remove();

        $lastUpdate.append('em')
            .html(
                `${data['last_update']}`
            );

        $tbody.selectAll('tr').remove();

        (data['reorder_data']).forEach((item, index) => {

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
}

function init() {
    let numMonths = '3';

    changeMonths(numMonths);
}

init();

let sel = document.getElementById('group-select');

sel.onchange = function () {
    document.getElementById("update-btn").href = this.value;

    // console.log(this.value);

    numMonths = this.value.match(/\d+/)[0];

    // console.log(numMonths);

    if (numMonths !== 0) {
        changeMonths(numMonths);
    }
}

// let sel = d3.select('#group-select');

// sel.on('change', () => {

//     d3.select('#update-btn')
//         .attr('href', this.value);

//     console.log(this.value);
// });

// TODO: learn promises, async, await in order to do color highlighting