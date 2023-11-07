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

?>
<script>
    function atCon(titleId, yearId, issueId) {
        $("#modalInfo").html("");
        $("#modalTitle").html("");
        $.ajax({
            type: "get", // HTTP method to use for the request
            url: "api/getComicInfo.php", // URL to which the request is sent.
            dataType: "json", // type of data expected back from the server
            data: {
                "tID": titleId, // map that is sent to the server with the request.
                "yID": yearId,
                "iID": issueId
            },
            success: function(data, status) { //callback function that is executed if the request succeeds.
                alert(data[0].creator); //ALSO THE BRACKETS in the preview indicate an object!
                //to be sure something is being sent back from the api 
                // *****  inspect element when working with js -->network: remote server --> response  --> console to examine data
                //test the api in the browser to be certain it works
                if (jQuery.isEmptyObject(data[0])) {
                    $("#modalTitle").append("<h3>Sorry!</h3>")
                    $("#modalInfo").append("At this time the creator is not scheduled at any conventions.");
                } else {
                    $("#modalTitle").append("Creator: " + data[0].creator);
                    $("#modalInfo").append("Convention: " + data[0].conName + "<br>");
                    $("#modalInfo").append("City: " + data[0].city + "<br>");
                    $("#modalInfo").append("State: " + data[0].state + "<br>");
                    $("#modalInfo").append("Attendance: " + data[0].turnOut + "<br>");
                    $("#modalInfo").append("<a href = '" + data[0].website + "\'>" + data[0].website + "</a>");
                }
            },
            complete: function(data, status) { //callback function that executes whenever the request finishes.
                alert(status);
            }
        }); //AJAX 1

    }
</script>

<?php
function dataDisplay($comic)
{
    foreach ($comic as $page) {
        echo "<tr>";
        echo "<td>" . $page['title'] . "</td><td>" . $page['creator'] . "</td><td>" . $page['issue'] . "</td><td>" . $page['publisher'] . "</td><td>" . $page['year'] . "</td>";
        echo "<td> <a data-toggle='modal' href='#myModal' onclick = 'atCon(\"" . $page['title'] . "\",\"" . $page['year'] . "\",\"" . $page['issue'] . "\")'>more</a></td>";
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
        <a class="nav-link" href="convention.php">Convention</a>
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
            <input type="submit" value="Search" name="filterForm" class="btn" />
        </div>

        <div class="col-auto">
            <input type="submit" value="All Comics" name="allIn" class="btn" /></span>
        </div>

        <div class="col-auto">
            <div class="input-group">
                <div class="input-group-text">Title</div>
                <input type="text" name="title" placeholder="Enter comic title Here" />
            </div>
        </div>

        <div class="col-auto">
            <div class="input-group">
                <div class="input-group-text">Creator</div>
                <input type="text" name="creator" placeholder="First or Last Name" />
            </div>
        </div>

        <div class="col-auto">
            <div class="input-group">
                <div class="input-group-text">Publisher</div>
                <select name="publisher">
                    <option value="" disabled selected>Select One</option>
                    <?php
                    $allPub = getDropDown('comicBook', 'publisher');
                    print_r($allPub);
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
                    <option value="title">Title</option>
                    <option value="creator">Creator</option>
                    <option value="year ASC">Year: Low to High</option>
                    <option value="year DESC">Year: High to Low</option>
                    <option value="issue ASC">Issue: Low to High</option>
                    <option value="issue DESC">Issue: High to Low</option>
                </select>
            </div>
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
                <th>Creator</th>
                <th>Issue</th>
                <th>Publisher</th>
                <th>Year</th>
                <th>Autograph</th>
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

<!-- Modal -->
<div id="myModal" class="modal fade" role="dialog">
    <div class="modal-dialog modal-sm">

        <!-- Modal content-->
        <div class="modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal">&times;</button>
                <h4 class="modal-title" id="modalTitle"></h4>
            </div>
            <div class="modal-body">
                <div id="modalInfo"></div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn" data-dismiss="modal">Close</button>
            </div>
        </div>

    </div>
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
