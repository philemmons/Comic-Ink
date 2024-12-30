<?php

function getDBConnection()
{
    /*******  UPdated 10.20.23
    // https://devcenter.heroku.com/articles/jawsdb#using-jawsdb-with-php
    $url = getenv('JAWSDB_URL');
    $dbparts = parse_url($url);
    $host = $dbparts['host'];
    $username = $dbparts['user'];
    $password = $dbparts['pass'];
    $dbname= ltrim($dbparts['path'],'/');
     *******/
    $dbHost = getenv('DB_HOST');
    $dbUser = getenv('DB_USER');
    $dbPW = getenv('DB_PW');
    $dbName = getenv('DB_NAME');

    try {
        // Creating database connection
        $dbConn = new PDO("mysql:host=$dbHost;dbname=$dbName", $dbUser, $dbPW);
        // Setting Error handling to Exception
        $dbConn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        //echo "Connected successfully";
    } catch (PDOException $e) {
        echo "There was some problem connecting to the database! Error: $e";
        exit();
    }
    return $dbConn;
}
