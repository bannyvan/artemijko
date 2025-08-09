<?php
session_start();
if (!isset($_SESSION['admin_id'])) {
    header('Location: login.php');
    exit;
}

echo "<h1>Admin Panel</h1>";
echo "<ul>";
echo "<li><a href='vacations.php'>Заявки на отпуск</a></li>";
echo "</ul>";
