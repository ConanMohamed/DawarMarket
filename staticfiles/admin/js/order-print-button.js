document.addEventListener('DOMContentLoaded', function () {
    const tools = document.querySelector('.object-tools');
    if (tools) {
        const printBtn = document.createElement('a');
        printBtn.innerText = "🖨️ طباعة الطلب";
        printBtn.href = window.location.pathname + "print/";
        printBtn.className = "button"
        tools.appendChild(printBtn);
    }
});
