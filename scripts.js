document.getElementById('search').addEventListener('input', function() {
    let search = this.value.trim();  // Trim whitespace

    // If the search term is empty, clear the results
    if (search === '') {
        document.getElementById('results').innerHTML = '';
        return;
    }

    // Perform an AJAX call to the PHP file with the search term
    fetch('procedures.php?search=' + encodeURIComponent(search))
        .then(response => response.text())
        .then(data => {
            // Update the results section with the fetched data
            document.getElementById('results').innerHTML = data;
        });
});
