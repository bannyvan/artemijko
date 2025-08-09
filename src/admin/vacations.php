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

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $id = (int)($_POST['id'] ?? 0);
    $action = $_POST['action'] ?? '';
    if ($id && in_array($action, ['approved', 'rejected'], true)) {
        $stmt = $db->prepare('UPDATE vacation_requests SET status=? WHERE id=?');
        $stmt->execute([$action, $id]);
    }
}

$stmt = $db->query('SELECT vr.id, e.full_name, vr.start_date, vr.end_date, vr.type, vr.comment, vr.status FROM vacation_requests vr JOIN employees e ON vr.employee_id=e.id ORDER BY vr.created_at DESC');
$requests = $stmt->fetchAll(PDO::FETCH_ASSOC);
?>
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Заявки на отпуск</title>
</head>
<body>
<h1>Заявки на отпуск</h1>
<table border="1" cellpadding="5" cellspacing="0">
    <tr>
        <th>Сотрудник</th>
        <th>Период</th>
        <th>Тип</th>
        <th>Комментарий</th>
        <th>Статус</th>
        <th>Действие</th>
    </tr>
    <?php foreach ($requests as $r): ?>
        <tr>
            <td><?= htmlspecialchars($r['full_name']) ?></td>
            <td><?= htmlspecialchars($r['start_date']) ?> - <?= htmlspecialchars($r['end_date']) ?></td>
            <td><?= htmlspecialchars($r['type']) ?></td>
            <td><?= htmlspecialchars($r['comment']) ?></td>
            <td><?= htmlspecialchars($r['status']) ?></td>
            <td>
                <?php if ($r['status'] === 'pending'): ?>
                    <form method="post" style="display:inline">
                        <input type="hidden" name="id" value="<?= $r['id'] ?>">
                        <button name="action" value="approved">Одобрить</button>
                    </form>
                    <form method="post" style="display:inline">
                        <input type="hidden" name="id" value="<?= $r['id'] ?>">
                        <button name="action" value="rejected">Отклонить</button>
                    </form>
                <?php else: ?>
                    -
                <?php endif; ?>
            </td>
        </tr>
    <?php endforeach; ?>
</table>
</body>
</html>

