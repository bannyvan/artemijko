<?php
require __DIR__ . '/../../vendor/autoload.php';

// Load user configuration
$config = file_exists(__DIR__ . '/config.php')
    ? require __DIR__ . '/config.php'
    : require __DIR__ . '/config.sample.php';

use TelegramBot\Api\BotApi;
use TelegramBot\Api\Types\Update;
use TelegramBot\Api\Types\ReplyKeyboardMarkup;
use TelegramBot\Api\Types\Inline\InlineKeyboardMarkup;

require_once __DIR__ . '/db.php';

$bot = new BotApi($config['bot_token']);

function mainMenu(): string
{
    return json_encode([
        'keyboard' => [
            ['📅 Начать смену', '🛑 Закончить смену'],
            ['📊 Моя статистика', '⚙️ Профиль']
        ],
        'resize_keyboard' => true
    ]);
}

$update = json_decode(file_get_contents('php://input'), true);

if (!$update) {
    exit;
}

$updateObj = Update::fromResponse($update);
$message = $updateObj->getMessage();
$chatId = $message->getChat()->getId();
$text = trim($message->getText());
$db = getDb($config);
$employee = getEmployee($db, $chatId);
$registration = getRegistration($db, $chatId);

if ($text === '/start') {
    if ($employee) {
        $bot->sendMessage($chatId, 'Вы уже зарегистрированы.', null, false, null, mainMenu());
    } else {
        startRegistration($db, $chatId);
        $bot->sendMessage($chatId, 'Добро пожаловать! Пожалуйста, введите ваше ФИО:');
    }
    exit;
}

if ($registration && !$employee) {
    switch ((int)$registration['step']) {
        case 1:
            updateRegistration($db, $chatId, ['full_name' => $text, 'step' => 2]);
            $bot->sendMessage($chatId, 'Введите дату рождения (ДД.ММ.ГГГГ):');
            break;
        case 2:
            if (!preg_match('/^\d{2}\.\d{2}\.\d{4}$/', $text)) {
                $bot->sendMessage($chatId, 'Неверный формат. Используйте ДД.ММ.ГГГГ:');
                break;
            }
            $date = DateTime::createFromFormat('d.m.Y', $text)->format('Y-m-d');
            updateRegistration($db, $chatId, ['birth_date' => $date, 'step' => 3]);
            $companies = $db->query('SELECT name FROM companies')->fetchAll(PDO::FETCH_COLUMN);
            $buttons = array_map(fn($c) => [$c], $companies);
            $markup = json_encode(['keyboard' => $buttons, 'one_time_keyboard' => true, 'resize_keyboard' => true]);
            $bot->sendMessage($chatId, 'Выберите компанию:', null, false, null, $markup);
            break;
        case 3:
            $stmt = $db->prepare('SELECT id FROM companies WHERE name=?');
            $stmt->execute([$text]);
            $cid = $stmt->fetchColumn();
            if (!$cid) {
                $bot->sendMessage($chatId, 'Компания не найдена, попробуйте ещё раз:');
                break;
            }
            updateRegistration($db, $chatId, ['company_id' => $cid, 'step' => 4]);
            $bot->sendMessage($chatId, 'Введите город работы:');
            break;
        case 4:
            updateRegistration($db, $chatId, ['city' => $text]);
            finishRegistration($db, $chatId);
            $bot->sendMessage($chatId, 'Регистрация завершена!', null, false, null, mainMenu());
            break;
    }
    exit;
}

if ($text === '/cancel') {
    if ($registration && !$employee) {
        cancelRegistration($db, $chatId);
        $bot->sendMessage($chatId, 'Регистрация отменена.', null, false, null, mainMenu());
    } else {
        $bot->sendMessage($chatId, 'Нечего отменять.', null, false, null, mainMenu());
    }
    exit;
}

switch ($text) {
    case '📅 Начать смену':
    case '/start_work':
        if (!$employee) {
            $bot->sendMessage($chatId, 'Сначала зарегистрируйтесь командой /start');
            break;
        }
        $active = $db->prepare("SELECT id FROM work_sessions WHERE employee_id=? AND status='active'");
        $active->execute([$employee['id']]);
        if ($active->fetch()) {
            $bot->sendMessage($chatId, 'Смена уже запущена');
            break;
        }
        $stmt = $db->prepare('INSERT INTO work_sessions (employee_id,start_time,date) VALUES (?,?,CURDATE())');
        $stmt->execute([$employee['id'], date('Y-m-d H:i:s')]);
        $bot->sendMessage($chatId, 'Смена начата', null, false, null, mainMenu());
        break;

    case '🛑 Закончить смену':
    case '/end_work':
        if (!$employee) {
            $bot->sendMessage($chatId, 'Сначала зарегистрируйтесь командой /start');
            break;
        }
        $stmt = $db->prepare("SELECT id,start_time FROM work_sessions WHERE employee_id=? AND status='active'");
        $stmt->execute([$employee['id']]);
        $session = $stmt->fetch(PDO::FETCH_ASSOC);
        if (!$session) {
            $bot->sendMessage($chatId, 'Активная смена не найдена');
            break;
        }
        $end = date('Y-m-d H:i:s');
        $start = new DateTime($session['start_time']);
        $finish = new DateTime($end);
        $hours = ($finish->getTimestamp() - $start->getTimestamp()) / 3600 - 1; // минус час на обед
        $upd = $db->prepare("UPDATE work_sessions SET end_time=?, total_hours=?, status='completed' WHERE id=?");
        $upd->execute([$end, $hours, $session['id']]);
        $bot->sendMessage($chatId, 'Смена завершена', null, false, null, mainMenu());
        break;

    case '📊 Моя статистика':
    case '/my_stats':
        if (!$employee) {
            $bot->sendMessage($chatId, 'Сначала зарегистрируйтесь командой /start');
            break;
        }
        $stmt = $db->prepare("SELECT SUM(total_hours) FROM work_sessions WHERE employee_id=? AND MONTH(date)=MONTH(CURDATE())");
        $stmt->execute([$employee['id']]);
        $hours = $stmt->fetchColumn() ?: 0;
        $avg = $hours ? round($hours / date('j'), 1) : 0;
        $active = $db->prepare("SELECT COUNT(*) FROM work_sessions WHERE employee_id=? AND status='active'");
        $active->execute([$employee['id']]);
        $open = $active->fetchColumn();
        $msg = "Отработано в этом месяце: {$hours} ч\nСреднее в день: {$avg} ч\nНезавершенные смены: {$open}";
        $bot->sendMessage($chatId, $msg, null, false, null, mainMenu());
        break;

    case '⚙️ Профиль':
        if (!$employee) {
            $bot->sendMessage($chatId, 'Сначала зарегистрируйтесь командой /start');
            break;
        }
        $stmt = $db->prepare('SELECT c.name FROM companies c WHERE c.id=?');
        $stmt->execute([$employee['company_id']]);
        $company = $stmt->fetchColumn();
        $msg = "ФИО: {$employee['full_name']}\nДата рождения: " . date('d.m.Y', strtotime($employee['birth_date'])) . "\nКомпания: {$company}\nГород: {$employee['city']}";
        $bot->sendMessage($chatId, $msg, null, false, null, mainMenu());
        break;

    case '/report week':
        if (!$employee) {
            $bot->sendMessage($chatId, 'Сначала зарегистрируйтесь командой /start');
            break;
        }
        $stmt = $db->prepare("SELECT SUM(total_hours) FROM work_sessions WHERE employee_id = ? AND date >= CURDATE() - INTERVAL 7 DAY");
        $stmt->execute([$employee['id']]);
        $hours = $stmt->fetchColumn() ?: 0;
        $bot->sendMessage($chatId, "Вы отработали за неделю: {$hours} часов", null, false, null, mainMenu());
        break;

    case '/report month':
        if (!$employee) {
            $bot->sendMessage($chatId, 'Сначала зарегистрируйтесь командой /start');
            break;
        }
        $stmt = $db->prepare("SELECT SUM(total_hours) FROM work_sessions WHERE employee_id = ? AND MONTH(date)=MONTH(CURDATE())");
        $stmt->execute([$employee['id']]);
        $hours = $stmt->fetchColumn() ?: 0;
        $bot->sendMessage($chatId, "Отработано за месяц: {$hours} часов", null, false, null, mainMenu());
        break;

    case '/history':
        if (!$employee) {
            $bot->sendMessage($chatId, 'Сначала зарегистрируйтесь командой /start');
            break;
        }
        $stmt = $db->prepare("SELECT start_time,end_time,total_hours FROM work_sessions WHERE employee_id=? ORDER BY id DESC LIMIT 5");
        $stmt->execute([$employee['id']]);
        $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
        if (!$rows) {
            $bot->sendMessage($chatId, 'Нет завершенных смен.', null, false, null, mainMenu());
            break;
        }
        $lines = array_map(function($r) {
            $start = date('d.m H:i', strtotime($r['start_time']));
            $end = $r['end_time'] ? date('d.m H:i', strtotime($r['end_time'])) : '-';
            return "$start - $end ({$r['total_hours']} ч)";
        }, $rows);
        $bot->sendMessage($chatId, implode("\n", $lines), null, false, null, mainMenu());
        break;
    default:
        $bot->sendMessage($chatId, 'Неизвестная команда', null, false, null, mainMenu());
}
