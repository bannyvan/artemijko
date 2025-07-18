<?php
// Simple script to manually edit work session times
require __DIR__ . '/../../vendor/autoload.php';
$config = file_exists(__DIR__ . '/../bot/config.php')
    ? require __DIR__ . '/../bot/config.php'
    : require __DIR__ . '/../bot/config.sample.php';

$db = new PDO(
    "mysql:host={$config['db']['host']};dbname={$config['db']['database']};charset={$config['db']['charset']}",
    $config['db']['user'],
    $config['db']['password']
);

$sessionId = (int)($_POST['session_id'] ?? 0);
$newStart = $_POST['start'] ?? null;
$newEnd = $_POST['end'] ?? null;
$reason = $_POST['reason'] ?? '';
$adminId = 1; // TODO: replace with real admin id from auth

if ($sessionId && $newStart && $newEnd) {
    $db->beginTransaction();
    $old = $db->prepare('SELECT start_time, end_time FROM work_sessions WHERE id=? FOR UPDATE');
    $old->execute([$sessionId]);
    $oldData = $old->fetch(PDO::FETCH_ASSOC);

    $upd = $db->prepare('UPDATE work_sessions SET start_time=?, end_time=? WHERE id=?');
    $upd->execute([$newStart, $newEnd, $sessionId]);

    $log = $db->prepare('INSERT INTO session_changes (session_id, old_start, old_end, new_start, new_end, reason, changed_by) VALUES (?,?,?,?,?,?,?)');
    $log->execute([$sessionId, $oldData['start_time'], $oldData['end_time'], $newStart, $newEnd, $reason, $adminId]);

    $db->commit();
    echo "Session updated";
} else {
    echo "Invalid data";
}
