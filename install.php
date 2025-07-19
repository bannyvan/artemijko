<?php
if (file_exists(__DIR__ . '/src/bot/config.php')) {
    echo 'Установка уже выполнена.';
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $botToken = trim($_POST['bot_token'] ?? '');
    $dbHost = trim($_POST['db_host'] ?? 'localhost');
    $dbName = trim($_POST['db_name'] ?? '');
    $dbUser = trim($_POST['db_user'] ?? '');
    $dbPass = trim($_POST['db_pass'] ?? '');
    $dbCharset = trim($_POST['db_charset'] ?? 'utf8mb4');
    $adminUser = trim($_POST['admin_user'] ?? '');
    $adminPass = trim($_POST['admin_pass'] ?? '');
    $webhook = trim($_POST['webhook'] ?? '');

    $config = "<?php\nreturn [\n    'bot_token' => '" . addslashes($botToken) . "',\n    'db' => [\n        'host' => '" . addslashes($dbHost) . "',\n        'database' => '" . addslashes($dbName) . "',\n        'user' => '" . addslashes($dbUser) . "',\n        'password' => '" . addslashes($dbPass) . "',\n        'charset' => '" . addslashes($dbCharset) . "'\n    ]\n];\n";
    file_put_contents(__DIR__ . '/src/bot/config.php', $config);

    try {
        $pdo = new PDO("mysql:host=$dbHost;dbname=$dbName;charset=$dbCharset", $dbUser, $dbPass);
        $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    } catch (PDOException $e) {
        exit('Ошибка подключения к БД: ' . $e->getMessage());
    }

    $schema = file_get_contents(__DIR__ . '/database/schema.sql');
    foreach (explode(";", $schema) as $sql) {
        $sql = trim($sql);
        if ($sql) {
            $pdo->exec($sql);
        }
    }

    if ($adminUser && $adminPass) {
        $hash = password_hash($adminPass, PASSWORD_DEFAULT);
        $stmt = $pdo->prepare('INSERT INTO admins (username, password_hash) VALUES (?, ?)');
        $stmt->execute([$adminUser, $hash]);
    }

    if ($webhook) {
        $url = "https://api.telegram.org/bot{$botToken}/setWebhook?url=" . urlencode($webhook);
        @file_get_contents($url);
    }

    echo 'Установка завершена.';
    exit;
}
?>
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Установка</title>
</head>
<body>
<h1>Установка системы</h1>
<form method="post">
    <h2>Настройки базы данных</h2>
    <input type="text" name="db_host" placeholder="Хост" value="localhost"><br>
    <input type="text" name="db_name" placeholder="База данных"><br>
    <input type="text" name="db_user" placeholder="Пользователь"><br>
    <input type="password" name="db_pass" placeholder="Пароль"><br>
    <input type="text" name="db_charset" value="utf8mb4" placeholder="Кодировка"><br>
    <h2>Telegram</h2>
    <input type="text" name="bot_token" placeholder="Токен бота"><br>
    <input type="text" name="webhook" placeholder="URL вебхука"><br>
    <h2>Администратор</h2>
    <input type="text" name="admin_user" placeholder="Логин"><br>
    <input type="password" name="admin_pass" placeholder="Пароль"><br><br>
    <button type="submit">Установить</button>
</form>
</body>
</html>
