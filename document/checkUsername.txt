<?php
header('Access-Control-Allow-Origin: *');
include '../../inc/dbConnection.php';
$dbConn = getDBConnection("techCheck");

    $sql = "SELECT username 
            FROM user
            WHERE username = :username";

    $statement = $dbConn->prepare($sql);
    $np = array();
    $np[":username"] = $_GET['username'];
    $statement->execute( $np );
    $record = $statement->fetch(PDO::FETCH_ASSOC);
    
    //print_r($record);
    echo json_encode($record); //jsonp -> "json format with padding"
?>