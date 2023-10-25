<?php
session_start();  //start or resume an existing session
include 'header.html';
include 'php/sourceFinal.php';

if (isset($_POST['logout'])) {
  session_destroy();
  header("Location: index.php");
}
?>

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

<div id="carouselExampleInterval" class="carousel slide" data-bs-ride="carousel">
  <div class="carousel-inner">

    <div class="carousel-item active" data-bs-interval="2000">
      <img src="img/1.png" class="d-block w-100" alt="starwars #1 1977">
    </div>
    <div class="carousel-item" data-bs-interval="2000">
      <img src="img/2.png" class="d-block w-100" alt="wolverine #1 1982">
    </div>
    <div class="carousel-item">
      <img src="img/3.png" class="d-block w-100" alt="weird fantasy #18 1953">
    </div>
    <div class="carousel-item" data-bs-interval="2000">
      <img src="img/4.png" class="d-block w-100" alt="mad magazine #1 1952">
    </div>
    <div class="carousel-item" data-bs-interval="2000">
      <img src="img/5.png" class="d-block w-100" alt="daredevil #1 1964">
    </div>
    <div class="carousel-item">
      <img src="img/6.png" class="d-block w-100" alt="doctor strange #169 1969">
    </div>
    <div class="carousel-item" data-bs-interval="2000">
      <img src="img/7.png" class="d-block w-100" alt="thor #126 1966">
    </div>
    <div class="carousel-item" data-bs-interval="2000">
      <img src="img/8.png" class="d-block w-100" alt="tales of suspense #39 1963">
    </div>
    <div class="carousel-item">
      <img src="img/9.png" class="d-block w-100" alt="detective comics #27 1939">
    </div>
    <div class="carousel-item" data-bs-interval="2000">
      <img src="img/10.png" class="d-block w-100" alt="watchmen #1 1986">
    </div>
    <div class="carousel-item" data-bs-interval="2000">
      <img src="img/11.png" class="d-block w-100" alt="action comics #1 1938">
    </div>
    <div class="carousel-item">
      <img src="img/12.png" class="d-block w-100" alt="new mutants #98 1991">
    </div>
    <div class="carousel-item" data-bs-interval="2000">
      <img src="img/13.png" class="d-block w-100" alt="justice league of america #1 1960">
    </div>
  </div>
  <button class="carousel-control-prev" type="button" data-bs-target="#carouselExampleInterval" data-bs-slide="prev">
    <span class="carousel-control-prev-icon" aria-hidden="true"></span>
    <span class="visually-hidden">Previous</span>
  </button>
  <button class="carousel-control-next" type="button" data-bs-target="#carouselExampleInterval" data-bs-slide="next">
    <span class="carousel-control-next-icon" aria-hidden="true"></span>
    <span class="visually-hidden">Next</span>
  </button>
</div>

<?php include 'footer.inc' ?>

</body>

</html>