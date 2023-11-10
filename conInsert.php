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

?>

<script src='js/jsFinal.js'></script>

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
    <a class="nav-link active" aria-current="page" href="conInsert.php">New Convention</a>
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

<<br>
  <div class="wrapper form-display">
    <h6>
      Welcome <?= $_SESSION['name'] ?> - New Convention Form
    </h6>
    <br>

    <?php
      if (isset($_POST['submitInsert'])) {
        //echo "form was submitted";
        addCon();
        echo "<h6 id='addDisplay'>Convention Added!</h6>";
      }
      ?>
    <form method='POST' name="insertConForm" class='row gx-4 gy-3 align-items-center' onsubmit='return validateInsert()' ;>

      <div class="col-md-2">
        <div class="form-floating">
          <input type="text" class="form-control" id="conID" placeholder="Default - auto incremented" name="conID" disabled />
          <label for="conID">ConID</label>
        </div>
      </div>

      <div class="col-md-10">
        <div class="form-floating">
          <input type="text" class="form-control" id="conName" placeholder="Enter Convention Name" name="conName" />
          <label for="conName">Convention Name</label>
          <span id="conNameError"></span>
        </div>
      </div>

      <div class="col-md-4">
        <div class="form-floating">
          <input type="text" class="form-control" id="start_date" name="start_date" />
          <label for="start_date">Start Month & Day Only</label>
          <span id="start_dateError"></span>
        </div>
      </div>

      <div class="col-md-4">
        <div class="form-floating">
          <input type="text" class="form-control" id="end_date" name="end_date" />
          <label for="end_date">End Month & Day Only</label>
          <span id="end_dateError"></span>
        </div>
      </div>

      <div class="col-md-4">
        <div class="form-floating">
          <input type="int" class="form-control" id="year" placeholder="Enter Year:" name="year" />
          <label for="year">Year</label>
          <span id="yearError"></span>
        </div>
      </div>

      <div class="col-12">
        <div class="form-floating">
          <input type="text" class="form-control" id="event_location" placeholder="Enter Location" name="event_location" />
          <label for="event_location">Event Location</label>
          <span id="event_locationError"></span>
        </div>
      </div>

      <div class="col-md-4">
        <div class="form-floating">
          <input type="text" class="form-control" id="city" placeholder="Enter City" name="city" />
          <label for="city">City</label>
          <span id="cityError"></span>
        </div>
      </div>

      <div class="col-md-4">
        <div class="form-floating">
          <input type="text" class="form-control" id="state" placeholder="Enter State" name="state" />
          <label for="state">State</label>
          <span id="stateError"></span>
        </div>
      </div>

      <div class="col-md-4">
        <div class="form-floating">
          <input type="text" class="form-control" id="country" placeholder="Enter Country" name="country" />
          <label for="country">Country</label>
          <span id="countryError"></span>
        </div>
      </div>

      <div class="col-md-12">
        <div class="form-floating">
          <input type="text" class="form-control" id="website" placeholder="xxx.example.xxx" name="website" />
          <label for="website">Website</label>
          <span id="websiteError"></span>
        </div>
      </div>

      <div class="col-md-3">
        <button type="submit" name="submitInsert" value="insert" class="btn" data-bs-toggle="modal" data-bs-target="#insertModal"> Add New Convention </button>
      </div>

      <div class="col-md-3">
        <button type="reset" name="reset" value="reset" class="btn" onclick="resetFields()"> Reset </button>
      </div>

      <div class="col-md-6">
        <a href="admin.php#middlePage" class="btn" style="float:right">Return to Admin</a>
      </div>
    </form>
  </div>

  <!-- Modal -->
<div class="modal fade" id="insertModal" tabindex="-1" aria-labelledby="insertModalLabel" aria-hidden="true">
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

  <br><br>
  <?php include 'footer.inc' ?>

  </body>

  </html>