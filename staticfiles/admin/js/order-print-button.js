document.addEventListener('DOMContentLoaded', function () {
    const tools = document.querySelector('.object-tools');

    // Match pattern like: /admin/store/order/119/change/
    const match = window.location.pathname.match(/^\/admin\/store\/order\/(\d+)\/change\/$/);
    
    if (tools && match) {
        const orderId = match[1];
        const printBtn = document.createElement('a');
        printBtn.innerText = "🖨️ طباعة الطلب";
        printBtn.href = `/admin/store/order/${orderId}/print/`;  // correct URL
        printBtn.className = "button";
        tools.appendChild(printBtn);
    }
});
