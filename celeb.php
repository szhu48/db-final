<?php
// Connect to database
$dbhost = 'dbase.cs.jhu.edu';
$dbuser = 'cs415_fa24_szhu48';
$dbpass = 'mCzqdpDxRw';
$dbname = 'cs415_fa24_szhu48_db';

$conn = new mysqli($dbhost, $dbuser, $dbpass, $dbname);

if ($conn->connect_error) {
    die('Error connecting to MySQL: ' . $conn->connect_error);
}

// Initialize variables for search filters and results
$birthYear = $_GET['birthYear'] ?? '';
$birthPlace = $_GET['birthPlace'] ?? '';
$occupation = $_GET['occupation'] ?? '';
$results = [];

if ($_SERVER['REQUEST_METHOD'] === 'GET' && (!empty($birthYear) || !empty($birthPlace) || !empty($occupation))) {
    $query = "SELECT c.name, c.birth_date, c.birth_place, o.occupation 
              FROM celebrities c 
              LEFT JOIN occupations o ON c.person_id = o.person_id 
              WHERE 1=1";
    $params = [];
    $types = "";

    if ($birthYear) {
        $query .= " AND strftime('%Y', c.birth_date) = ?";
        $params[] = $birthYear;
        $types .= "s";
    }

    if ($birthPlace) {
        $query .= " AND c.birth_place LIKE ?";
        $params[] = "%$birthPlace%";
        $types .= "s";
    }

    if ($occupation) {
        $query .= " AND o.occupation LIKE ?";
        $params[] = "%$occupation%";
        $types .= "s";
    }

    $stmt = $conn->prepare($query);

    if ($types) {
        $stmt->bind_param($types, ...$params);
    }

    $stmt->execute();
    $result = $stmt->get_result();

    while ($row = $result->fetch_assoc()) {
        $results[] = $row;
    }

    $stmt->close();
}

$conn->close();
?>