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

if (isset($_GET['submit'])) {  //admin has submitted the "update user" form
  $sql = "UPDATE convention
                  SET con_id = :con_id,
                      conName = :conName,
                      city = :city,
                      state = :state,
                      creator = :creator,
                      website = :website,
                      turnOut = :turnOut
                  WHERE con_id = :con_id";

  $np = array();
  $np[':con_id'] = $_GET['con_id'];
  $np[':conName']  = $_GET['conName'];
  $np[':city'] = $_GET['city'];
  $np[':state'] = $_GET['state'];
  $np[':creator'] = $_GET['creator'];
  $np[':website'] = $_GET['website'];
  $np[':turnOut'] = $_GET['turnOut'];
  $stmt = $dbConn->prepare($sql);
  $stmt->execute($np);

  sleep(2); // pause the modal

} //eof if



if (isset($_GET['con_id'])) {
  $conInfo = getConInfo($_GET['con_id']);
  //print_r($userInfo);
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
<div class="collapse navbar-collapse" id="bs-example-navbar-collapse-1">
  <ul class="nav navbar-nav">
    <li><a href="index.php">Home</a></li>
    <li><a href="collection.php">Collection</a></li>
    <li><a href="convention.php">Convention</a></li>
    <li><a href="admin.php">Admin</a></li>
    <li class="active"><a href="conUpdate.php">Update<span class="sr-only">(current)</span></a></li>
  </ul>

  <?php
  if (isset($_SESSION["status"])) {
    echo '<form method ="POST" id="one" >';
    echo '<input type="submit" value="Logout" class="btn" name="logout" style="box-shadow: none !important; margin-top: 4px;"/>';
    echo '</form>';
  }
  ?>

</div><!-- /.navbar-collapse -->
</div><!-- /.container-fluid -->
</nav>

<div class="wrapper">

  <form class="form-horizontal" onsubmit="return validateUpdate()">
    <h4>Welcome <?= $_SESSION['name'] ?> - Update Convention Info</h4>
    <div class="form-group">
      <label for="con_id" class="col-sm-2 control-label">Con_ID:</label>
      <div class="col-sm-10">
        <input class="form-control" id="con_id" placeholder="default A.I." type="int" name="con_id" value="<?= $conInfo['con_id'] ?>" />
        <span id="con_idError"></span>
      </div>
    </div>
    <div class="form-group">
      <label for="conName" class="col-sm-2 control-label">Convention Name:</label>
      <div class="col-sm-10">
        <input class="form-control" id="conName" placeholder="enter name" type="text" name="conName" value="<?= $conInfo['conName'] ?>" />
        <span id="conNameError"></span>
      </div>
    </div>

    <div class="form-group">
      <label for="city" class="col-sm-2 control-label">City:</label>
      <div class="col-sm-10">
        <input class="form-control" id="city" placeholder="enter city" type="text" name="city" value="<?= $conInfo['city'] ?>" />
        <span id="cityError"></span>
      </div>
    </div>
    <div class="form-group">
      <label for="state" class="col-sm-2 control-label">State:</label>
      <div class="col-sm-10">
        <input class="form-control" id="state" placeholder="eg - CA UT KA" type="text" name="state" value="<?= $conInfo['state'] ?>" />
        <span id="stateError"></span>
      </div>
    </div>

    <div class="form-group">
      <label for="creator" class="col-sm-2 control-label">Creator:</label>
      <div class="col-sm-10">
        <input class="form-control" id="creator" placeholder="enter first or last name" type="text" name="creator" value="<?= $conInfo['creator'] ?>" />
        <span id="creatorError"></span>
      </div>
    </div>
    <div class="form-group">
      <label for="website" class="col-sm-2 control-label">Full Website:</label>
      <div class="col-sm-10">
        <input class="form-control" id="website" placeholder="http(s)://xxx.example.xxx" type="text" name="website" value="<?= $conInfo['website'] ?>" />
        <span id="websiteError"></span>
      </div>
    </div>

    <div class="form-group">
      <label for="turnOut" class="col-sm-2 control-label">Ticket Price:</label>
      <div class="col-sm-10">
        <input class="form-control" id="turnOut" placeholder="xx.xx" type="decimal" name="turnOut" value="<?= $conInfo['turnOut'] ?>" / <span id="turnOutError"></span>
      </div>
    </div>

    <div class="form-group">
      <div class="col-sm-offset-2 col-sm-10">
        <!-- <button type="submit" class="btn btn-default">Sign in</button> -->
        <button type="submit" name="submit" value="update" class="btn"> Update </button>
        <button type="reset" name="reset" value="reset" class="btn"> Reset </button>
        <a href="admin.php" class="btn" data-dismiss="modal" style="float:right">Return to Admin</a>

      </div>
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

<?php include 'footer.inc' ?>

</body>

</html>