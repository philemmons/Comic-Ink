<?php
session_start();  //start or resume an existing session
include 'header.html';
include 'php/sourceFinal.php';
?>
        <!-- Collect the nav links, forms, and other content for toggling -->
        <div class="collapse navbar-collapse" id="bs-example-navbar-collapse-1">
          <ul class="nav navbar-nav">
            <li class="active"><a href="index.php">Home<span class="sr-only">(current)</span></a></li>
            <li><a href="collection.php">Collection</a></li>
            <li><a href="convention.php">Convention</a></li>
            <li><a href="login.php">Admin</a></li>
          </ul>
   <?php             
   if (isset($_SESSION["username"])) {  //Check whether the admin has logged in
        echo <form method ="get" id="one" >
                echo <input type="submit" value="Logout" class="btn" name="logout" style="box-shadow: none !important; margin-top: 4px;"/>
        echo </form>
    ?>
        </div><!-- /.navbar-collapse -->
      </div><!-- /.container-fluid -->
    </nav>
        
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
