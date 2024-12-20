document.getElementById('celebrity-relationship-form').addEventListener('submit', function(event) {
    event.preventDefault();  // Prevent the form from submitting and refreshing the page

    // Get the celebrity name from the form
    let celebrityName = document.getElementById('celebrity_name').value.trim();

    if (!celebrityName) {
        alert("Please enter a celebrity name.");
        return;
    }

    // Construct the query string with the celebrity name
    let queryString = `&celebrity_name=${encodeURIComponent(celebrityName)}`;

    // Perform an AJAX call to the PHP file with the celebrity name
    fetch('/db-final/php/relationships.php?' + queryString)
        .then(response => response.text())
        .then(data => {
            console.log('Data received:', data); // Log the data to check if it's returned correctly

            // If data is returned and not empty, show the results container
            if (data) {
                document.getElementById('results').innerHTML = data;
                document.getElementById('results').style.display = 'block'; // Show results
            } else {
                document.getElementById('results').innerHTML = '<p class="no-results">No relationships found for this celebrity.</p>';
                document.getElementById('results').style.display = 'block'; // Show results even if empty
            }
        })
        .catch(error => {
            console.error('Error fetching data:', error);
            document.getElementById('results').innerHTML = '<p class="no-results">Error fetching data. Please try again.</p>';
            document.getElementById('results').style.display = 'block'; // Show results even if error occurs
        });
});
