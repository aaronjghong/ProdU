// Handles the opening and closing of the comment section

let commentButton = document.getElementById("comment-button");
let commentDisplay = document.getElementById("comment-disp")
let closeBtn = document.getElementById("close-comments");

window.onload = ()=>{
    commentButton.addEventListener("click", ()=>{
        commentButton.style.display = "none";
        commentDisplay.style.display = "flex";
    })
    closeBtn.addEventListener("click", ()=>{
        commentDisplay.style.display = "none";
        commentButton.style.display = "block";
    })
};