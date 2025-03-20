document.addEventListener("DOMContentLoaded", function () {
    function checkNewOrders() {
        fetch("/admin/store/order/check-new-orders/")
            .then(response => response.json())
            .then(data => {
                if (data.new_orders > 0) {
                    showNotification(data.new_orders);
                    refreshOrdersList();
                }
            })
            .catch(error => console.error("Error fetching new orders:", error));
    }

    function showNotification(orderCount) {
        let existingNotification = document.getElementById("order-notification");
        if (!existingNotification) {
            const notification = document.createElement("div");
            notification.id = "order-notification";
            notification.innerText = `📢 لديك ${orderCount} طلبات جديدة!`;
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: red;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
                z-index: 9999;
            `;
            document.body.appendChild(notification);

            setTimeout(() => notification.remove(), 5000); // يحذف الإشعار بعد 5 ثواني
        }
    }

    function refreshOrdersList() {
        fetch(window.location.href) // جلب البيانات بدون ريفريش
            .then(response => response.text())
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, "text/html");
                const newOrdersTable = doc.querySelector(".results"); // استبدل بالـ class الخاص بالجدول

                const currentOrdersTable = document.querySelector(".results");
                if (currentOrdersTable && newOrdersTable) {
                    currentOrdersTable.innerHTML = newOrdersTable.innerHTML;
                }
            })
            .catch(error => console.error("Error refreshing orders:", error));
    }

    setInterval(checkNewOrders, 10000); // يفحص الطلبات كل 10 ثواني
});



document.addEventListener("DOMContentLoaded", function () {
    function updateOrderPrices() {
        document.querySelectorAll(".field-total_price_display").forEach(function (element) {
            const orderId = element.parentElement.querySelector(".field-id").innerText.trim();
            fetch(`/admin/store/order/update-order-total/${orderId}/`)
                .then(response => response.json())
                .then(data => {
                    element.innerHTML = `<strong>${data.total_price} EGP</strong>`;
                })
                .catch(error => console.error("Error updating order price:", error));
        });
    }

    setInterval(updateOrderPrices, 10000); // تحديث كل 10 ثواني
});
