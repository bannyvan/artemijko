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

// Notify about unfinished sessions older than 15h
$stmt = $db->prepare("SELECT ws.id, e.telegram_id FROM work_sessions ws JOIN employees e ON ws.employee_id=e.id WHERE ws.status='active' AND ws.start_time < NOW() - INTERVAL 15 HOUR");
$stmt->execute();
foreach ($stmt->fetchAll(PDO::FETCH_ASSOC) as $row) {
    $bot->sendMessage($row['telegram_id'], "У вас есть незавершенная смена более 15 часов. Пожалуйста, завершите ее.");
}

// This script can also be extended to remind about start/end of shifts
