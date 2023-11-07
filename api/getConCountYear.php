<?php

    include_once '../php/dbConnection.php';
    $dbConn = getDBConnection();    
   
    $sql = "SELECT year, COUNT(*) AS c FROM convention GROUP BY year ORDER BY c ASC";
            
    $stmt = $dbConn -> prepare($sql);
    $stmt -> execute();
    $result = $stmt->fetch(PDO::FETCH_ASSOC);
    echo json_encode($result);
