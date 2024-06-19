    <br>
    <a href="#toTop" class="btn back-to-top" id="back-to-top-link" title="Back to Top" aria-label="Back to Top"><img src="./img/star-trek.png" alt="star trek icon" title="back to top" /></a>
</main>

<footer>
    <div id='footer'>
        ©2016 to <?php echo date("Y"); ?> <a href="https://philemmons.com" class="text-white" target='_blank' rel="noopener noreferrer">philemmons.com<span class="sr-only">(Opens a new window)</span></a> All rights reserved.
    </div>
</footer>

<script>
    /** tooltip - https://www.tutorialrepublic.com/codelab.php?topic=bootstrap&file=tooltips-placement-via-javascript **/
    document.addEventListener("DOMContentLoaded", function() {
        // Placement of tooltip on top
        var tipTop = document.getElementById("tipTop");
        var tooltipTop = new bootstrap.Tooltip(tipTop, {
            placement: "top",
            animated: 'fade',
            placement: 'bottom',
            html: true
        });
    });
</script>

<script src="../js/backToTop.js"></script>