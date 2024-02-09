document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('searchBtn').addEventListener('click', function() {
        document.getElementById('actionInput').value = 'search';
        document.getElementById('pokemonForm').submit();
    });

    document.getElementById('previousBtn').addEventListener('click', function() {
        document.getElementById('actionInput').value = 'previous';
        document.getElementById('pokemonForm').submit();
    });

    document.getElementById('nextBtn').addEventListener('click', function() {
        document.getElementById('actionInput').value = 'next';
        document.getElementById('pokemonForm').submit();
    });
});