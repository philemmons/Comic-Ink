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
//admin reports
function getAvg()
{
  global $dbConn;
  $sql = "select round(avg(turnOut))
            from convention";
  $ans =  preExeFetNOPARA($sql);
  //print_r($ans);
  return $ans;
}

function displayNum($num)
{
  foreach ($num as $digit) {
    echo $digit['round(avg(turnOut))'] . " ";
  }
}

function getList()
{
  global $dbConn;
  $sql = "SELECT state, count( * )
          FROM convention
          GROUP BY state 
          ORDER BY count( * ) DESC, state ASC";
  $list =  preExeFetNOPARA($sql);
  //print_r($list);
  return $list;
}

function displayList($list)
{
  foreach ($list as $item) {
    echo $item['state'] . " " . $item['count( * )'] . ", ";
  }
}
function getTot()
{
  global $dbConn;
  $sql = "SELECT sum(turnOut)
          FROM convention";
  $tot =  preExeFetNOPARA($sql);
  //print_r($tot);
  return $tot;
}
function displayTot($tot)
{
  foreach ($tot as $part) {
    echo $part['sum(turnOut)'] . " ";
  }
}
function getCount()
{
  global $dbConn;
  $sql = "SELECT count(con_id)
          FROM convention";
  $cnt =  preExeFetNOPARA($sql);
  //print_r($cnt);
  return $cnt;
}
function displayCount($cnt)
{
  foreach ($cnt as $one) {
    echo $one['count(con_id)'] . " ";
  }
}

function getBig()
{
  global $dbConn;
  $sql = "SELECT *
        FROM convention
        WHERE turnOut = (
        SELECT max( turnOut )
        FROM convention ) ";
  $big =  preExeFetNOPARA($sql);
  //print_r($big);
  return $big;
}
function displayBig($big)
{
  foreach ($big as $small) {
    echo $small['conName'] . "<br>" . $small['city'] . ", " . $small['state'] . "<br>" . $small['turnOut'] . "<br>" . $small['creator'] .
      "<br> <a href='" . $small['website'] . "' target='_blank'/>" . $small['website'] . "</a>";
  }
}
//end admin reports

?>

<script>
  function confirmDelete(userFullName) {
    var confirmDelete = confirm("Do you really want to delete: " + userFullName + "");
    if (!confirmDelete) {
      return false;
    } else {
      return true;
    }
  }
</script>
<!-- Collect the nav links, forms, and other content for toggling -->
<div class="collapse navbar-collapse" id="bs-example-navbar-collapse-1">
  <ul class="nav navbar-nav">
    <li><a href="index.php">Home</a></li>
    <li><a href="collection.php">Collection</a></li>
    <li><a href="convention.php">Convention</a></li>
    <li class="active"><a href="admin.php">Admin<span class="sr-only">(current)</span></a></li>
  </ul>

  <?php
  if (isset($_SESSION["user"])) {
    echo '<form method ="POST" id="one" >';
    echo '<input type="submit" value="Logout" class="btn" name="logout" style="box-shadow: none !important; margin-top: 4px;"/>';
    echo '</form>';
  }
  ?>

</div><!-- /.navbar-collapse -->
</div><!-- /.container-fluid -->
</nav>

<div class="wrapper">
  <table class="table table-striped" id="adminDisplay">
    <thead>
      <tr>
        <th colspan="3">Welcome <?= $_SESSION['username'] ?>
        <th></th>
        <th>
          <form action="conInsert.php">
            <input type="submit" value="Add New Con!" class="btn btn-sm" />
          </form>
        </th>
        <th colspan="3"><button type="" class="btn btn-sm" data-toggle="modal" data-target="#myModal">Admin Reports</button>
        </th>

      </tr>
      <tr>
        <th>Name</th>
        <th>City</th>
        <th>State</th>
        <th>Creator</th>
        <th>More Info</th>
        <th>Attendance</th>
        <th></th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      <?php
      $convention = getInfo("convention");
      foreach ($convention as $eachCon) {
        //$conData="con_id=".$eachCon['con_id']."<br>".$eachCon['conName']."<br>".$eachCon['city']."<br>".$eachCon['state']."<br>".$eachCon['creator']."<br>".$eachCon['website']."<br>".$eachCon['turnOut']."<br>";
        echo "<tr>";
        //echo "<td><a href='conInfo.php?".$conData."' target='userInfoFrame'>" . $eachCon['conName'] . "</a></td> ";

        echo "<td>" . $eachCon['conName'] . "</td><td>" . $eachCon['city'] . "</td><td>" . $eachCon['state'] . "</td><td>" . $eachCon['creator'] . "</td><td style='text-transform: lowercase'>" . $eachCon['website'] . "</td><td>" . $eachCon['turnOut'];


        echo "</td><td><a href='conUpdate.php?con_id=" . $eachCon['con_id'] . "'>
                      <button type=\"button\" class=\"btn btn-sm\">
                      <span class=\"glyphicon glyphicon-pencil\" aria-hidden=\"true\"></span> Update
                      </button></a>";

        echo "</td><td><a href='deleteCon.php?con_id=" . $eachCon['con_id'] . "' onclick= 'return confirmDelete(\"" . $eachCon['conName'] . "\")' >
                      <button type=\"button\" class=\"btn btn-sm\">
                      <span class=\"glyphicon glyphicon-remove\" aria-hidden=\"true\"></span> Delete
                      </button></a>";
        echo "</td></tr>";
      }
      ?>
    </tbody>
  </table>
</div>

<!-- Modal -->
<div class="modal fade" id="myModal" role="dialog">
  <div class="modal-dialog modal-sm">

    <!-- Modal content-->
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal">&times;</button>
        <h3 class="modal-title">Admin Reports:</h3>
      </div>
      <div class="modal-body">
        <p>Total convention attendance:
          <?php
          $tot = getTot();
          displayTot($tot);
          ?></p>
        <p>Average attendance conventions:
          <?php
          $num = getAvg();
          displayNum($num);
          ?></p>
        <p>Number of convention by state:<br>
          <?php
          $list = getList();
          displayList($list);
          ?></p>
        <p>Total conventions:
          <?php
          $cnt = getCount();
          displayCount($cnt);
          ?></p>
        <p>Largest attendance convention details:<br>
        <div style='padding-left: 20px' <?php
                                        $big = getBig();
                                        displayBig($big);
                                        ?></div>
          </p>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn" data-dismiss="modal">Close</button>
        </div>
      </div>

    </div>
  </div>

  <?php include 'footer.inc' ?>

  <script>
    //https://datatables.net/reference/option
    $(document).ready(function() {
      $('#adminDisplay').DataTable({
        "lengthMenu": [5, 10, 20],
        "searching": false,
        "ordering": false
      });
    });
  </script>

  </body>

  </html>