<?php
session_start();  //start or resume an existing session

include_once 'php/sourceFinal.php';

if (isset($_POST['logout'])) {
  session_destroy();
  header("Location: /");
}

include_once 'header.inc';
?>

<ul class="navbar-nav me-auto mb-2 mb-lg-0">
  <li class="nav-item">
    <a class="nav-link active" aria-current="page" href="/">Home<span class="visually-hidden">(current)</span></a>
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
</ul>

<?php
if (isset($_SESSION["status"])) {
  echo '<form method ="POST" id="one" >';
  echo '<input type="submit" value="Logout" class="btn" name="logout" style="box-shadow: none !important;"/>';
  echo '</form>';
}
?>

</div><!-- .collapse navbar-collapse -->
</div><!-- .container-fluid -->
</nav>

<main id="main-content">
  <article aria-label="Influential and favorite covers">
    <div class="container mt-5">
      <div class="row justify-content-center">
        <div class="col-sm-8 p-3 bg-body-tertiary">
          <section>
            <h3 class="h6 text-white">The most significant comic mediums span a variety of genres, styles, and historical periods, each marking a pivotal moment in the medium's development. Below are thirteen covers of the most influential and some personal favorites.</h3>
          </section>
        </div>
      </div>
    </div>
  </article>


  <article aria-label="Thirteen famous covers" class="pt-5">
    <div id="carouselExampleInterval" class="carousel slide">

      <div class="carousel-inner">

        <div class="carousel-item active" data-bs-interval="2000">
          <img src="img/1.png" class="d-block w-100" alt="starwars #1 from 1977">
        </div>
        <div class="carousel-item" data-bs-interval="2000">
          <img src="img/2.png" class="d-block w-100" alt="wolverine #1 from 1982">
        </div>
        <div class="carousel-item" data-bs-interval="2000">
          <img src="img/3.png" class="d-block w-100" alt="weird fantasy #18 from 1953">
        </div>
        <div class="carousel-item" data-bs-interval="2000">
          <img src="img/4.png" class="d-block w-100" alt="mad magazine #1 from 1952">
        </div>
        <div class="carousel-item" data-bs-interval="2000">
          <img src="img/5.png" class="d-block w-100" alt="daredevil #1 from 1964">
        </div>
        <div class="carousel-item" data-bs-interval="2000">
          <img src="img/6.png" class="d-block w-100" alt="doctor strange #169 from 1969">
        </div>
        <div class="carousel-item" data-bs-interval="2000">
          <img src="img/7.png" class="d-block w-100" alt="thor #126 from from 1966">
        </div>
        <div class="carousel-item" data-bs-interval="2000">
          <img src="img/8.png" class="d-block w-100" alt="tales of suspense #39 from 1963">
        </div>
        <div class="carousel-item" data-bs-interval="2000">
          <img src="img/9.png" class="d-block w-100" alt="detective comics #27 from 1939">
        </div>
        <div class="carousel-item" data-bs-interval="2000">
          <img src="img/10.png" class="d-block w-100" alt="watchmen #1 from 1986">
        </div>
        <div class="carousel-item" data-bs-interval="2000">
          <img src="img/11.png" class="d-block w-100" alt="action comics #1 from 1938">
        </div>
        <div class="carousel-item" data-bs-interval="2000">
          <img src="img/12.png" class="d-block w-100" alt="new mutants #98 from 1991">
        </div>
        <div class="carousel-item" data-bs-interval="2000">
          <img src="img/13.png" class="d-block w-100" alt="justice league of america #1 from 1960">
        </div>

      </div>

      <button class="carousel-control-prev btn" type="button" data-bs-target="#carouselExampleInterval" data-bs-slide="prev">
        <span class="carousel-control-prev-icon" aria-hidden="true" title="Previous"></span>
        <span class="visually-hidden">Previous</span>
      </button>

      <button class="carousel-control-next btn" type="button" data-bs-target="#carouselExampleInterval" data-bs-slide="next">
        <span class="carousel-control-next-icon" aria-hidden="true" title="Next"></span>
        <span class="visually-hidden">Next</span>
      </button>

    </div>
  </article>


  <article aria-label="Important because">
    <div class="container mt-5">
      <div class="row justify-content-center mb-5">
        <div class="col-sm-8 p-3 bg-body-tertiary text-white mb-5">
          <p>These comics are significant not only for their storytelling and artistic achievements but also for their impact on the comic book industry and popular culture. They have inspired countless adaptations in film, television, and other media, and continue to influence new generations of creators and readers.</p>
        </div>
      </div>
    </div>
  </article>

  <?php include_once 'footer.inc' ?>

  </body>

  </html>