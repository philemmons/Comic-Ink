<?php
session_start();  //start or resume an existing session
include 'header.html';
include 'php/sourceFinal.php';

if (isset($_POST['logout'])) {
  session_destroy();
  header("Location: index.php");
}
?>

<!-- https://getbootstrap.com/docs/5.0/components/navbar/-->
<ul class="navbar-nav me-auto mb-2 mb-lg-0">
  <li class="nav-item">
    <a class="nav-link active" aria-current="page" href="index.php">Home</a>
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
</ul>

<?php
if (isset($_SESSION["username"])) {
  echo '<form method ="POST" id="one" >';
  echo '<input type="submit" value="Logout" class="btn" name="logout" style="box-shadow: none !important; margin-top: 4px;"/>';
  echo '</form>';
}
?>

</div><!-- .collapse navbar-collapse -->
</div><!-- .container-fluid -->
</nav>

<!-- https://getbootstrap.com/docs/5.0/components/carousel/ -->

<div id="carouselExampleFade center-carousel" class="carousel slide carousel-fade" data-bs-ride="carousel">
  <div class="carousel-inner">
    <div class="carousel-item active">
      <img src="img/1.jpg" class="d-block w-100" alt="...">
    </div>
    <div class="carousel-item">
      <img src="img/2.jpg" class="d-block w-100" alt="...">
    </div>
    <div class="carousel-item">
      <img src="img/3.jpg" class="d-block w-100" alt="...">
    </div>
  </div>
  <button class="carousel-control-prev" type="button" data-bs-target="#carouselExampleFade" data-bs-slide="prev">
    <span class="carousel-control-prev-icon" aria-hidden="true"></span>
    <span class="visually-hidden">Previous</span>
  </button>
  <button class="carousel-control-next" type="button" data-bs-target="#carouselExampleFade" data-bs-slide="next">
    <span class="carousel-control-next-icon" aria-hidden="true"></span>
    <span class="visually-hidden">Next</span>
  </button>
</div>


</body>

</html>