<?php
// Database connection function
function getDbConnection() {
    // Connect to the SQLite database
    $db = new SQLite3('celebrities.db');
    return $db;
}

// Handle search request
if (isset($_GET['search'])) {
    $search = $_GET['search'];
    $db = getDbConnection();

    // Query the database for celebrities matching the search term
    $stmt = $db->prepare("SELECT * FROM celebrities WHERE name LIKE :search LIMIT 10");
    $stmt->bindValue(':search', '%'.$search.'%', SQLITE3_TEXT);
    $results = $stmt->execute();

    // Initialize an empty string for displaying results
    $output = '';

    // Fetch and display results
    while ($row = $results->fetchArray()) {
        $output .= "<div class='celebrity-card'>";
        $output .= "<h3>" . htmlspecialchars($row['name']) . "</h3>";
        $output .= "<p>Born: " . htmlspecialchars($row['birth_date']) . " in " . htmlspecialchars($row['birth_place']) . "</p>";
        $output .= "</div>";
    }

    // Output the results
    echo $output;
    exit;
}
?>