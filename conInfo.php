<?php
session_start();

if (!isset($_SESSION["username"])) {  //Check whether the admin has logged in
    header("Location: login.php");
}

include 'php/sourceFinal.php';
?>

<!DOCTYPE html>
<html>

<head>
    <title> Con Info </title>
    <style>
        body {
            color: white;
            font-family: cursive;
        }
    </style>
</head>

<body>
    <h2>Specific Data <?php //echo info() 
                        ?></h2> <!-- https://stackoverflow.com/questions/2020445/what-does-mean-in-php -->
</body>

</html>