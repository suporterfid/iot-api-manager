document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.filter-input').forEach(input => {
        input.addEventListener('change', function () {
            const form = this.closest('form');
            fetch(form.action, {
                method: 'GET',
                body: new URLSearchParams(new FormData(form))
            }).then(response => response.text())
            .then(html => {
                document.querySelector('#rule-list-container').innerHTML = html;
            });
        });
    });
});
