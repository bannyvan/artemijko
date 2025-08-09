<?php
function getDb(array $config): PDO
{
    return new PDO(
        "mysql:host={$config['db']['host']};dbname={$config['db']['database']};charset={$config['db']['charset']}",
        $config['db']['user'],
        $config['db']['password']
    );
}

function getEmployee(PDO $db, int $tgId)
{
    $stmt = $db->prepare('SELECT * FROM employees WHERE telegram_id = ?');
    $stmt->execute([$tgId]);
    return $stmt->fetch(PDO::FETCH_ASSOC);
}

function getRegistration(PDO $db, int $tgId)
{
    $stmt = $db->prepare('SELECT * FROM registrations WHERE telegram_id = ?');
    $stmt->execute([$tgId]);
    return $stmt->fetch(PDO::FETCH_ASSOC);
}

function startRegistration(PDO $db, int $tgId)
{
    $stmt = $db->prepare('INSERT INTO registrations (telegram_id) VALUES (?) ON DUPLICATE KEY UPDATE step=step');
    $stmt->execute([$tgId]);
}

function updateRegistration(PDO $db, int $tgId, array $data)
{
    $fields = [];
    $params = [];
    foreach ($data as $k => $v) {
        $fields[] = "$k=?";
        $params[] = $v;
    }
    $params[] = $tgId;
    $stmt = $db->prepare('UPDATE registrations SET ' . implode(',', $fields) . ' WHERE telegram_id = ?');
    $stmt->execute($params);
}

function finishRegistration(PDO $db, int $tgId)
{
    $reg = getRegistration($db, $tgId);
    if (!$reg) {
        return false;
    }
    $stmt = $db->prepare('INSERT INTO employees (telegram_id, full_name, birth_date, company_id, city) VALUES (?,?,?,?,?)');
    $stmt->execute([
        $tgId,
        $reg['full_name'],
        $reg['birth_date'],
        $reg['company_id'],
        $reg['city']
    ]);
    $db->prepare('DELETE FROM registrations WHERE telegram_id = ?')->execute([$tgId]);
    return true;
}

function cancelRegistration(PDO $db, int $tgId)
{
    $db->prepare('DELETE FROM registrations WHERE telegram_id = ?')->execute([$tgId]);
}

function getVacationRequest(PDO $db, int $tgId)
{
    $stmt = $db->prepare('SELECT * FROM vacation_requests_tmp WHERE telegram_id = ?');
    $stmt->execute([$tgId]);
    return $stmt->fetch(PDO::FETCH_ASSOC);
}

function startVacationRequest(PDO $db, int $tgId)
{
    $stmt = $db->prepare('INSERT INTO vacation_requests_tmp (telegram_id) VALUES (?) ON DUPLICATE KEY UPDATE step=step');
    $stmt->execute([$tgId]);
}

function updateVacationRequest(PDO $db, int $tgId, array $data)
{
    $fields = [];
    $params = [];
    foreach ($data as $k => $v) {
        $fields[] = "$k=?";
        $params[] = $v;
    }
    $params[] = $tgId;
    $stmt = $db->prepare('UPDATE vacation_requests_tmp SET ' . implode(',', $fields) . ' WHERE telegram_id = ?');
    $stmt->execute($params);
}

function finishVacationRequest(PDO $db, int $tgId, int $employeeId)
{
    $req = getVacationRequest($db, $tgId);
    if (!$req) {
        return false;
    }
    $stmt = $db->prepare('INSERT INTO vacation_requests (employee_id,start_date,end_date,type,comment) VALUES (?,?,?,?,?)');
    $stmt->execute([
        $employeeId,
        $req['start_date'],
        $req['end_date'],
        $req['type'],
        $req['comment']
    ]);
    $db->prepare('DELETE FROM vacation_requests_tmp WHERE telegram_id=?')->execute([$tgId]);
    return true;
}

function cancelVacationRequest(PDO $db, int $tgId)
{
    $db->prepare('DELETE FROM vacation_requests_tmp WHERE telegram_id=?')->execute([$tgId]);
}
