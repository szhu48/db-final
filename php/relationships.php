<?php

// Database connection
function getDbConnection() {
    $db = new SQLite3(__DIR__ . '/../celebrities.db');
    if (!$db) {
        die("Database connection failed: " . SQLite3::lastErrorMsg());
    }
    return $db;
}

// Get the celebrity name from the query string
$celebrityName = isset($_GET['celebrity_name']) ? $_GET['celebrity_name'] : '';

// Build the SQL query to get relationship data for the celebrity
$query = "
    SELECT c.name, r.spouse, r.partner
    FROM celebrities c
    LEFT JOIN relationships r ON c.person_id = r.person_id
    WHERE c.name LIKE '%" . SQLite3::escapeString($celebrityName) . "%'
";

// Execute the query
$db = getDbConnection();
$results = $db->query($query);

// Initialize the output string
$output = '';
$relationshipFound = false;

// Loop through the results and build the output for each relationship
while ($row = $results->fetchArray()) {
    // Check if there is a spouse or partner and display accordingly
    if ($row['spouse'] || $row['partner']) {
        $output .= "<div class='celebrity-card'>";
        $output .= "<h3>" . htmlspecialchars($row['name']) . "</h3>";
        
        // Display spouse information
        if ($row['spouse']) {
            $output .= "<p><strong>Spouse(s):</strong> " . htmlspecialchars($row['spouse']) . "</p>";
        }
        
        // Display partner information
        if ($row['partner']) {
            $output .= "<p><strong>Partner(s):</strong> " . htmlspecialchars($row['partner']) . "</p>";
        }
        
        $output .= "</div>";
        
        // Set flag to true indicating relationships were found
        $relationshipFound = true;
    }
}

// If no relationships were found, output a message
if (!$relationshipFound) {
    $output = "<p>No relationship history found for this celebrity.</p>";
}

// Output the results
echo $output;
exit;
?>