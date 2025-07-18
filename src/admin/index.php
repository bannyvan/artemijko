<?php
session_start();
if (!isset($_SESSION['admin_id'])) {
    header('Location: login.php');
    exit;
}

// Placeholder for admin panel
// Future implementation will use Bootstrap and AdminLTE

echo "<h1>Admin Panel in development</h1>";
