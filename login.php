<?php
session_start();

if (!isset($_SESSION["user"])) {  //Check whether the admin has logged in
    $_SESSION["name"] = "Guest";
}else{
    header("Location:admin.php");
}

include 'header.html';
include 'php/sourceFinal.php';

$dbConn = getDBConnection();

if(isset($_POST['logout'])){
    session_destroy();
    header("Location: index.php");
}

?>
    
        <!-- Collect the nav links, forms, and other content for toggling -->
        <div class="collapse navbar-collapse" id="bs-example-navbar-collapse-1">
          <ul class="nav navbar-nav">
            <li><a href="index.php">Home</a></li>
            <li><a href="collection.php">Collection</a></li>
            <li><a href="convention.php">Convention</a></li>
            <li class="active"><a href="login.php">Admin<span class="sr-only">(current)</span></a></li>
          </ul>
          
    <?php if (isset($_SESSION["username"])) { 
      echo'<form method ="get" id="one" >';
        echo'<input type="submit" value="logout" class="btn" name="logout" style="box-shadow: none !important; margin-top: 4px;"/>';
      echo'</form>';
   } ?>
            
        </div><!-- /.navbar-collapse -->
      </div><!-- /.container-fluid -->
    </nav>
        
<!-- https://www.w3schools.com/howto/howto_css_login_form.asp -->
<div id="mLogin">
<h2>Admin Page: To continue...</h2>
<button onclick="document.getElementById('id01').style.display='block'" class="btn" style="font-size:2.0em;">Login</button>
        <?php
            if(isset($_POST['login'])){
                goMain();
        }
        ?>
        <br><br>
        <img src="img/key-robot.png" alt="robot with a gold key" />
</div>

<div id="id01" class="modalAD">
  
  <form method="POST" class="modal-contentAD animateAD" name="loginForm">
    <div class="imgcontainerAD">
      <span onclick="document.getElementById('id01').style.display='none'" class="closeAD" title="Close Modal">&times;</span>
     
    </div>

    <div class="containerAD">
      <label><b>Username</b></label>
      <input type="text" placeholder="Enter Username" name="username" required id="ittAD">

      <label><b>Password</b></label>
      <input type="password" placeholder="Enter Password" name="password" required id="itpAD">
        
      
      <!--<button type="submit" class="btnAD" name="login" value="ok">Login</button> -->
      <input type="submit" name ="login" value="Login" class="btnAD btn" />
     
    </div>

    <div class="containerAD" style="background-color:#f1f1f1">
      <button type="button" onclick="document.getElementById('id01').style.display='none'" id="cancelbtnAD" class="btn" >Cancel</button>
    </div>
  </form>
</div>

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
