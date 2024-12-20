document.getElementById('celebrity-filter-form').addEventListener('submit', function(event) {
    event.preventDefault();  // Prevent the form from submitting and refreshing the page

    // Get the filter values from the form
    let occupation = document.getElementById('occupation').value.trim();
    let birthPlace = document.getElementById('birth_place').value.trim();
    let ageRange = document.getElementById('age_range').value;
    let children = document.getElementById('children').value;

    // Validate that at least one field is filled
    if (!occupation && !birthPlace && !ageRange && !children) {
        alert("Please fill out at least one filter field.");
        return; // Stop the form submission if no field is filled
    }

    // Construct the query string with all filters
    let queryString = '';
    if (occupation) queryString += `&occupation=${encodeURIComponent(occupation)}`;
    if (birthPlace) queryString += `&birth_place=${encodeURIComponent(birthPlace)}`;
    if (ageRange) queryString += `&age_range=${encodeURIComponent(ageRange)}`;
    if (children) queryString += `&children=${encodeURIComponent(children)}`;

    // Perform an AJAX call to the PHP file with the filters
    fetch('/db-final/php/matchmaking.php?' + queryString)
        .then(response => response.text())
        .then(data => {
            const resultsContainer = document.getElementById('results');
            // Show the results container (after the form is submitted)
            resultsContainer.style.display = 'block';
            // Update the results section with the fetched data (celebrity names or "Found no matches")
            resultsContainer.innerHTML = data;
        })
        .catch(error => {
            console.error('Error fetching data:', error);
        });
});
