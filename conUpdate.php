<?php
session_start();

if (!isset($_SESSION["status"])) {  //Check whether the admin has logged in
  header("Location: login.php");
}

include 'header.html';
include 'php/sourceFinal.php';

$dbConn = getDBConnection();

if (isset($_POST['logout'])) {
  session_destroy();
  header("Location: index.php");
}
//NOTE: the next 3 sections of code sequence matters for the updated output

if (isset($_POST['submitUpdate'])) {  //admin has submitted the "update user" form
  $sql = "UPDATE convention
          SET conName = :conName,
              start_date = :start_date,
              end_date = :end_date,
              year = :year,
              event_location = :event_location,
              city = :city,
              state = :state,
              country =:country,
              website = :website   
          WHERE id = :con_id";

  $np = array();

echo $_POST['conID'];
die();

  $np[':con_id'] = htmlspecialchars($_POST['conID'], ENT_QUOTES);
  $np[':conName']  = htmlspecialchars($_POST['conName'], ENT_QUOTES);
  $np[':start_date'] = htmlspecialchars($_POST['start_date'], ENT_QUOTES);
  $np[':end_date'] = htmlspecialchars($_POST['end_date'], ENT_QUOTES);
  $np[':year'] = htmlspecialchars($_POST['year'], ENT_QUOTES);
  $np[':event_location'] = htmlspecialchars($_POST['event_location'], ENT_QUOTES);
  $np[':city'] = htmlspecialchars($_POST['city'], ENT_QUOTES);
  $np[':state'] = htmlspecialchars($_POST['state'], ENT_QUOTES);
  $np[':country'] = htmlspecialchars($_POST['country'], ENT_QUOTES);
  $np[':website'] = htmlspecialchars($_POST['website'], ENT_QUOTES);

  $stmt = $dbConn->prepare($sql);
  $stmt->execute($np);

  sleep(2); // pause the modal

} //eof if

if (isset($_GET['id'])) {
  $conInfo = getConInfo($_GET['id']);
  //echo gettype($conInfo)."<br>";
  //var_dump($conInfo);
  //die();
}

?>

<script src='js/jsFinal.js'></script>

<script>
  $(document).ready(function() {
    $("#conName").change(function() {
      notBlank("#conName");
    });
  }); //documentReady
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
    <a class="nav-link" href="login.php">Admin</a>
  </li>
  <li class="nav-item">
    <a class="nav-link" href="conInsert.php">New Convention</a>
  </li>
  <li class="nav-item">
    <a class="nav-link active" aria-current="page" href="conUpdate.php">Update Convention</a>
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
    Welcome <?= $_SESSION['name'] ?> - Update Convention Info
  </h6>
  <br>
  <form method='POST' name= "updateConForm" class='row gx-4 gy-3 align-items-center' action="">

    <div class="col-md-2">
      <div class="form-floating">
        <input type="text" class="form-control" id="conID" placeholder="Default - auto incremented" name="conID" value="<?= $conInfo['id'] ?>" disabled />
        <label for="conID">ConID</label>
        <span id="conIDError"></span>
      </div>
    </div>

    <div class="col-md-10">
      <div class="form-floating">
        <input type="text" class="form-control" id="conName" placeholder="Enter Convention Name" name="conName" value="<?= $conInfo['conName'] ?>" />
        <label for="conName">Convention Name</label>
        <span id="conNameError"></span>
      </div>
    </div>

    <div class="col-md-4">
      <div class="form-floating">
        <input type="text" class="form-control" id="start_date" name="start_date" value="<?= $conInfo['start_date'] ?>" />
        <label for="start_date">Start Date</label>
        <span id="start_dateError"></span>
      </div>
    </div>

    <div class="col-md-4">
      <div class="form-floating">
        <input type="text" class="form-control" id="end_date" name="end_date" value="<?= $conInfo['end_date'] ?>" />
        <label for="end_date">End Date</label>
        <span id="end_dateError"></span>
      </div>
    </div>

    <div class="col-md-4">
      <div class="form-floating">
        <input type="int" class="form-control" id="year" placeholder="Enter Year:" name="year" value="<?= $conInfo['year'] ?>" />
        <label for="year">Year</label>
        <span id="yearError"></span>
      </div>
    </div>

    <div class="col-12">
      <div class="form-floating">
        <input type="text" class="form-control" id="event_location" placeholder="Enter Location" name="event_location" value="<?= $conInfo['event_location'] ?>" />
        <label for="event_location">Event Location</label>
        <span id="event_locationError"></span>
      </div>
    </div>

    <div class="col-md-4">
      <div class="form-floating">
        <input type="text" class="form-control" id="city" placeholder="Enter City" name="city" value="<?= $conInfo['city'] ?>" />
        <label for="city">City</label>
        <span id="cityError"></span>
      </div>
    </div>

    <div class="col-md-4">
      <div class="form-floating">
        <input type="text" class="form-control" id="state" placeholder="Enter State" name="state" value="<?= $conInfo['state'] ?>" />
        <label for="state">State</label>
        <span id="stateError"></span>
      </div>
    </div>

    <div class="col-md-4">
      <div class="form-floating">
        <input type="text" class="form-control" id="country" placeholder="Enter Country" name="country" value="<?= $conInfo['country'] ?>" />
        <label for="country">Country</label>
        <span id="countryError"></span>
      </div>
    </div>

    <div class="col-md-12">
      <div class="form-floating">
        <input type="text" class="form-control" id="website" placeholder="xxx.example.xxx" name="website" value="<?= $conInfo['website'] ?>" />
        <label for="website">Website</label>
        <span id="websiteError"></span>
      </div>
    </div>

    <div class="col-md-4">
      <input type="submit" name="submitUpdate" value="Update" class="btn" />
    </div>

    <div class="col-md-4">
      <button type="reset" name="reset" value="reset" class="btn"> Reset </button>
    </div>

    <div class="col-md-4">
      <a href="admin.php" class="btn" data-dismiss="modal" style="float:right">Return to Admin</a>
    </div>

  </form>
</div>

<div id="modal-content" class="modal fade" tabindex="-1" role="dialog">
  <div class="modal-dialog modal-sm">
    <div class="modal-content">
      <div class="modal-body" style="text-align: center">
        <h3 id="txtname">Update</h3>
        <img src='img/complete.png' alt='complete word with red border with a brick like texture.' />
      </div>
    </div>
  </div>
</div>

<br><br>
<?php include 'footer.inc' ?>

</body>

</html>