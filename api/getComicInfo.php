<?php

    include_once '../php/dbConnection.php';
    $dbConn = getDBConnection();    
    $sql = "create view matchCreator as 
            SELECT *
            FROM convention natural join comicBook";
          
    $stmt = $dbConn -> prepare($sql);
    $stmt -> execute();
    
    $sql = "select creator, conName, city, state, turnOut, website 
            from matchCreator 
            where title = :tID
            and year= :yID
            and issue = :iID";
            
    $stmt = $dbConn -> prepare($sql);
    $nPara[':tID'] = $_GET['tID'];
    $nPara[':yID'] = $_GET['yID'];
    $nPara[':iID'] = $_GET['iID'];
    $stmt -> execute($nPara);
    $result = $stmt->fetchAll(PDO::FETCH_ASSOC);
    echo json_encode($result);
    
    $sql = "drop view matchCreator";
    $stmt = $dbConn -> prepare($sql);
    $stmt -> execute();
