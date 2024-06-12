<br>

<a href="#toTop" class="btn back-to-top" id="back-to-top-link" title="Back to Top" aria-label="Back to Top"><img src="./img/star-trek.png" alt="star trek icon" title="back to top" /></a>

<footer>
    <div id='footer'>
        ©2016 - <?php echo date("Y"); ?> Phillip Emmons. All rights reserved.<a href="https://philemmons.com" target='_blank' id='sentence-case'>Contact Info</a>
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