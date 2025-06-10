document.addEventListener('DOMContentLoaded', function() {
    // Match both /admin/store/order/1/change/ and /admin/store/order/1/change
    const match = window.location.pathname.match(/\/admin\/store\/order\/(\d+)\/change\/?$/);
    
    if (match) {
        const orderId = match[1];
        const tools = document.querySelector('.object-tools');
        
        if (tools) {
            const printBtn = document.createElement('a');
            printBtn.innerText = "🖨️ طباعة الطلب";
            printBtn.href = `/admin/store/order/${orderId}/print/`;
            printBtn.className = "button";
            printBtn.style.marginLeft = "10px";
            tools.appendChild(printBtn);
        }
    }
});