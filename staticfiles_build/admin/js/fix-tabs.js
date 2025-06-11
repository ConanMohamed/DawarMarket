document.addEventListener('DOMContentLoaded', function () {
    const hash = window.location.hash;
    if (hash) {
        const tabTrigger = document.querySelector(`a[href="${hash}"]`);
        if (tabTrigger) {
            tabTrigger.click();
        }
    }

    // حفظ آخر تبويب
    const tabLinks = document.querySelectorAll('.nav-tabs a');
    tabLinks.forEach(tab => {
        tab.addEventListener('click', function () {
            history.replaceState(null, null, this.getAttribute('href'));
        });
    });
});
