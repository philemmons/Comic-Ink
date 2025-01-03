<?php
session_start();
/* Update SQL query with named parameters that prevent SQL injection */

if (!isset($_SESSION["status"]) || ($_SESSION['status'] != getenv('LOGIN_STATUS'))) {  //Check whether the admin has logged in
    header("Location: login.php");
    exit;
}

include_once 'php/dbConnection.php';

$dbConn = getDBConnection();

$nPara[':dConId'] = $_GET['id'];
$sql = "DELETE FROM convention
            WHERE id = :dConId ";
//echo $sql;
$stmt = $dbConn->prepare($sql);
$stmt->execute($nPara);

header("Location: admin.php");
exit;
