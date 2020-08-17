button = document.getElementById("addplan");
body = document.body;
form = document.getElementById("center");
display = document.getElementById("disp");
addbtn = document.getElementById("add");
dim = document.getElementById("dim");

// Get preexisting form and set visible to none

function main(){
    form.style.display = "none";
    form.style.zIndex = 99;
    dim.style.display = "none";
    button.addEventListener("click", ()=>{
        form.style.display = "block";
        // display.style.display = "none";
        dim.style.display = "block";
    })
    addbtn.addEventListener("click", ()=>{
        form.style.display = "none";
        // display.style.display = "block";
        dim.style.display = "none";
    })
    dim.addEventListener("click", ()=>{
        form.style.display = "none";
        // display.style.display = "block";
        dim.style.display = "none";
    })
}

window.onload = main();