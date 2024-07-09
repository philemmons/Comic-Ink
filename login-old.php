<?php
session_start();

if (isset($_SESSION["status"]) && ($_SESSION['status'] == getenv('LOGIN_STATUS'))) {  //Check whether the admin has logged in
  header("Location:admin.php");
  exit;
} else {
  $_SESSION["name"] = "Guest";
}

include_once 'header.inc';
include_once 'php/sourceFinal.php';

$dbConn = getDBConnection();

if (isset($_POST['logout'])) {
  session_destroy();
  header("Location: index.php");
  exit;
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
    <a class="nav-link" href="graphicNovel.php">Graphic Novels</a>
  </li>
  <li class="nav-item">
    <a class="nav-link" href="convention.php">Conventions</a>
  </li>
  <li class="nav-item">
    <a class="nav-link active" aria-current="page" href="login.php">Admin</a>
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

<!-- https://www.w3schools.com/howto/howto_css_login_form.asp -->
<div id="mLogin">
  <h6>Please login to continue...</h6>
  <br>
  <button onclick="document.getElementById('id01').style.display='block'" class="btn">Login</button>
  <?php
  if (isset($_POST['login'])) {
    goMain();
  }
  ?>
  <br><br>
  <div id='wrapper-robot'>
    <div class='title'>
      <img src="img/robot.png" alt="Small robot typing on a small laptop at a desk." />
    </div>
  </div>
</div>
<div id="id01" class="modalAD">

  <form method="POST" class="modal-contentAD animateAD" name="loginForm">

    <div class="containerAD">
      <label><b>Username</b></label>
      <input type="text" placeholder="Enter Username" name="formUN" required id="ittAD">

      <label><b>Password</b></label>
      <input type="password" placeholder="Enter Password" name="formPW" required id="itpAD">

      <input type="submit" name="login" value="Login" class="btnAD btn" style="width: 100%;" />
    </div>

    <div class="containerAD">
      <button type="button" onclick="document.getElementById('id01').style.display='none'" id="cancelbtnAD" class="btn">Cancel</button>
    </div>
  </form>
</div>

<?php include_once 'footer.inc' ?>

<script>
  // Get the modal
  var modal = document.getElementById('id01');
  // When the user clicks anywhere outside of the modal, close it
  window.onclick = function(event) {
    if (event.target == modal) {
      modal.style.display = "none";
    }
  }
</script>

</body>

</html>