<?php
    session_start();
    
    if (!isset($_SESSION["username"])) {  //Check whether the admin has logged in
        header("Location: login.php"); 
    }
    
    include 'php/dbConnection.php';
    
    $dbConn = getDBConnection();
    $sql = "DELETE FROM convention
            WHERE con_id = " . $_GET['con_id'];
    //echo $sql;
    $stmt = $dbConn->prepare($sql);
    $stmt->execute();
    
    header("Location: admin.php");
?>