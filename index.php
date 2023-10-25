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

<div id="carouselExampleFade" class="carousel slide carousel-fade" data-bs-ride="carousel">
  <div class="carousel-inner">
    <div class="carousel-item active">
      <img src="..." class="d-block w-100" alt="...">
    </div>
    <div class="carousel-item">
      <img src="..." class="d-block w-100" alt="...">
    </div>
    <div class="carousel-item">
      <img src="..." class="d-block w-100" alt="...">
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

<div id="carouselExampleCaptions" class="carousel slide" data-bs-ride="carousel">
  <div class="carousel-indicators">
    <button type="button" data-bs-target="#carouselExampleCaptions" data-bs-slide-to="0" class="active" aria-current="true" aria-label="Slide 1"></button>
    <button type="button" data-bs-target="#carouselExampleCaptions" data-bs-slide-to="1" aria-label="Slide 2"></button>
    <button type="button" data-bs-target="#carouselExampleCaptions" data-bs-slide-to="2" aria-label="Slide 3"></button>
  </div>
  <div class="carousel-inner">
    <div class="carousel-item active">
      <img src="..." class="d-block w-100" alt="...">
      <div class="carousel-caption d-none d-md-block">
        <h5>First slide label</h5>
        <p>Some representative placeholder content for the first slide.</p>
      </div>
    </div>
    <div class="carousel-item">
      <img src="..." class="d-block w-100" alt="...">
      <div class="carousel-caption d-none d-md-block">
        <h5>Second slide label</h5>
        <p>Some representative placeholder content for the second slide.</p>
      </div>
    </div>
    <div class="carousel-item">
      <img src="..." class="d-block w-100" alt="...">
      <div class="carousel-caption d-none d-md-block">
        <h5>Third slide label</h5>
        <p>Some representative placeholder content for the third slide.</p>
      </div>
    </div>
  </div>
  <button class="carousel-control-prev" type="button" data-bs-target="#carouselExampleCaptions" data-bs-slide="prev">
    <span class="carousel-control-prev-icon" aria-hidden="true"></span>
    <span class="visually-hidden">Previous</span>
  </button>
  <button class="carousel-control-next" type="button" data-bs-target="#carouselExampleCaptions" data-bs-slide="next">
    <span class="carousel-control-next-icon" aria-hidden="true"></span>
    <span class="visually-hidden">Next</span>
  </button>
</div>


<div id="carouselCointainer">
  <div id="carousel-example-generic" class="carousel slide" data-ride="carousel">
    <!-- Indicators -->
    <ol class="carousel-indicators">
      <li data-target="#carousel-example-generic" data-slide-to="0" class="active"></li>
      <li data-target="#carousel-example-generic" data-slide-to="1"></li>
      <li data-target="#carousel-example-generic" data-slide-to="2"></li>
      <li data-target="#carousel-example-generic" data-slide-to="3"></li>
      <li data-target="#carousel-example-generic" data-slide-to="4"></li>
      <li data-target="#carousel-example-generic" data-slide-to="5"></li>
      <li data-target="#carousel-example-generic" data-slide-to="6"></li>
      <li data-target="#carousel-example-generic" data-slide-to="7"></li>
      <li data-target="#carousel-example-generic" data-slide-to="8"></li>
      <li data-target="#carousel-example-generic" data-slide-to="9"></li>
      <li data-target="#carousel-example-generic" data-slide-to="10"></li>
      <li data-target="#carousel-example-generic" data-slide-to="11"></li>
    </ol>

    <!-- Wrapper for slides -->
    <div class="carousel-inner" role="listbox">
      <div class="item active">
        <img src="img/1.jpg" alt="">
        <div class="carousel-caption">
          ...
        </div>
      </div>
      <div class="item">
        <img src="img/2.jpg" alt="">
        <div class="carousel-caption">
          ...
        </div>
      </div>
      <div class="item">
        <img src="img/3.jpg" alt="">
        <div class="carousel-caption">
          ...
        </div>
      </div>
      <div class="item">
        <img src="img/4.jpg" alt="">
        <div class="carousel-caption">
          ...
        </div>
      </div>
      <div class="item">
        <img src="img/5.jpg" alt="">
        <div class="carousel-caption">
          ...
        </div>
      </div>
      <div class="item">
        <img src="img/6.png" alt="">
        <div class="carousel-caption">
          ...
        </div>
      </div>
      <div class="item">
        <img src="img/4.jpg" alt="">
        <div class="carousel-caption">
          ...
        </div>
      </div>
      <div class="item">
        <img src="img/7.jpg" alt="">
        <div class="carousel-caption">
          ...
        </div>
      </div>
      <div class="item">
        <img src="img/8.jpg" alt="">
        <div class="carousel-caption">
          ...
        </div>
      </div>
      <div class="item">
        <img src="img/9.jpg" alt="">
        <div class="carousel-caption">
          ...
        </div>
      </div>

      <div class="item">
        <img src="img/10.jpg" alt="">
        <div class="carousel-caption">
          ...
        </div>
      </div>
      <div class="item">
        <img src="img/11.jpg" alt="">
        <div class="carousel-caption">
          ...
        </div>
      </div>
      <div class="item">
        <img src="img/12.jpg" alt="">
        <div class="carousel-caption">
          ...
        </div>
      </div>

    </div><!-- end wrapper -->

    <!-- Controls -->
    <a class="left carousel-control" href="#carousel-example-generic" role="button" data-slide="prev">
      <span class="glyphicon glyphicon-chevron-left" aria-hidden="true"></span>
      <span class="sr-only">Previous</span>
    </a>
    <a class="right carousel-control" href="#carousel-example-generic" role="button" data-slide="next">
      <span class="glyphicon glyphicon-chevron-right" aria-hidden="true"></span>
      <span class="sr-only">Next</span>
    </a>
  </div>
</div>
<!-- //carousel -->
</body>

</html>