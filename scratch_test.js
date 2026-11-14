
    const bagsPurchasedInp = document.getElementById('id_bags_purchased');
    const costPerBagInp = document.getElementById('id_cost_per_bag');
    const purchaseTotalSpan = document.getElementById('calc_purchase_total');

    function recalcPurchase() {
        const bags = parseFloat(bagsPurchasedInp ? bagsPurchasedInp.value : 0) || 0;
        const cost = parseFloat(costPerBagInp ? costPerBagInp.value : 0) || 0;
        const total = bags * cost;
        if (purchaseTotalSpan) purchaseTotalSpan.textContent = '$' + total.toFixed(2);
    }

    [bagsPurchasedInp, costPerBagInp].forEach(inp => {
        if(inp) inp.addEventListener('input', recalcPurchase);
    });

    recalcPurchase();

    function handlePurchaseSubmit(form, e) {
        const btn = document.getElementById('savePurchaseBtn');
        const btnText = document.getElementById('purchaseBtnText');
        const btnIcon = document.getElementById('purchaseBtnIcon');

        if (btn) {
            btn.disabled = true;
            btnText.textContent = 'Saving Delivery...';
            btnIcon.innerHTML = '<svg class="animate-spin h-4 w-4 text-white inline-block mr-1" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg>';
        }
    }
