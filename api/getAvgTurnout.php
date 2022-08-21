<?php

    include '../php/dbConnection.php';
    $dbConn = getDBConnection();    
   
    $sql = "select avg(turnOut)
            from convention";
            
    $stmt = $dbConn -> prepare($sql);
    $stmt -> execute();
    $result = $stmt->fetch(PDO::FETCH_ASSOC);
    echo json_encode($result);
