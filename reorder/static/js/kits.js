function removeRow(element) {
    let tableRow = element.parentNode.parentNode;

    tableRow.parentNode.removeChild(tableRow);
}

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

    // Add add icon to add row button
    let $addRowBtn = document.querySelector('#add-row-btn');

    // Table tbody
    let $tbody = document.querySelector('tbody');

    // Add rows listener
    $addRowBtn.addEventListener('click', function () {
        // Check steps
        if ($mainSku.value !== "" && $compQuant.value !== "") {
            // Get second to last row index
            let rowIndex = $tbody.rows.length - 1;

            // Create table row element
            let tableRow = $tbody.insertRow(rowIndex);

            // Create cells
            let cell1 = tableRow.insertCell(0),
                cell2 = tableRow.insertCell(1),
                cell3 = tableRow.insertCell(2);

            // Insert data in cells
            cell1.innerHTML = `<input name="final_product" value="${$mainSku.value}">`;
            cell2.innerHTML = `<input name="component_product" value="${$compQuant.value}">`;
            cell3.innerHTML = '<a class="btn-small waves-effect waves-light red remove-row-btn" onclick="removeRow(this)"><i class="material-icons center">remove_circle_outline</i></a>';

            // Reset input fields
            $mainSku.value = null;
            $compQuant.value = null;
        }
        else {
            // Alert with a toast
            M.toast({ html: 'Please check you input' })
        }
    });
});