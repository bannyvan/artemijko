<?php
session_start();
if (!isset($_SESSION['admin_id'])) {
    header('Location: login.php');
    exit;
}
?>
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Панель администратора</title>
    <link rel="stylesheet" href="assets/css/style.css">
</head>
<body>
<header>
    <h1>Панель администратора</h1>
    <button onclick="toggleMenu()">☰ Меню</button>
    <nav id="nav" style="display:none;">
        <ul>
            <li><a href="index.php">Главная</a></li>
            <li><a href="edit_session.php">Редактировать смену</a></li>
            <li><a href="logout.php">Выход</a></li>
        </ul>
    </nav>
</header>
<main>
    <h2>Добро пожаловать!</h2>
    <p>Админпанель находится в разработке.</p>
</main>
<script src="assets/js/menu.js"></script>
</body>
</html>
