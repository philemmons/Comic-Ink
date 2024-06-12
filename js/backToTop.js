/*
source: https://github.com/mdbootstrap/bootstrap-back-to-top-button
*/

//Get the button
let bttLink = document.getElementById("back-to-top-link");

// When the user scrolls down 20px from the top of the document, show the button
window.onscroll = function () {
    scrollFunction();
};

function scrollFunction() {
    if (
        document.body.scrollTop > 20 ||
        document.documentElement.scrollTop > 20
    ) {
        bttLink.style.opacity = "1";
    } else {
        bttLink.style.opacity = "0";
    }
}
// When the user clicks on the button, scroll to the top of the document
bttLink.addEventListener("click", backToTop);

function backToTop() {
    document.body.scrollTop = 0;
    document.documentElement.scrollTop = 0;
}