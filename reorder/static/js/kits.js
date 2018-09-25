document.addEventListener('DOMContentLoaded', function () {
    // Enable floating action button
    let $actionBtn = document.querySelectorAll('.fixed-action-btn');
    M.FloatingActionButton.init($actionBtn);

    // Enable tooltips
    let $toolTip = document.querySelectorAll('.tooltipped');
    M.Tooltip.init($toolTip);

    // Input fields
    let $mainSku = document.querySelector('#main-sku'),
        $compQuant = document.querySelector('#comp-quant');

    // Buttons
    let $addRowBtn = document.querySelector('#add-row-btn');

    // Table
    let $tbody = document.querySelector('tbody');

    $addRowBtn.addEventListener('click', function () {
        console.log($mainSku.value);
        console.log($compQuant.value);

        // Create table row element
        let tableRow = $tbody.insertRow()

        // Create cells
        let cell1 = tableRow.insertCell(0),
            cell2 = tableRow.insertCell(1),
            cell3 = tableRow.insertCell(2);

        // Insert data in cells
        cell1.innerHTML = `${$mainSku.value}`;
        cell2.innerHTML = `${$compQuant.value}`;
        cell3.innerHTML = '<a class="btn-small waves-effect waves-light"><i class="material-icons center">remove_circle_outline</i></a>';
    });

    //
});