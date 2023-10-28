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

<div class="wrapper">
  <form class="form-horizontal" onsubmit="return validateInsert()">

    <h4>Welcome <?= $_SESSION['name'] ?> - New Convention Info</h4>
    <div class="form-group">
      <label for="con_id" class="col-sm-2 control-label">Con_ID:</label>
      <div class="col-sm-10">
        <input class="form-control" id="con_id" placeholder="Default value" type="int" name="con_id" value="default" />
        <span id="con_idError"></span>
      </div>
    </div>
    <div class="form-group">
      <label for="conName" class="col-sm-2 control-label">Convention Name:</label>
      <div class="col-sm-10">
        <input class="form-control" id="conName" placeholder="enter name" type="text" name="conName" />
        <span id="conNameError"></span>
      </div>
    </div>

    <div class="form-group">
      <label for="city" class="col-sm-2 control-label">City:</label>
      <div class="col-sm-10">
        <input class="form-control" id="city" placeholder="enter city" type="text" name="city" />
        <span id="cityError"></span>
      </div>
    </div>
    <div class="form-group">
      <label for="state" class="col-sm-2 control-label">State:</label>
      <div class="col-sm-10">
        <input class="form-control" id="state" placeholder="eg - CA UT KA" type="text" name="state" />
        <span id="stateError"></span>
      </div>
    </div>

    <div class="form-group">
      <label for="creator" class="col-sm-2 control-label">Creator:</label>
      <div class="col-sm-10">
        <input class="form-control" id="creator" placeholder="enter first or last name" type="text" name="creator" />
        <span id="creatorError"></span>
      </div>
    </div>
    <div class="form-group">
      <label for="website" class="col-sm-2 control-label">Full Website:</label>
      <div class="col-sm-10">
        <input class="form-control" id="website" placeholder="http(s)://xxx.example.xxx" type="text" name="website" />
        <span id="websiteError"></span>
      </div>
    </div>

    <div class="form-group">
      <label for="turnOut" class="col-sm-2 control-label">Attendance:</label>
      <div class="col-sm-10">
        <input class="form-control" id="turnOut" placeholder="est number" type="decimal" name="turnOut" />
        <span id="turnOutError"></span>
      </div>
    </div>

    <div class="form-group">
      <div class="col-sm-offset-2 col-sm-10">
        <!-- <button type="submit" class="btn btn-default">Sign in</button> -->
        <button type="submit" name="submit" value="insert" class="btn"> Insert </button>
        <button type="reset" name="reset" value="reset" class="btn" onclick="resetFields()"> Reset </button>
        <a href="admin.php" class="btn" data-dismiss="modal" style="float:right">Return to Admin</a>
        <?php
        if (isset($_GET['submit'])) {
          //echo "form was submitted";
          addCon();
          echo "<h3 id='addDisplay'>Convention Added!</h3>";
        }
        ?>
      </div>
    </div>
  </form>
</div>

<?php include 'footer.inc' ?>

</body>

</html>