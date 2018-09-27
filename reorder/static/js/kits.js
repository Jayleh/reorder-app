function removeRow(element) {
    let tableRow = element.parentNode.parentNode,
        $modal2 = document.querySelector('#modal2');

    let instance = M.Modal.getInstance($modal2);
    instance.open();

    let $deleteRowBtn = document.querySelector('#delete-row-btn');

    $deleteRowBtn.addEventListener('click', function() {
        tableRow.parentNode.removeChild(tableRow);
        instance.close();
    });
}

function disableButtons(buttonList) {
    // Disable all buttons
    buttonList.forEach(function (element) {
        element.classList.add('disabled');
    });
}

function enableButtons(buttonList) {
    // Disable all buttons
    buttonList.forEach(function (element) {
        element.classList.remove('disabled');
    });
}

document.addEventListener('DOMContentLoaded', function () {
    // Enable floating action button
    let $actionBtn = document.querySelectorAll('.fixed-action-btn');
    M.FloatingActionButton.init($actionBtn);

    // Enable tooltips
    let $toolTip = document.querySelectorAll('.tooltipped');
    M.Tooltip.init($toolTip);

    // Enable modal
    let $modal = document.querySelectorAll('.modal');
    M.Modal.init($modal);

    // Click event on flash message
    let $flashBtn = document.querySelector('#flash-close');

    if ($flashBtn) {
        $flashBtn.addEventListener("click", function () {
            let $flashToast = document.querySelector('#flash-toast');
            $flashToast.parentNode.removeChild($flashToast);
        });
    }

    // Input fields
    let $mainSku = document.querySelector('#main-sku'),
        $compQuant = document.querySelector('#comp-quant');

    // Buttons
    let $addRowBtn = document.querySelector('#add-row-btn'),
        $saveBtn = document.querySelector('#save-kits-btn');

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
            cell1.innerHTML = `<div class="input-field"><input name="final_product" value="${$mainSku.value}"></div>`;
            cell2.innerHTML = `<div class="input-field"><input name="component_product" value="${$compQuant.value}"></div>`;
            cell3.innerHTML = '<a class="btn-small waves-effect waves-light red remove-row-btn"><i class="material-icons center">remove_circle_outline</i></a>';

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