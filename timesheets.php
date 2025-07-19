<?php
require __DIR__ . '/vendor/autoload.php';
$config = file_exists(__DIR__ . '/src/bot/config.php')
    ? require __DIR__ . '/src/bot/config.php'
    : require __DIR__ . '/src/bot/config.sample.php';

$db = new PDO(
    "mysql:host={$config['db']['host']};dbname={$config['db']['database']};charset={$config['db']['charset']}",
    $config['db']['user'],
    $config['db']['password']
);

$token = $_GET['token'] ?? '';
$stmt = $db->prepare('SELECT expires_at FROM share_links WHERE token=?');
$stmt->execute([$token]);
$expires = $stmt->fetchColumn();
if (!$expires || strtotime($expires) < time()) {
    http_response_code(403);
    echo 'Недействительный или просроченный токен';
    exit;
}

if (isset($_GET['download']) && isset($_GET['employee'])) {
    $empId = (int)$_GET['employee'];
    $emp = $db->prepare('SELECT full_name FROM employees WHERE id=?');
    $emp->execute([$empId]);
    $name = $emp->fetchColumn();
    if (!$name) {
        http_response_code(404);
        exit('Сотрудник не найден');
    }
    $stmt = $db->prepare('SELECT date,start_time,end_time,total_hours FROM work_sessions WHERE employee_id=? ORDER BY date');
    $stmt->execute([$empId]);
    $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
    $spreadsheet = new PhpOffice\PhpSpreadsheet\Spreadsheet();
    $sheet = $spreadsheet->getActiveSheet();
    $sheet->fromArray(['Дата','Начало','Конец','Часы'], null, 'A1');
    $sheet->fromArray($rows, null, 'A2');
    header('Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
    header('Content-Disposition: attachment; filename="timesheet.xlsx"');
    $writer = new PhpOffice\PhpSpreadsheet\Writer\Xlsx($spreadsheet);
    $writer->save('php://output');
    exit;
}

$events = [];
$rows = $db->query('SELECT e.full_name, ws.start_time, ws.end_time FROM work_sessions ws JOIN employees e ON ws.employee_id = e.id')->fetchAll(PDO::FETCH_ASSOC);
foreach ($rows as $r) {
    $events[] = [
        'title' => $r['full_name'],
        'start' => $r['start_time'],
        'end' => $r['end_time']
    ];
}
$employees = $db->query('SELECT id, full_name FROM employees')->fetchAll(PDO::FETCH_ASSOC);
?>
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Календарь смен</title>
    <link href="https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/main.min.css" rel="stylesheet">
</head>
<body>
<div id="calendar"></div>
<h2>Экспорт</h2>
<ul>
<?php foreach ($employees as $emp): ?>
    <li><?= htmlspecialchars($emp['full_name']) ?> - <a href="timesheets.php?token=<?= htmlspecialchars($token) ?>&download=1&employee=<?= $emp['id'] ?>">Скачать Excel</a></li>
<?php endforeach; ?>
</ul>
<script src="https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/main.min.js"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {
  var calendarEl = document.getElementById('calendar');
  var calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'dayGridMonth',
    events: <?php echo json_encode($events, JSON_UNESCAPED_UNICODE); ?>
  });
  calendar.render();
});
</script>
</body>
</html>
