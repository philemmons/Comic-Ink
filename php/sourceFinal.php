<?php
include 'dbConnection.php';

$dbConn = getDBConnection();

/*********
 * 10-24-23
 * Updated functions with prepared statements to prevent SQL injection
 * 
 **********/

/*
*Form vars - All input converted to lower case.
*/
if (isset($_POST['title']))
    $title = strtolower($_POST['title']); // User input deviceName

if (isset($_POST['creator']))
    $creator = strtolower($_POST['creator']); // User input deviceName

if (isset($_POST['']))
    $pub = strtolower($_POST['publisher']); // User selected deviceType

if (isset($_POST['year']))
    $year = $_POST['year']; // Selection display type

if (isset($_POST['issue']))
    $issue = $_POST['issue']; //User input item statusable selection

if (isset($_POST['sortBy']))
    $sortBy = $_POST['sortBy'];

//$creator, $sortBy - from above
if (isset($_POST['city']))
    $city = strtolower($_POST['city']);

if (isset($_POST['conName']))
    $conName = strtolower($_POST['conName']);

if (isset($_POST['state']))
    $state = strtoupper($_POST['state']);

if (isset($_POST['turnOut']))
    $turnOut =  $_POST['turnOut'];

if (isset($_POST['website']))
    $website = $_POST['website'];


/*
*@input: sql string to be processed
*@output: table from the sql query
*/
function preExeFet($sql)
{
    global $dbConn, $nPara;

    //print_r($dbConn);
    //echo '<br>';
    //print_r($nPara);

    $stmt = $dbConn->prepare($sql);
    $stmt->execute($nPara);
    $records = $stmt->fetchAll(PDO::FETCH_ASSOC);
    return $records;
}
function preExeFetNOPARA($sql)
{
    global $dbConn;

    $stmt = $dbConn->prepare($sql);
    $stmt->execute();
    $records = $stmt->fetchAll(PDO::FETCH_ASSOC);
    return $records;
}

/*
*@input: 
*@output: all contents of device table for the user in alphebetical order
*/
function getInfo($table)
{
    global $nPara;
    $nPara[':dTable'] = $table;
    $sql = "SELECT * FROM :dTable";
    return preExeFet($sql);
}

/*
*@input: form input by user: partial device name, dropdown device type, order by price or name and statusablity
*@output: returns a table based on the query including a device count. a-e letters allow for different output order.
*/
function goSQLcomic($table)
{
    global $title, $creator, $pub, $year, $issue, $sortBy, $nPara;
    $needle = "WHERE"; //If the 'where' keyword is used  then 'and 'is added to the string in place of.

    $nPara[':dTable'] = $table;
    $sql = "SELECT title, creator, publisher, year, issue FROM :dTable";

    if ($title) {
        //Prevents SQL injection by using a named parameter.
        $nPara[':dTitle'] = '%' . $title . '%';
        $sql .= " WHERE title LIKE :dTitle ";
    }
    if ($creator) {
        if (strlen(stristr($sql, $needle)) > 0) { //String search for 'where': stristr returns the partial string up to 'where'.
            // Needle Found - compare lenth>0 means the keyword was found.  http://www.maxi-pedia.com/string+contains+substring+php
            $sql .= " AND ";
        } else {
            $sql .= " WHERE ";
        }
        //Prevents SQL injection by using a named parameter.
        $nPara[':dCreator'] = '%' . $creator . '%';
        $sql .= " creator LIKE :dCreator ";
    }
    if ($pub) {
        //String search for 'where': stristr returns the partial string up to 'where'.
        // compare lenth>0 means the keyword was found.  http://www.maxi-pedia.com/string+contains+substring+php
        if (strlen(stristr($sql, $needle)) > 0) {
            // Needle Found
            $sql .= " AND ";
        } else {
            $sql .= " WHERE ";
        }
        //Prevents SQL injection by using a named parameter.
        $nPara[':dPub'] = '%' . $pub . '%';
        $sql .= " publisher LIKE :dPub ";
    }

    if (isset($_POST['allIn'])) { // Added due to user submitting a blank form.
        $sql .= " ";
    }

    if ($sortBy) { // Name or price
        $nPara[':dSortBy'] = $sortBy;
        $sql .= " ORDER BY :dSortBy ";
    }
    //echo $sql;
    return preExeFet($sql);
}

function get($table, $column)
{
    global $nPara;

    $nPara[':dColumn'] = $column;
    $nPara[':dTable'] = $table;
    //$sql = "SELECT DISTINCT :dColumn FROM :dTable";
    $sql = 'select distinct ' . $column . ' from ' * $table;
    //echo $sql;
    //die();
    return preExeFetNOPARA($sql);
}

function goSQLcon($table)
{
    global $city, $creator, $conName, $state, $turnOut, $website, $sortBy, $nPara;
    $needle = "WHERE"; //If the 'where' keyword is used  then 'and 'is added to the string in place of.

    $nPara[':dTable'] = $table;
    $sql = "SELECT conName, city, state, turnOut, creator, website FROM :dTable";

    if ($conName) {
        //Prevents SQL injection by using a named parameter.
        $nPara[':dConName'] = '%' . $conName . '%';
        $sql .= " WHERE conName LIKE :dConName ";
    }
    if ($creator) {
        if (strlen(stristr($sql, $needle)) > 0) { //String search for 'where': stristr returns the partial string up to 'where'.
            // Needle Found - compare lenth>0 means the keyword was found.  http://www.maxi-pedia.com/string+contains+substring+php
            $sql .= " AND ";
        } else {
            $sql .= " WHERE ";
        }
        //Prevents SQL injection by using a named parameter.
        $nPara[':dCreator'] = '%' . $creator . '%';
        $sql .= " creator LIKE :dCreator ";
    }
    if ($state) {
        if (strlen(stristr($sql, $needle)) > 0) { //String search for 'where': stristr returns the partial string up to 'where'.
            // Needle Found - compare lenth>0 means the keyword was found.  http://www.maxi-pedia.com/string+contains+substring+php
            $sql .= " AND ";
        } else {
            $sql .= " WHERE ";
        }
        //Prevents SQL injection by using a named parameter.
        $nPara[':dState'] = '%' . $state . '%';
        $sql .= " state LIKE :dState ";
    }

    if (isset($_POST['allIn'])) { // Added due to user submitting a blank form.
        $sql .= " ";
    }

    if ($sortBy) { // Name or price
        $nPara[':dSortBy'] = $sortBy;
        $sql .= " ORDER BY :dSortBy ";
    }
    //echo $sql;
    return preExeFet($sql);
}

//login.php
/*
*@input: login process accesssed by login.php with user input
*@output: successful login  directs user to index.php
*Future work - https://stackoverflow.com/questions/20764031/php-salt-and-hash-sha256-for-login-password
*/
function goMain()
{
    global $dbConn, $nPara;

    $userForm = $_POST['formUN'];
    $pwForm = hash('sha256', $_POST['formPW']);
    //echo $pwForm;
    //die();
    //USE NAMEDPARAMETERS TO PREVENT SQL INJECTION
    $nPara[':username'] = $userForm;
    $nPara[':password'] = $pwForm;

    $sql = "SELECT * FROM admin WHERE userName = :username AND password = :password";

    $statement = $dbConn->prepare($sql);
    $statement->execute($nPara);
    $record = $statement->fetch(PDO::FETCH_ASSOC);

    if (empty($record)) { //wrong credentials
        echo "<form method='POST' action='login.php'>";
        echo "<br><span style='color:red'><h4>Wrong username or password.</h4></span>";
        echo "</form>";
    } else {
        $_SESSION["name"] = $record['firstName'] . " " . $record['lastName'];
        $_SESSION["username"]  = $record['userName'];
        $_SESSION["status"] = "Admin";
        //echo $_SESSION["status"];
        header("Location: admin.php"); //redirect to home page
    }
}

//admin.php - display admin info
/*
function info(){
    //global $userData;
    //http://php.net/manual/en/function.explode.php
    //$data = $_GET['$userData'];
    $pie = explode(",", $_GET['con_Id']);
    foreach($pie as $slice){
        echo"<br>".$slice;
    }
}

<div id="iframecss">
            <iframe src="" width="300" height="300" name="userInfoFrame"></iframe>
        </div>        
*/


//conInsert.php and conUpdate.php
function getConInfo($con_id)
{
    global $dbConn, $nPara;

    $nPara[':dConId'] = $con_id;
    $sql = "SELECT * FROM convention WHERE con_id = :dConId ";
    $stmt = $dbConn->prepare($sql);
    $stmt->execute();
    $record = $stmt->fetch(PDO::FETCH_ASSOC);
    return $record;
}
//conInsert.php
function addCon()
{
    global $dbConn;

    if (isset($_GET['submit'])) {  //admin has submitted the "update user" form
        $sql = "INSERT INTO convention (
                    con_id,  
                    conName,   
                    city,   
                    state,  
                    creator,  
                    website,  
                    turnOut   
                )
                VALUES (
                :con_id,:conName,:city, :state, :creator, :website,:turnOut
                )";

        $nPara = array();
        $nPara[':con_id'] = $_GET['con_id'];
        $nPara[':conName']  = $_GET['conName'];
        $nPara[':city'] = $_GET['city'];
        $nPara[':state'] = $_GET['state'];
        $nPara[':creator'] = $_GET['creator'];
        $nPara[':website'] = $_GET['website'];
        $nPara[':turnOut'] = $_GET['turnOut'];

        $stmt = $dbConn->prepare($sql);
        $stmt->execute($nPara);
        //clear the value - prevent multiple insertions
        $nPara = array();
    } //eof if
}
