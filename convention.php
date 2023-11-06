<?php
session_start();

if (!isset($_SESSION["status"])) {  //Check whether the admin has logged in
    $_SESSION["name"] = "Guest";
}

include_once 'header.html';
include_once 'php/sourceFinal.php';

$dbConn = getDBConnection();

if (isset($_POST['logout'])) {
    session_destroy();
    header("Location: index.php");
}

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
        echo "<td> <a href='https://" . $eachCon['website'] . "' target='_blank'/>" . $eachCon['website'] . "</a></td>";
        echo "</tr>";
    }
}
?>

<!-- Collect the nav links, forms, and other content for toggling -->
<ul class="navbar-nav me-auto mb-2 mb-lg-0">
    <li class="nav-item">
        <a class="nav-link" href="index.php">Home</a>
    </li>
    <li class="nav-item">
        <a class="nav-link" href="collection.php">Collection</a>
    </li>
    <li class="nav-item">
        <a class="nav-link active" aria-current="page" href="convention.php">Convention</a>
    </li>
    <li class="nav-item">
        <a class="nav-link" href="login.php">Admin</a>
    </li>
</ul>

<?php
if (isset($_SESSION["status"])) {
    echo '<form method ="POST" id="one" >';
    echo '<input type="submit" value="Logout" class="btn" name="logout" style="box-shadow: none !important;"/>';
    echo '</form>';
}
?>

</div><!-- /.navbar-collapse -->
</div><!-- /.container-fluid -->
</nav>

<br>
<div class="wrapper form-display">
    <h4>
        Welcome <?= $_SESSION['name'] ?>
    </h4>
    <br>
    <form method="POST" name="conForm" class="row gx-4 gy-3 align-items-center">
        <div class="col-auto">
            <div class="input-group">
                <div class="input-group-text">Name</div>
                <input type="text" name="conName" placeholder="Enter Convention Name" />
            </div>
        </div>

        <div class="col-auto">
            <div class="input-group">
                <div class="input-group-text">Date</div>
                <input type="date" name="conDate" />
            </div>
        </div>

        <div class="col-auto">
            <div class="input-group">
                <div class="input-group-text">City</div>
                <input type="text" name="conCity" placeholder="Enter a City" />
            </div>
        </div>

        <div class="col-auto">
            <div class="input-group">
                <div class="input-group-text">State</div>
                <select name="state">
                    <option value="" disabled selected>Select One</option>
                    <?php
                    $allState = getDropDown('convention', 'state');
                    foreach ($allState as $singleState) {
                        echo "<option>" . $singleState['state'] . " </option>";
                    }
                    ?>
                </select>
            </div>
        </div>

        <div class="col-auto">
            <div class="input-group">
                <div class="input-group-text">Sort By</div>
                <select name="sortBy">
                    <option value="" disabled selected>Select One</option>
                    <option value="conName">Name</option>
                    <option value="city">City</option>
                    <option value="state">State</option>
                    <option value="country">Country</option>
                </select>
            </div>
        </div>

        <div class="col-auto">
            <input type="submit" value="Search" name="filterForm" class="btn" />
        </div>

        <div class="col-auto">
            <input type="submit" value="All Conventions" name="allIn" class="btn" />
        </div>
    </form>
</div>
<br><br>
<div class="wrapper form-display" style="overflow: auto;">
    <table class="table table-sm table-striped table-hover display nowrap" id="convDisplay" style="width:100%;">
        <caption>Comic Book Conventions Updated Last 11.06.23</caption>
        <!--https://www.w3schools.com/bootstrap/bootstrap_tables.asp-->
        <thead class='table-dark'>
            <tr>
                <th>Name</th>
                <th>Date</th>
                <th>Year</th>
                <th>Location</th>
                <th>City</th>
                <th>State</th>
                <th>Country</th>
                <th>Official</th>
            </tr>
        </thead>
        <tbody>
            <?php
            if (isset($_POST['filterForm'])) {
                $filterCon = goSQLcon("convention");
                displayCon($filterCon);
            } else { // Display inventory initially.
                $convention = getInfo("convention");
                displayCon($convention);
            }
            ?>
        </tbody>
    </table>
</div>
<br><br>
<?php include_once 'footer.inc' ?>

<script>
    //https://datatables.net/reference/option
    new DataTable('#convDisplay', {
        lengthMenu: [8, 16],
        searching: false,
        ordering: false,
        responsive: true,
        pagingType: 'simple'
    });
</script>

</body>

</html>
