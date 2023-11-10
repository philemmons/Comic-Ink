<?php
    session_start();
    /* Update SQL query with named parameters that prevent SQL injection */
    
    if (!isset($_SESSION["username"])) {  //Check whether the admin has logged in
        header("Location: login.php"); 
    }
    
    include 'php/dbConnection.php';
    
    $dbConn = getDBConnection();

    $nPara[':dConId'] = $_GET['id'];
    $sql = "DELETE FROM convention
            WHERE id = :dConId ";
    //echo $sql;
    $stmt = $dbConn->prepare($sql);
    $stmt->execute($nPara);
    
    header("Location: admin.php");
