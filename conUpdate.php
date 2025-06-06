<?php
session_start();

if (!isset($_SESSION["status"]) || ($_SESSION['status'] != getenv('LOGIN_STATUS'))) {  //Check whether the admin has logged in
  header("Location: login.php");
  exit;
}

if (isset($_POST['logout'])) {
  session_destroy();
  header("Location: /");
  exit;
}

include_once 'php/sourceFinal.php';

$dbConn = getDBConnection();

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

  $nPara[':con_id'] = htmlspecialchars($_GET['id'], ENT_QUOTES);
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

  $nPara = array();

  sleep(2); // pause the modal

} //eof if

include_once 'header.inc';
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
    <a class="nav-link" href="/">Home</a>
  </li>
  <li class="nav-item">
    <a class="nav-link" href="collection.php">Collection</a>
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
  <li class="nav-item">
    <a class="nav-link" href="conInsert.php">New Convention</a>
  </li>
  <li class="nav-item">
    <a class="nav-link active" aria-current="page" href="conUpdate.php">Update Convention<span class="visually-hidden">(current)</span></a>
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
    <h6>
      Welcome <?= $_SESSION['name'] ?> - Update Convention Info
    </h6>
    <br>

    <?php
    if (isset($_GET['id'])) {
      $conInfo = getConInfo($_GET['id']);
    ?>
      <form method='POST' name="updateConForm" class='row gx-4 gy-3 align-items-center' onsubmit='validateUpdate();'>

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
            <label for="start_date">Start Month & Day Only</label>
            <span id="start_dateError"></span>
          </div>
        </div>

        <div class="col-md-4">
          <div class="form-floating">
            <input type="text" class="form-control" id="end_date" name="end_date" value="<?= $conInfo['end_date'] ?>" />
            <label for="end_date">End Month & Day Only</label>
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

        <div class="col-md-3"><!-- Button trigger modal -->
          <button type="submit" name="submitUpdate" value="update" class="btn" data-bs-toggle="modal" data-bs-target="#updateModal">Update</btn>
        </div>

        <div class="col-md-3">
          <button type="reset" name="reset" value="reset" class="btn" onclick="myReset('updateConForm')" ;> Reset </button>
        </div>
      <?php } else {  ?>
        <h6> Hello, there was no convention selected which to update, and please select one from the Admin panel.</h6>
      <?php } ?>

      <div class="col-md-6">
        <a href="admin.php#middlePage" class="btn" style="float:right">Return to Admin</a>
      </div>

      </form>
  </div>

  <!-- Modal -->
  <div class="modal fade" id="updateModal" tabindex="-1" aria-labelledby="updateModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-sm">
      <div class="modal-content">
        <div class="modal-body" style="text-align: center">
          <h3>Update</h3>
          <img src='img/complete.png' alt='complete word with red border with a brick like texture.' />
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
        </div>
      </div>
    </div>
  </div>

  <?php include_once 'footer.inc' ?>

  </body>

  </html>