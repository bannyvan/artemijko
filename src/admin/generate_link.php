<?php
session_start();
if (!isset($_SESSION['admin_id'])) {
    header('Location: login.php');
    exit;
}

require __DIR__ . '/../../vendor/autoload.php';
$config = file_exists(__DIR__ . '/../bot/config.php')
    ? require __DIR__ . '/../bot/config.php'
    : require __DIR__ . '/../bot/config.sample.php';

$db = new PDO(
    "mysql:host={$config['db']['host']};dbname={$config['db']['database']};charset={$config['db']['charset']}",
    $config['db']['user'],
    $config['db']['password']
);

$link = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $token = bin2hex(random_bytes(16));
    $expires = date('Y-m-d H:i:s', time() + 7 * 24 * 3600); // 7 days
    $stmt = $db->prepare('INSERT INTO share_links (token, expires_at) VALUES (?, ?)');
    $stmt->execute([$token, $expires]);
    $link = '/timesheets.php?token=' . $token;
}
?>
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Сгенерировать ссылку</title>
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
            <li><a href="generate_link.php">Поделиться календарем</a></li>
            <li><a href="logout.php">Выход</a></li>
        </ul>
    </nav>
</header>
<main>
    <h2>Ссылка для общего доступа</h2>
    <?php if ($link): ?>
        <p><a href="<?= $link ?>" target="_blank"><?= $link ?></a></p>
    <?php else: ?>
        <form method="post">
            <button type="submit">Создать ссылку</button>
        </form>
    <?php endif; ?>
</main>
<script src="assets/js/menu.js"></script>
</body>
</html>
