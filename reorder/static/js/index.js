function changeMonths(numMonths) {
    let $brand = d3.select('#brand').html(),
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
                `Last update on ${data['last_update']} PST`
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

function dimPage() {
    // Dim page contents and display preloader
    let $main = document.querySelectorAll('.container'),
        $preloader = document.querySelector('#preloader-container');

    $main.forEach(function (element) {
        element.setAttribute("style", "opacity: 0.2;")
    });

    $preloader.setAttribute("style", "display: unset;")
}

function disableButtons(buttonList) {
    // Disable all buttons
    buttonList.forEach(function (element) {
        element.classList.add('disabled');
    });
}

function checkSelectField(sel, selBtn) {
    if (sel.value !== "javascript:void(0)") {
        selBtn.classList.remove('disabled');
    }
    else {
        selBtn.classList.add('disabled');
    }
}

document.addEventListener('DOMContentLoaded', function () {
    // Enable floating action button
    let $actionBtn = document.querySelectorAll('.fixed-action-btn');
    M.FloatingActionButton.init($actionBtn);

    // Enable tooltips
    let $toolTip = document.querySelectorAll('.tooltipped');
    M.Tooltip.init($toolTip);

    // Enable select
    let $select = document.querySelectorAll('select');
    M.FormSelect.init($select);

    // Click event on flash message
    let $flashBtn = document.querySelector('#flash-close');

    if ($flashBtn) {
        $flashBtn.addEventListener("click", function () {
            let $flashToast = document.querySelector('#flash-toast');
            $flashToast.parentNode.removeChild($flashToast);
        });
    }

    // List all buttons
    let $updateBtn = document.querySelector('#update-btn'),
        $sohUpdateBtn = document.querySelector('#soh-update-btn'),
        $salesUpdateBtn = document.querySelector('#sales-update-btn'),
        buttonList = [$updateBtn, $sohUpdateBtn, $salesUpdateBtn];


    // Select fields
    let $sellSelect = document.querySelector('#group-select'),
        $salesSelect = document.querySelector('#sales-group-select');

    $sellSelect.addEventListener('change', function () {
        // Change href value for sell through update
        document.querySelector('#update-btn').href = this.value;

        // console.log(this.value);

        let numMonths = this.value.match(/\d+/)[0];

        if (numMonths !== '0') {
            changeMonths(numMonths);
        }

        // Disable update button if no option selected
        checkSelectField($sellSelect, $updateBtn)
    });

    $salesSelect.addEventListener('change', function () {
        // Change href value for sales orders update
        document.querySelector('#sales-update-btn').href = this.value;

        // Disable update button if no option selected
        checkSelectField($salesSelect, $salesUpdateBtn)
    });

    // Click event on each update button
    buttonList.forEach((element, index) => {
        element.addEventListener("click", function () {
            if (element.href !== "javascript:void(0)") {
                // Alert with a toast
                M.toast({ html: 'This may be a minute' });

                // Dimmer
                dimPage();

                // Disable all buttons
                disableButtons(buttonList);
            }
        });
    })
});
