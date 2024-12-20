<?php

// Database connection
function getDbConnection() {
    $db = new SQLite3(__DIR__ . '/../celebrities.db');
    if (!$db) {
        die("Database connection failed: " . SQLite3::lastErrorMsg());
    }
    return $db;
}

// Get filter parameters from the URL
$occupation = isset($_GET['occupation']) ? $_GET['occupation'] : '';
$birthPlace = isset($_GET['birth_place']) ? $_GET['birth_place'] : '';
$ageRange = isset($_GET['age_range']) ? $_GET['age_range'] : '';
$children = isset($_GET['children']) ? $_GET['children'] : '';

// Build SQL query based on the user input
$query = "
    SELECT c.name
    FROM celebrities c
    LEFT JOIN occupations o ON c.person_id = o.person_id
    LEFT JOIN relationships r ON c.person_id = r.person_id
    WHERE 1=1
";

// Apply filters if specified
if ($occupation) {
    $query .= " AND o.occupation LIKE '%" . SQLite3::escapeString($occupation) . "%'";
}
if ($birthPlace) {
    $query .= " AND c.birth_place LIKE '%" . SQLite3::escapeString($birthPlace) . "%'";
}
if ($ageRange) {
    list($minAge, $maxAge) = explode('-', $ageRange);
    // Assuming birth_date is in 'YYYY-MM-DD' format, we can calculate age based on today's date
    $currentYear = date('Y');
    $minYear = $currentYear - $maxAge;
    $maxYear = $currentYear - $minAge;
    $query .= " AND strftime('%Y', c.birth_date) BETWEEN $minYear AND $maxYear";
}
if ($children) {
    if ($children == '3+') {
        $query .= " AND r.num_children >= 3";
    } else {
        $query .= " AND r.num_children = $children";
    }
}

// Limit results
$query .= " LIMIT 10";

// Execute the query
$db = getDbConnection();
$results = $db->query($query);

// Initialize the output string
$output = '';
if ($row = $results->fetchArray()) {
    // Loop through and display celebrity names if any results are found
    do {
        $output .= "<p>" . htmlspecialchars($row['name']) . "</p>";
    } while ($row = $results->fetchArray());
} else {
    // If no results, display "Found no matches"
    $output = "<div class='no-matches-message'><p>Found no matches</p></div>";
}

// Output the results
echo $output;
exit;
?>