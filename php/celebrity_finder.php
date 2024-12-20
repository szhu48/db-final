<?php

// Database connection
function getDbConnection() {
    $db = new SQLite3(__DIR__ . '/../celebrities.db');
    if (!$db) {
        die("Database connection failed: " . SQLite3::lastErrorMsg());
    }
    return $db;
}

// Handle search for celebrity by name
if (isset($_GET['search'])) {
    $search = $_GET['search'];
    $db = getDbConnection();

    // Query the database for celebrities matching the search name
    $stmt = $db->prepare("SELECT person_id, birth_name, birth_date, birth_place FROM celebrities WHERE name LIKE :search LIMIT 10");
    if (!$stmt) {
        die("Failed to prepare SQL query: " . $db->lastErrorMsg());
    }
    $stmt->bindValue(':search', '%' . $search . '%', SQLITE3_TEXT);
    $results = $stmt->execute();

    // Initialize an empty string for displaying results
    $output = '';

    // Fetch and display results
    while ($row = $results->fetchArray()) {
        $output .= "<div class='celebrity-card'>";
        $output .= "<h3>" . htmlspecialchars($row['person_id']) . "</h3>";
        $output .= "<p>Birth Name: " . htmlspecialchars($row['birth_name']) . "</p>";
        $output .= "<p>Birth Date: " . htmlspecialchars($row['birth_date']) . "</p>";
        $output .= "<p>Born in: " . htmlspecialchars($row['birth_place']) . "</p>";
        $output .= "</div>";
    }

    // Output the results
    echo $output;
    exit;
}
?>
