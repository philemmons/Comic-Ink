<?php
session_start();

if (!isset($_SESSION["user"])) {  //Check whether the admin has logged in
    $_SESSION["name"] = "Guest";
}

include 'header.html';
include 'php/sourceFinal.php';

$dbConn = getDBConnection();

if(isset($_POST['logout'])){
    session_destroy();
    header("Location: index.php");
}

function displayCon($convention){
    foreach($convention as $eachCon) {
        echo"<tr>";
        //$str = $eachCon['conName'] . ", " .$eachCon['city'] .", ".$eachCon['state'] .", ".$eachCon['turnOut'] .", ".$eachCon['creator'];
        echo "<td>".$eachCon['conName'] . "</td><td>" .$eachCon['city'] ."</td><td>".$eachCon['state'] ."</td><td>".$eachCon['turnOut'] ."</td><td>".$eachCon['creator']."</td>";
        echo "<td> <a href='".$eachCon[website]."' target='_blank'/>".$eachCon[website]."</a></td>";
        echo "</tr>";
    }
}
?>
        <!-- Collect the nav links, forms, and other content for toggling -->
        <div class="collapse navbar-collapse" id="bs-example-navbar-collapse-1">
          <ul class="nav navbar-nav">
            <li ><a href="index.php">Home</a></li>
            <li><a href="collection.php">Collection</a></li>
            <li class="active"><a href="convention.php">Convention<span class="sr-only">(current)</span></a></li>
            <li><a href="login.php">Admin</a></li>
          </ul>
            
   <?php if (isset($_SESSION["username"])) { ?> 
        <form method ="get" id="one" >
                <input type="submit" value="Logout" class="btn" name="logout" style="box-shadow: none !important; margin-top: 4px;"/>
       </form>
   <?php; } ?>
            
        </div><!-- /.navbar-collapse -->
      </div><!-- /.container-fluid -->
    </nav>
    <br>
    <form method="POST" name="conForm">
        <table>
            <th colspan="2">Welcome <?=$_SESSION['name']?>
                <td><input type="submit" value="Search" name="filterForm" class="btn"/>
                </td>
                <td>
                    <input type="submit" value="All Conventions" name="allIn" class="btn"/>
                </td>
            </th>
            <tr>
                <td><label id="l5">Name:</label>  <input type="text" name="conName" size="30" placeholder="enter convention name here."/>
                </td>
                <td><label id="l6">Creator:</label>   <input type="text" name="creator" size="20" placeholder="first or last name"/>
                </td>
                <td><label id="l7">State:</label> 
                    <select name="state">
                        <option value= "" disabled selected>select one</option>
                         <?php
                            $allState = get('convention', 'state');
                            //print_r($allState);
                            foreach($allState as $singleState) {
                                echo "<option>" .$singleState['state']. " </option>";
                            }
                        ?>
                        
                    </select>
                </td>
                <td><label id="l8">Sort By:</label> 
                <select name="sortBy">
                    <option value= "" disabled selected>select one</option>
                    <option value="conName" >Name</option>
                    <option value="creator" >Creator</option>
                    <option value="turnOut ASC" >Turn Out: Low to High</option>
                    <option value="turnOut DESC" >Turn Out: High to Low</option>
                </select>
                </td>
            </tr>
        </table>
    </form>

     <form method="POST" action="">
        <div class="wrapper">
        <table class="table table-condensed" id="convDisplay"><!--https://www.w3schools.com/bootstrap/bootstrap_tables.asp-->
            <thead>
              <tr>
                <th>Name</th>
                <th>City</th>
                <th>State</th>
                <th>Attendance</th>
                <th>Creator</th>
                <th>Offical</th>
              </tr>
            </thead>
            <tbody>
            <?php
                if( isset($_POST['filterForm']) ){
                    $filterCon = goSQLcon("convention");
                    displayCon($filterCon);
                 
                }else{ // Display inventory initially.
                    $convention = getInfo("convention");
                    displayCon($convention);
                }
            ?>
            </tbody>
        </table>
        </div>
    </form>
    
    
 <script>
    //https://datatables.net/reference/option
    $(document).ready(function() {
        $('#convDisplay').DataTable({
            "lengthMenu": [10,15,30],
            "searching": false,
            "ordering": false
        });
    } );
    </script>
</body>
</html>
