document.addEventListener('DOMContentLoaded', function () {
    const tools = document.querySelector('.object-tools');

    const match = window.location.pathname.match(/\/(\d+)\/change\/$/);
    if (tools && match) {
        const orderId = match[1];
        const printBtn = document.createElement('a');
        printBtn.innerText = "🖨️ طباعة الطلب";
        printBtn.href = `/admin/store/order/${orderId}/print/`;
        printBtn.className = "button";
        tools.appendChild(printBtn);
    }
});
