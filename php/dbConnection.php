<?php


function getDBConnection() {
    
    // https://devcenter.heroku.com/articles/jawsdb#using-jawsdb-with-php
    $url = getenv('JAWSDB_URL');
    $dbparts = parse_url($url);
    $host = $dbparts['host'];
    $username = $dbparts['user'];
    $password = $dbparts['pass'];
    $dbname= ltrim($dbparts['path'],'/');
    
    //old
    //$host = "localhost";
    //$username = "philemmons";//authorized user to have access to create and drop views
    //$password = "s3cr3t";
    
    try {
        //Creating database connection
        $dbConn = new PDO("mysql:host=$host;dbname=$dbname", $username, $password);
        // Setting Errorhandling to Exception
        $dbConn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION); 
        //echo "Connected successfully";
    }
    catch (PDOException $e) {
        echo "There was some problem connecting to the database! Error: $e";
        exit();
    }
    return $dbConn;
}
?>
