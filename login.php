<?php
session_start();

if (isset($_SESSION["status"]) && ($_SESSION['status'] == getenv('LOGIN_STATUS'))) {  //Check whether the admin has logged in
  header("Location:admin.php");
} else {
  $_SESSION["name"] = "Guest";
}

include_once 'header.inc';
include_once 'php/sourceFinal.php';

$dbConn = getDBConnection();

if (isset($_POST['logout'])) {
  session_destroy();
  header("Location: index.php");
}

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
    <a class="nav-link" href="convention.php">Conventions</a>
  </li>
  <li class="nav-item">
    <a class="nav-link active" aria-current="page" href="login.php">Admin<span class="visually-hidden">(current)</span></a>
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

  <article aria-label="Admin login screen">
    <div class="container mt-5">
      <div class="row justify-content-center">
        <div class="col-md-6 text-center">
          <section class="bg-body-tertiary p-2">
            <h3 class="h5 text-white">Please login to continue.</h3>
          </section>
          <button onclick="document.getElementById('id01').style.display='block'" class="btn my-4">Login</button>
<?php
          if (isset($_POST['login'])) {
            goMain();
          }
?>
          <img src="img/robot.png" class="mx-auto d-block border border-white border-2" alt="Small robot typing on a small laptop at a desk." />
        </div>
      </div>
    </div>
  </article>

  <article aria-label="Login modal">
    <div id="id01" class="modalAD">
      <form method="POST" class="modal-contentAD animateAD" name="loginForm">

        <div class="containerAD">
          <label for="ittAD"><b>Username</b></label>
          <input type="text" placeholder="Enter Username" name="formUN" required id="ittAD">

          <label for="itpAD"><b>Password</b></label>
          <input type="password" placeholder="Enter Password" name="formPW" required id="itpAD">

          <input type="submit" name="login" value="Login" class="btnAD btn" style="width: 100%;" />
        </div>

        <div class="containerAD">
          <button type="button" onclick="document.getElementById('id01').style.display='none'" id="cancelbtnAD" class="btn">Cancel</button>
        </div>

      </form>
    </div>
  </article>a

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
