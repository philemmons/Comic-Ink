<?php
session_start();

if (!isset($_SESSION["status"]) || ($_SESSION['status'] != getenv('LOGIN_STATUS'))) {  //Check whether the admin has logged in
    $_SESSION["name"] = "Guest";
}

include_once 'php/sourceFinal.php';

$dbConn = getDBConnection();

if (isset($_POST['logout'])) {
    session_destroy();
    header("Location: /");
    exit;
}

include_once 'header.inc';
?>

<!-- Collect the nav links, forms, and other content for toggling -->
<ul class="navbar-nav me-auto mb-2 mb-lg-0">
    <li class="nav-item">
        <a class="nav-link" href="/">Home</a>
    </li>
    <li class="nav-item">
        <a class="nav-link" href="collection.php">Collection</a>
    </li>
    <li class="nav-item">
        <a class="nav-link" href="graphicNovel.php">Graphic Novels</a>
    </li>
    <li class="nav-item">
        <a class="nav-link active" aria-current="page" href="convention.php">Conventions<span class="visually-hidden">(current)</span></a>
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

<main id="main-content">
    <div class="wrapper form-display">
        <h3 class="h6">
            Welcome <?= $_SESSION['name'] ?>
        </h3>
        <br>
        <form method="POST" name="conForm" aria-label="Convention Search">
            <fieldset class="text-bg-light">
                <legend class="bg-body-tertiary text-white p-1">Optional Search by Name, Date, City, State, or Sort</legend>
                <div class="row gx-4 gy-3 align-items-center">

                    <div class="col-auto">
                        <div class="input-group">
                            <label for="conName" class="input-group-text">Name</label>
                            <input type="text" name="conName" id="conName" placeholder="Enter Convention Name" />
                        </div>
                    </div>

                    <div class="col-auto">
                        <div class="input-group">
                            <label for="conDate" class="input-group-text">Date</label>
                            <input type="date" name="conDate" id="conDate">
                        </div>
                    </div>

                    <div class="col-auto">
                        <div class="input-group">
                            <label for="conCity" class="input-group-text">City</label>
                            <input type="text" name="conCity" id="conCity" placeholder="Enter a City" />
                        </div>
                    </div>

                    <div class="col-auto">
                        <div class="input-group">
                            <label for="state" class="input-group-text">State</label>
                            <select name="state" id="state">
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
                            <label for="sortBy" class="input-group-text">Sort By</label>
                            <select name="sortBy" id="sortBy">
                                <option value="" disabled selected>Select One</option>
                                <option value="conName">Name</option>
                                <option value="city">City</option>
                                <option value="state">State</option>
                                <option value="country">Country</option>
                            </select>
                        </div>
                    </div>
                </div>

                <div class="row py-2">
                    <div class="col-auto py-3">
                        <input type="submit" value="Search" name="filterForm" class="btn" />
                    </div>

                    <div class="col-auto py-3">
                        <input type="submit" value="All Conventions" name="allIn" class="btn" />
                    </div>

                </div>
            </fieldset>
        </form>
    </div>

    <br><br>

    <div class="wrapper form-display mb-5">
        <table class="table table-sm table-striped table-hover display nowrap" id="convDisplay" style="width:100%;" aria-labelledby="comic-conventions">
            <caption class="small bg-body-tertiary text-white p-2 my-2" id="comic-conventions"><strong>Comic Conventions</strong> - The first row consist of eight columns which are Name, Date, Year, Location, City, State, Country, and Official. The first column has the convention name listed in alphabetical order, by default, or by selecting All Conventions. There may be identical conventions listed at different dates, or different Cities, or different States, depending on your search. The convention data was gathered online from various sources on 11.06.2023 Cross reference the Name row with the column for the specific data.</caption>
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
                    $convention = getConData("convention");
                    displayCon($convention);
                }
                ?>
            </tbody>
        </table>
    </div>

    <?php include_once 'footer.inc' ?>

    <script>
        /** https://datatables.net/examples/index **/
        new DataTable('#convDisplay', {
 
           lengthMenu: [16, 8],
            searching: false,
            ordering: false,
            responsive: true,
            pagingType: 'simple',
            language: {
                paginate: {
                    next: 'Next',
                    previous: 'Previous'
                }
            },
            columnDefs: [{
                    responsivePriority: 1,
                    targets: 0
                },
                {
                    responsivePriority: 2,
                    targets: 1
                },
                {
                    responsivePriority: 3,
                    targets: 2
                },
                {
                    responsivePriority: 8,
                    targets: 3
                },
                {
                    responsivePriority: 4,
                    targets: 4
                },
                {
                    responsivePriority: 5,
                    targets: 5
                },
                {
                    responsivePriority: 6,
                    targets: 6
                },
                {
                    responsivePriority: 7,
                    targets: 7
                }
            ] 

        }); 

        /**  https://datatables.net/forums/discussion/71404/accessibility-pagination-using-actual-buttons-instead-of-links */
        const prevNextCollection = document.getElementsByClassName("page-link");
        prevNextCollection[0].setAttribute("role", "button");
        prevNextCollection[1].setAttribute("role", "button");

        /**https://stackoverflow.com/questions/8058109/jquery-datatable-overflow-and-text-wrapping-issues */
    </script>

    </body>

    </html>