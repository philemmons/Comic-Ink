<?php
session_start();

if (!isset($_SESSION["status"])) {  //Check whether the admin has logged in
  header("Location: login.php");
}

include_once 'header.html';
include_once 'php/sourceFinal.php';

$dbConn = getDBConnection();

if (isset($_POST['logout'])) {
  session_destroy();
  header("Location: index.php");
}

/*admin report*/
/* average number of conventions per state */
function getConAvg()
{
  global $dbConn;
  $sql = "SELECT ROUND(COUNT(*) / COUNT(DISTINCT (state))) as result 
          FROM convention";
  $ans =  preExeFetNOPARA($sql);
  //print_r($ans);
  return $ans;
}
function displayConAvg($num)
{
  foreach ($num as $digit) {
    echo $digit['result'] . " ";
  }
}
/* number of conventions per state greater than four*/
function getConByState()
{
  global $dbConn;
  $sql = "SELECT state, c
          FROM
            (SELECT state, COUNT(*) AS c
             FROM convention AS t1
             GROUP BY state
             ORDER BY c DESC) AS t2
          WHERE t2.c > 4";
  $list =  preExeFetNOPARA($sql);
  //print_r($list);
  return $list;
}
function displayConByState($list)
{
  foreach ($list as $item) {
    echo $item['state'] . " " . $item['c'] . "<br>";
  }
}

/* total convention */
function getConTot()
{
  global $dbConn;
  $sql = "SELECT count(*) as conTotal FROM convention";
  $tot =  preExeFetNOPARA($sql);
  //print_r($tot);
  return $tot;
}
function displayConTot($tot)
{
  foreach ($tot as $part) {
    echo $part['conTotal'] . " ";
  }
}

/* list of the upcoming conventions based on date, one or more */
function getNextCon()
{
  global $dbConn;



  $sql = "SELECT COUNT(*) as c
          FROM
              (SELECT 
                  id, STR_TO_DATE(CONCAT(start_date, ' ', year), '%M %d %Y') AS result
              FROM convention
              ORDER BY result IS NULL , result ASC) AS t1
          WHERE
              result > CURRENT_DATE()
          GROUP BY result
          ORDER BY result ASC
          limit 1";

  $stmt = $dbConn->prepare($sql);
  $stmt->execute();
  $records = $stmt->fetchAll(PDO::FETCH_ASSOC);

  foreach ($records as $item) {
    $limit =  $item['c'];
  }

  $sql = "SELECT *, STR_TO_DATE(CONCAT(start_date, ' ', year), '%M %d %Y') AS r
          FROM convention 
          WHERE STR_TO_DATE(CONCAT(start_date, ' ', year), '%M %d %Y') > CURRENT_DATE() 
          ORDER BY r IS NULL , r ASC limit ". $limit;
  $stmt = $dbConn->prepare($sql);
  $stmt->execute();
  $records = $stmt->fetchAll(PDO::FETCH_ASSOC);

  return $records;
}

/* convention display with update and delete buttons for each */
function displayConAdmin($convention)
{
  foreach ($convention as $eachCon) {
    $newDate = dateDisplay($eachCon['start_date'], $eachCon['end_date']);

    echo "<tr>";
    echo "<td>" . $eachCon['conName'] . "</td>";
    echo "<td>
    <a href='conUpdate.php?id=" . $eachCon['id'] . "'>
      <button type=\"button\" class=\"btn\">
        <span class=\"glyphicon glyphicon-pencil\" aria-hidden=\"true\"></span> Update
      </button>
    </a>";
    echo "</td>";
    echo "<td>
    <a href='deleteCon.php?id=" . $eachCon['id'] . "' onclick= 'return confirmDelete(\"" . $eachCon['conName'] . "\")' >
      <button type=\"button\" class=\"btn\">
        <span class=\"glyphicon glyphicon-remove\" aria-hidden=\"true\"></span> Delete
      </button>
    </a>";
    echo "</td>";
    echo "<td>" . $newDate . "</td>";
    echo "<td>" . $eachCon['year'] . "</td>";
    echo "<td>" . $eachCon['event_location'] . "</td>";
    echo "<td>" . $eachCon['city'] . "</td>";
    echo "<td>" . $eachCon['state'] . "</td>";
    echo "<td>" . $eachCon['country'] . "</td>";
    echo "<td> <a href='https://" . $eachCon['website'] . "' target='_blank'>" . $eachCon['website'] . "</a> </td>";
    echo "</tr>";
  }
}
/* end admin reports*/
?>

<script>
  function confirmDelete(userFullName) {
    var confirmDelete = confirm("Do you really want to delete: " + userFullName + "");
    if (!confirmDelete) {
      return false;
    } else {
      return true;
    }
  }
</script>

<!-- Collect the nav links, forms, and other content for toggling -->
<ul class="navbar-nav me-auto mb-2 mb-lg-0">
  <li class="nav-item">
    <a class="nav-link" href="index.php">Home</a>
  </li>
  <li class="nav-item">
    <a class="nav-link" href="collection.php">Collection</a>
  </li>
  <li class="nav-item">
    <a class="nav-link" href="convention.php">Convention</a>
  </li>
  <li class="nav-item">
    <a class="nav-link active" aria-current="page" href="login.php">Admin</a>
  </li>
  <li class="nav-item">
    <a class="nav-link" href="conInsert.php">New Convention</a>
  </li>
  <li class="nav-item">
    <a class="nav-link" href="conUpdate.php">Update Convention</a>
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
  <form method="POST" name="conForm" class="row gx-4 gy-3 align-items-center">

    <div class="col-auto">
      <div class="input-group">
        <div class="input-group-text">Name</div>
        <input type="text" name="conName" placeholder="Enter Convention Name" />
      </div>
    </div>

    <div class="col-auto">
      <input type="submit" value="Search" name="filterForm" class="btn" />
    </div>

    <div class="col-auto">
      <a href="conInsert.php" class="btn">Add New Con!</a>
    </div>

    <div class="col-auto">
      <!-- Button trigger modal -->
      <button type="button" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#myModal">
        Admin Reports
      </button>
    </div>

  </form>
</div>
<br><br>
<div class="wrapper form-display" style="overflow: auto;">
  <table class="table table-sm table-striped table-hover display nowrap" id="adminDisplay" style="width:auto;">
    <caption>Admin Conventions</caption>
    <!--https://www.w3schools.com/bootstrap/bootstrap_tables.asp-->
    <thead class='table-dark'>
      <tr>
        <th>Name</th>
        <th>Alter</th>
        <th>Remove</th>
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
        displayConAdmin($filterCon);
      } else {
        $convention = getConData("convention");
        displayConAdmin($convention);
      }
      ?>
    </tbody>
  </table>
</div>

<!-- Modal -->
<div class="modal fade" id="myModal" tabindex="-1" aria-labelledby="myModalLabel" aria-hidden="true">
  <div class="modal-dialog modal-xl">
    <div class="modal-content">
      <div class="modal-header">
        <h6 class="modal-title fs-5" id="myModalLabel">Admin Report</h6>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
      </div>

      <div class="modal-body">
        <p>Average number of conventions per State:
          <?php $num = getConAvg();
          displayConAvg($num); ?></p>
        <p>Number of convention per State with more than four:<br>
          <?php $list = getConByState();
          displayConByState($list); ?></p>
        <p>Total conventions:
          <?php $cnt = getConTot();
          displayConTot($cnt); ?> </p>
        <p>One or more upcoming conventions based on date:</p>

        <table class="table table-sm table-striped table-hover display nowrap" id="summaryDisplay" style="width:100%;">
          <caption>Admin Upcoming Convention Summary</caption>
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
            $groupCons = getNextCon();
            displayCon($groupCons);
            ?>
          </tbody>
        </table>
      </div>

      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
      </div>
      
    </div>
  </div>
</div>

<br><br>
<?php include 'footer.inc' ?>

<script>
  //https://datatables.net/reference/option
  new DataTable('#adminDisplay', {
    lengthMenu: [8, 16],
    searching: false,
    ordering: false,
    responsive: true,
    pagingType: 'simple'
  });
  new DataTable('#summaryDisplay', {
    lengthMenu: [5, 10],
    searching: false,
    ordering: false,
    responsive: true,
    pagingType: 'simple'
  });
</script>

</body>

</html>