<?php
session_start();

if (!isset($_SESSION["status"]) || ($_SESSION['status'] != getenv('LOGIN_STATUS'))) {  //Check whether the admin has logged in
     $_SESSION["name"] = "Guest";
}

include_once 'php/sourceFinal.php';

$dbConn = getDBConnection();

if (isset($_POST['logout'])) {
     session_destroy();
     header("Location: /");
     exit;
}

function dataDisplay($gNovels)
{
     foreach ($gNovels as $book) {
          echo "<tr>";
          echo "<td>" . $book['title'] . "</td>";
          echo "<td>" . $book['volume'] . "</td>";
          echo "<td>" . $book['year'] . "</td>";
          echo "<td>" . $book['publisher'] . "</td>";
          echo "</tr>";
     }
}

include_once 'header.inc';
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
          <a class="nav-link active" aria-current="page" href="graphicNovel.php">Graphic Novels<span class="visually-hidden">(current)</span></a>
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

</div><!-- /.navbar-collapse -->
</div><!-- /.container-fluid -->
</nav>

<br>

<main id="main-content">
     <div class="wrapper form-display">
          <h3 class="h6">
               Welcome <?= $_SESSION['name'] ?>
          </h3>
          <br>
          <form method="POST" name="gNovelForm" aria-label="Graphic Novel Search">
               <fieldset class="text-bg-light">
                    <legend class="bg-body-tertiary text-white p-1">Optional Search by Title, Publisher, or Sort</legend>
                    <div class="row gx-4 gy-3 align-items-center">

                         <div class="col-auto">
                              <div class="input-group">
                                   <label for="title" class="input-group-text">Title</label>
                                   <input type="text" name="title" id="title" placeholder="Enter Title Here" />
                              </div>
                         </div>

                         <div class="col-auto">
                              <div class="input-group">
                                   <label for="publisher" class="input-group-text">Publisher</label>
                                   <select name="publisher" id="publisher">
                                        <option value="" disabled selected>Select One</option>
                                        <?php
                                        $allPub = getDropDown('graphicNovel', 'publisher');
                                        //print_r($allPub);
                                        foreach ($allPub as $singlePub) {
                                             echo "<option>" . $singlePub['publisher'] . " </option>";
                                        }
                                        ?>
                                   </select>
                              </div>
                         </div>

                         <div class="col-auto">
                              <div class="input-group">
                                   <label for="sortBy" class="input-group-text">Sort By</label>
                                   <select name="sortBy" id="sortBy">
                                        <option value="" disabled selected>Select One</option>
                                        <option value="title ASC">Title</option>
                                        <option value="publisher ASC">Publisher</option>
                                        <option value="year ASC">Year: Low to High</option>
                                        <option value="year DESC">Year: High to Low</option>
                                   </select>
                              </div>
                         </div>
                    </div>

                    <div class="row py-2">
                         <div class="col-auto py-3">
                              <input type="submit" value="Search" name="filterForm" class="btn" />
                         </div>

                         <div class="col-auto py-3">
                              <input type="submit" value="All Graphic Novels" name="allIn" class="btn" /></span>
                         </div>
                    </div>

               </fieldset>
          </form>
     </div>

     <br><br>

     <div class="wrapper form-display mb-5">
          <table class="table table-sm table-striped table-hover display nowrap" id="novelDisplay" style="width:100%;" aria-labelledby="graphic-novel">
               <caption class="small bg-body-tertiary text-white p-2 my-2" id="graphic-novel"><strong>Graphic Novel Collection</strong> - The first row consist of four columns which are Title, Volume, Year, and Publisher. The first column has the titles listed in alphabetical order, and the number of books will vary based on the users input of search all, title or publisher, or by sorting. The user can sort by title, publisher, and year. Cross reference the title row with the column for the specific data. There may be more than one title based on volume, publisher, or year.</caption>
               <thead class='table-dark'>
                    <tr>
                         <th>Title</th>
                         <th>Volume</th>
                         <th>Year</th>
                         <th>Publisher</th>
                    </tr>
               </thead>
               <tbody>
                    <?php
                    if (isset($_POST['filterForm'])) {
                         $filterList = goSQLcomic("graphicNovel");
                         dataDisplay($filterList);
                    } else { // Display inventory initially.
                         $gNovels = getInfo("graphicNovel");
                         dataDisplay($gNovels);
                    }
                    ?>
               </tbody>
          </table>
     </div>

     <?php include_once 'footer.inc' ?>

     <script>
          /** https://datatables.net/examples/index **/
          new DataTable('#novelDisplay', {
               lengthMenu: [16, 8],
               searching: false,
               ordering: false,
               responsive: true,
               pagingType: 'simple',
               language: {
                    paginate: {
                         next: 'Next',
                         previous: 'Previous'
                    }
               },
               columnDefs: [{
                    targets: [0],
                    class: "wrapok"
               }]
          });

          /**  https://datatables.net/forums/discussion/71404/accessibility-pagination-using-actual-buttons-instead-of-links */
          const prevNextCollection = document.getElementsByClassName("page-link");
          prevNextCollection[0].setAttribute("role", "button");
          prevNextCollection[1].setAttribute("role", "button");
     </script>

     </body>

     </html>