document.addEventListener("DOMContentLoaded", function () {
    function checkNewOrders() {
        fetch("/admin/store/order/check-new-orders/")
            .then(response => response.json())
            .then(data => {
                if (data.new_orders > 0) {
                    showNotification(data.new_orders);
                }
            })
            .catch(error => console.error("Error checking new orders:", error));
    }

    function showNotification(orderCount) {
        let existing = document.getElementById("order-notification");
        if (!existing) {
            const notification = document.createElement("div");
            notification.id = "order-notification";
            notification.innerText = `📢 يوجد ${orderCount} طلب جديد`;
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: green;
                color: white;
                padding: 10px 15px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                z-index: 9999;
                box-shadow: 0 0 10px rgba(0,0,0,0.2);
            `;
            document.body.appendChild(notification);

            const sound = document.getElementById("order-sound");
            if (sound) sound.play();

            setTimeout(() => notification.remove(), 6000);
        }
    }

    setInterval(checkNewOrders, 15000); // كل 15 ثانية
});
