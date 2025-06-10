class OrderActions {
    static async copyOrder(orderId) {
        try {
            const response = await fetch(`/api/orders/${orderId}/copy/`);
            const data = await response.json();
            
            if (data.success) {
                await navigator.clipboard.writeText(data.order_text);
                this.showSuccess('تم نسخ الطلب بنجاح!');
            } else {
                this.showError('حدث خطأ في نسخ الطلب: ' + data.error);
            }
        } catch (error) {
            console.error('Error:', error);
            this.showError('حدث خطأ في نسخ الطلب');
        }
    }
    
    static async printOrder(orderId) {
        try {
            const response = await fetch(`/api/orders/${orderId}/print/`);
            const data = await response.json();
            
            if (data.success) {
                const printWindow = window.open('', '_blank');
                printWindow.document.write(this.generatePrintHTML(data.data));
                printWindow.document.close();
                printWindow.focus();
                printWindow.print();
            } else {
                this.showError('حدث خطأ في طباعة الطلب: ' + data.error);
            }
        } catch (error) {
            console.error('Error:', error);
            this.showError('حدث خطأ في طباعة الطلب');
        }
    }
    
    static showSuccess(message) {
        // Create success notification
        const notification = document.createElement('div');
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed; top: 20px; right: 20px; z-index: 10000;
            background: #28a745; color: white; padding: 15px;
            border-radius: 5px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        `;
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 3000);
    }
    
    static showError(message) {
        alert(message);
    }
    
    static generatePrintHTML(orderData) {
        // Same HTML generation as above...
        return `<!DOCTYPE html>...`; // Copy from above
    }
}

// Make functions globally available
window.copyOrder = (orderId) => OrderActions.copyOrder(orderId);
window.printOrder = (orderId) => OrderActions.printOrder(orderId);