<?php
require __DIR__ . '/../vendor/autoload.php';
$config = file_exists(__DIR__ . '/../src/bot/config.php')
    ? require __DIR__ . '/../src/bot/config.php'
    : require __DIR__ . '/../src/bot/config.sample.php';

use TelegramBot\Api\BotApi;

$bot = new BotApi($config['bot_token']);
$db = new PDO(
    "mysql:host={$config['db']['host']};dbname={$config['db']['database']};charset={$config['db']['charset']}",
    $config['db']['user'],
    $config['db']['password']
);

// Send weekly statistics (sum of hours for last 7 days)
$stmt = $db->query("SELECT employee_id, SUM(total_hours) AS hours FROM work_sessions WHERE date >= CURDATE() - INTERVAL 7 DAY GROUP BY employee_id");
$stats = $stmt->fetchAll(PDO::FETCH_ASSOC);

foreach ($stats as $row) {
    $emp = $db->prepare('SELECT telegram_id FROM employees WHERE id=?');
    $emp->execute([$row['employee_id']]);
    $tg = $emp->fetchColumn();
    if ($tg) {
        $bot->sendMessage($tg, "Ваши отработанные часы за неделю: {$row['hours']}");
    }
}

// Extend to monthly statistics as needed
