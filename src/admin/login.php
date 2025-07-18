<?php
session_start();
require __DIR__ . '/../../vendor/autoload.php';
$config = file_exists(__DIR__ . '/../bot/config.php')
    ? require __DIR__ . '/../bot/config.php'
    : require __DIR__ . '/../bot/config.sample.php';

$db = new PDO(
    "mysql:host={$config['db']['host']};dbname={$config['db']['database']};charset={$config['db']['charset']}",
    $config['db']['user'],
    $config['db']['password']
);

$error = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = $_POST['username'] ?? '';
    $password = $_POST['password'] ?? '';
    $stmt = $db->prepare('SELECT id, password_hash FROM admins WHERE username=?');
    $stmt->execute([$username]);
    $row = $stmt->fetch(PDO::FETCH_ASSOC);
    if ($row && password_verify($password, $row['password_hash'])) {
        $_SESSION['admin_id'] = $row['id'];
        header('Location: index.php');
        exit;
    }
    $error = 'Неверный логин или пароль';
}
?>
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Вход</title>
    <link rel="stylesheet" href="assets/css/style.css">
</head>
<body>
<header>
    <h1>Панель администратора</h1>
</header>
<main>
    <form method="post">
        <h2>Вход</h2>
        <input type="text" name="username" placeholder="Логин">
        <input type="password" name="password" placeholder="Пароль">
        <button type="submit">Войти</button>
        <?php if ($error) echo '<p id="error">' . $error . '</p>'; ?>
    </form>
</main>
<script src="assets/js/menu.js"></script>
</body>
</html>
