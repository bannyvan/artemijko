document.addEventListener('DOMContentLoaded', function() {
    const nav = document.querySelector('nav');
    const toggle = document.querySelector('.menu-toggle');
    if (toggle) {
        toggle.addEventListener('click', function() {
            nav.classList.toggle('open');
        });
    }
});
