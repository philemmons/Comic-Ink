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

function dataDisplay($comic)
{
    foreach ($comic as $page) {
        echo "<tr>";
        echo "<td>" . $page['title'] . "</td>";
        echo "<td>" . $page['issue'] . "</td>";
        echo "<td>" . $page['year'] . "</td>";
        echo "<td>" . $page['volume'] . "</td>";
        echo "<td>" . $page['total_issues'] . "</td>";
        echo "<td>" . $page['publisher'] . "</td>";
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
        <a class="nav-link active" aria-current="page" href="collection.php">Collection</a>
    </li>
    <li class="nav-item">
        <a class="nav-link" href="graphicNovel.php">Graphic Novels</a>
    </li>
    <li class="nav-item">
        <a class="nav-link" href="convention.php">Conventions</a>
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
    <h6>
        Welcome <?= $_SESSION['name'] ?>
    </h6>
    <br>
    <form method="POST" name="comicForm" class="row gx-4 gy-3 align-items-center">
        <div class="col-auto">
            <div class="input-group">
                <div class="input-group-text">Title</div>
                <input type="text" name="title" placeholder="Enter comic title Here" />
            </div>
        </div>

        <div class="col-auto">
            <div class="input-group">
                <div class="input-group-text">Publisher</div>
                <select name="publisher">
                    <option value="" disabled selected>Select One</option>
                    <?php
                    $allPub = getDropDown('comicBook', 'publisher');
                    //print_r($allPub);
                    foreach ($allPub as $singlePub) {
                        echo "<option>" . $singlePub['publisher'] . " </option>";
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
                    <option value="title ASC">Title</option>
                    <option value="publisher ASC">Publisher</option>
                    <option value="year ASC">Year: Low to High</option>
                    <option value="year DESC">Year: High to Low</option>
                </select>
            </div>
        </div>

        <div class="col-auto">
            <input type="submit" value="Search" name="filterForm" class="btn" />
        </div>

        <div class="col-auto">
            <input type="submit" value="All Comics" name="allIn" class="btn" /></span>
        </div>

    </form>
</div>
<br><br>
<div class="wrapper form-display" style="overflow: auto;">
    <table class="table table-sm table-striped table-hover display nowrap" id="comDisplay" style="width:100%;">
        <!--https://www.w3schools.com/bootstrap/bootstrap_tables.asp-->
        <thead class='table-dark'>
            <tr>
                <th>Title</th>
                <th>Issue</th>
                <th>Year</th>
                <th>Volume</th>
                <th>Total Issues</th>
                <th>Publisher</th>
            </tr>
        </thead>
        <tbody>
            <?php
            if (isset($_POST['filterForm'])) {
                $filterList = goSQLcomic("comicBook");
                dataDisplay($filterList);
            } else { // Display inventory initially.
                $comic = getInfo("comicBook");
                dataDisplay($comic);
            }
            ?>
        </tbody>
    </table>
</div>

<br><br>
<?php include_once 'footer.inc' ?>

<script>
    //https://datatables.net/reference/option
    new DataTable('#comDisplay', {
        lengthMenu: [8, 16],
        searching: false,
        ordering: false,
        responsive: true,
        pagingType: 'simple'
    });
</script>

</body>

</html>