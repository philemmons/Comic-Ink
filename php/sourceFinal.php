<?php

include_once 'dbConnection.php';

$dbConn = getDBConnection();

/*********
 * 10-24-23
 * Updated functions with prepared statements to prevent SQL injection
 * NOTE: https://dev.mysql.com/doc/refman/8.0/en/prepare.html
 *    **************  Parameter markers can be used only where data values should appear, NOT for SQL keywords, identifiers, and so forth.  ************
 **********/

/*
*Form vars - All input converted to lower case unless numerical
*/

/* comic book table */
if (isset($_POST['title']))
    $title = strtolower($_POST['title']); // User input deviceName

if (isset($_POST['issue']))
    $issue = strtolower($_POST['issue']);

if (isset($_POST['year']))
    $year = $_POST['year'];

if (isset($_POST['volume']))
    $volume = $_POST['volume'];

if (isset($_POST['total_issues']))
    $tot_issues = strtolower($_POST['total_issues']);

if (isset($_POST['publisher']))
    $pub = strtolower($_POST['publisher']);

if (isset($_POST['sortBy']))
    $sortBy = $_POST['sortBy'];

/* convention table below, except for sortBy*/

if (isset($_POST['conName']))
    $conName = strtolower($_POST['conName']);

if (isset($_POST['conDate']))
    $conDate = strtolower($_POST['conDate']);

if (isset($_POST['conCity']))
    $conCity =  strtolower($_POST['conCity']);

if (isset($_POST['state']))
    $state = strtolower($_POST['state']);

/*
*@input: PDO sql string to be processed with or without parameterized variable(s)
*@output: table from the sql query
*/
function preExeFet($sql)
{
    global $dbConn, $nPara;

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
*@input: Name of the database table 
*@output: all contents of device table for the user in alphabetical order BY title
*/
function getInfo($table)
{
    $sql = "SELECT * FROM " . $table . " ORDER BY title ASC";
    return preExeFetNOPARA($sql);
}

/*
*@input: Name of the convention table
*@output: all contents of CONVENTION table for the user by ascending date with TBA values last
*/
function getConData($table)
{
    $sql = "SELECT *, STR_TO_DATE(CONCAT(start_date, ' ', year),
    '%M %d %Y') AS result FROM " . $table . " ORDER BY conName ASC";
    return preExeFetNOPARA($sql);

    /** ORIGINAL 
    $sql = "SELECT *, STR_TO_DATE(CONCAT(start_date, ' ', year),
    '%M %d %Y') AS result FROM " . $table . " ORDER BY result IS NULL , result ASC";
    return preExeFetNOPARA($sql);
     **/
}

/*
*@input: form input by user: title, publisher dropdown option from DB, and sort function
*@output: returns a table based on the query including titles, publishers, and sort by title, publisher, and year.
*/
function goSQLcomic($table)
{
    global $title, $year, $pub, $sortBy, $nPara;
    $needle = "WHERE"; //If the 'where' keyword is used  then 'and 'is added to the string in place of.

    $sql = "SELECT * FROM " . $table;

    if ($title) {
        //Prevents SQL injection by using a named parameter.
        $nPara[':dTitle'] = '%' .  htmlspecialchars($title, ENT_QUOTES) . '%';
        $sql .= " WHERE title LIKE :dTitle ";
    }
    if ($pub) {
        if (strlen(stristr($sql, $needle)) > 0) {
            $sql .= " AND ";
        } else {
            $sql .= " WHERE ";
        }
        //Prevents SQL injection by using a named parameter.
        $nPara[':dPub'] = '%' . $pub . '%';
        $sql .= " publisher LIKE :dPub ";
    }
    /*Sort by title, year, or publisher*/
    if ($sortBy) {
        $sql .= " ORDER BY " . $sortBy;
    }
    /* no parameters included */
    if (strlen(stristr($sql, $needle)) < 0) {
        return preExeFetNOPARA($sql);
    }
    //echo $sql;
    return preExeFet($sql);
}

function getDropDown($table, $column)
{
    $sql = 'SELECT DISTINCT ' . $column . ' FROM ' . $table . ' ORDER BY ' . $column . ' ASC';
    //echo $sql;
    return preExeFetNOPARA($sql);
}
/* convention.php */
function goSQLcon($table)
{
    global $conName, $conDate, $conCity, $state, $sortBy, $nPara;
    $needle = "WHERE"; //If the 'where' keyword is used  then 'and 'is added to the string in place of.

    $sql = "SELECT *  FROM " . $table;

    if ($conName) {
        //Prevents SQL injection by using a named parameter.
        $nPara[':dConName'] = '%' . htmlspecialchars($conName, ENT_QUOTES) . '%';
        $sql .= " WHERE conName LIKE :dConName ";
    }

    if ($conDate) {
        if (strlen(stristr($sql, $needle)) > 0) { //String search for 'where': stristr returns the partial string up to 'where'.
            // Needle Found - compare lenth>0 means the keyword was found.  http://www.maxi-pedia.com/string+contains+substring+php
            $sql .= " AND ";
        } else {
            $sql .= " WHERE ";
        }
        //Convert date to text
        //Prevents SQL injection by using a named parameter.
        $nPara[':dConDate'] = date("F j", strtotime($conDate));
        $sql .= " start_date LIKE :dConDate ";
    }

    if ($conCity) {
        if (strlen(stristr($sql, $needle)) > 0) {
        } else {
            $sql .= " WHERE ";
        }
        //Prevents SQL injection by using a named parameter.
        $nPara[':dCity'] = '%' . htmlspecialchars($conCity, ENT_QUOTES) . '%';
        $sql .= " city LIKE :dCity ";
    }

    if ($state) {
        if (strlen(stristr($sql, $needle)) > 0) {
            $sql .= " AND ";
        } else {
            $sql .= " WHERE ";
        }
        //Prevents SQL injection by using a named parameter.
        $nPara[':dState'] = '%' . $state . '%';
        $sql .= " state LIKE :dState ";
    }

    if ($sortBy) {
        $sql .= " ORDER BY " . $sortBy . " ASC";
    }
    //echo $sql;
    if (strlen(stristr($sql, $needle)) < 0) {
        return preExeFetNOPARA($sql);
    }

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

    $userForm = htmlspecialchars($_POST['formUN'], ENT_QUOTES);
    $pwForm = hash('sha256', $_POST['formPW']);

    //Prevents SQL injection by using a named parameter.
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
        $_SESSION["status"] = getenv('LOGIN_STATUS');
        header("Location: admin.php");
        exit; //redirect to admin page
    }
}

//conInsert.php and conUpdate.php
function getConInfo($conID)
{
    global $dbConn, $nPara;

    $nPara[':dConId'] = $conID;
    $sql = "SELECT * FROM convention WHERE id = :dConId ";
    $stmt = $dbConn->prepare($sql);
    $stmt->execute($nPara);
    $record = $stmt->fetch(PDO::FETCH_ASSOC);
    return $record;
}

/*conInsert.php*/
function addCon()
{
    global $dbConn;

    if (isset($_POST['submitInsert'])) {
        $sql = "INSERT INTO convention (
                    conName,
                    start_date,
                    end_date,
                    year,
                    event_location,
                    city,
                    state,
                    country,
                    website
                ) VALUES (
                :conName, :start_date, :end_date, :year, :event_location, :city, :state, :country, :website
                )";

        $nPara[':conName']  = htmlspecialchars($_POST['conName'], ENT_QUOTES);
        $nPara[':start_date'] = htmlspecialchars($_POST['start_date'], ENT_QUOTES);
        $nPara[':end_date'] = htmlspecialchars($_POST['end_date'], ENT_QUOTES);
        $nPara[':year'] = htmlspecialchars($_POST['year'], ENT_QUOTES);
        $nPara[':event_location'] = htmlspecialchars($_POST['event_location'], ENT_QUOTES);
        $nPara[':city'] = htmlspecialchars($_POST['city'], ENT_QUOTES);
        $nPara[':state'] = htmlspecialchars($_POST['state'], ENT_QUOTES);
        $nPara[':country'] = htmlspecialchars($_POST['country'], ENT_QUOTES);
        $nPara[':website'] = htmlspecialchars(preg_replace("(^https?://)", "", $_POST['website']), ENT_QUOTES);

        $stmt = $dbConn->prepare($sql);
        $stmt->execute($nPara);
        //clear the value - prevent multiple insertions
        $nPara = array();

        sleep(5);
    } //eof if
}


/* convention.php and admin.php */
function dateDisplay($startDate, $endDate)
{
    $result = strcasecmp($startDate, $endDate);
    if ($result == 0) {
        return $startDate;
    }
    return $startDate . "-" . substr($endDate, strrpos($endDate, ' ') + 1);
}

function displayCon($convention)
{
    foreach ($convention as $eachCon) {
        $newDate = dateDisplay($eachCon['start_date'], $eachCon['end_date']);

        echo "<tr>";
        echo "<td>" . $eachCon['conName'] . "</td>";
        echo "<td>" . $newDate . "</td>";
        echo "<td>" . $eachCon['year'] . "</td>";
        echo "<td>" . $eachCon['event_location'] . "</td>";
        echo "<td>" . $eachCon['city'] . "</td>";
        echo "<td>" . $eachCon['state'] . "</td>";
        echo "<td>" . $eachCon['country'] . "</td>";
        echo "<td>
                <a href='https://" . $eachCon['website'] . "' target='_blank' rel='noopener noreferrer'>" . $eachCon['website'] . "</a>
              </td>";
        echo "</tr>";
    }
}
