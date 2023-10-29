<?php
session_start();

if (!isset($_SESSION["status"])) {  //Check whether the admin has logged in
    $_SESSION["name"] = "Guest";
}

include 'header.html';
include 'php/sourceFinal.php';

$dbConn = getDBConnection();

if (isset($_POST['logout'])) {
    session_destroy();
    header("Location: index.php");
}

function displayCon($convention)
{
    foreach ($convention as $eachCon) {
        echo "<tr>";
        //$str = $eachCon['conName'] . ", " .$eachCon['city'] .", ".$eachCon['state'] .", ".$eachCon['turnOut'] .", ".$eachCon['creator'];
        echo "<td>" . $eachCon['conName'] . "</td><td>" . $eachCon['city'] . "</td><td>" . $eachCon['state'] . "</td><td>" . $eachCon['turnOut'] . "</td><td>" . $eachCon['creator'] . "</td>";
        echo "<td> <a href='" . $eachCon['website'] . "' target='_blank'/>" . $eachCon['website'] . "</a></td>";
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
                <div class="input-group-text">Creator</div>
                <input type="text" name="creator" placeholder="Enter First or Last Name" />
            </div>
        </div>

        <div class="col-auto">
            <div class="input-group">
                <div class="input-group-text">State</div>
                <select name="state">
                    <option value="" disabled selected>Select One</option>
                    <?php
                    $allState = getDropDown('convention', 'state');
                    //print_r($allState);
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
                    <option value="creator">Creator</option>
                    <option value="turnOut ASC">Turn Out: Low to High</option>
                    <option value="turnOut DESC">Turn Out: High to Low</option>
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

<div class="wrapper form-display">
    <table class="table table-sm table-striped table-hover display nowrap" id="convDisplay" style="width:100%">
        <!--https://www.w3schools.com/bootstrap/bootstrap_tables.asp-->
        <thead class='table-dark'>
            <tr>
                <th>Name</th>
                <th>City</th>
                <th>State</th>
                <th>Attendance</th>
                <th>Creator</th>
                <th>Offical</th>
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

<?php include 'footer.inc' ?>

<script>
    //https://datatables.net/reference/option
    new DataTable('#convDisplay', {
        lengthMenu: [8, 16, 24],
        searching: false,
        ordering: false,
        responsive: true
    });
</script>

</body>

</html>