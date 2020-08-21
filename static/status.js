let statusnodelist = document.querySelectorAll(".statustext");
let statusArr = Array.prototype.slice.call(statusnodelist);
let shareForm = document.getElementById("shareable");
let shareSubmit = document.getElementById("addshare");
let shareBtn = document.getElementById("share");
let manageBtn = document.getElementById("manageshared");
let dim = document.getElementById("dim");
let manageDisp = document.getElementById("shared-disp");

shareForm.style.display = "none";
manageDisp.style.display = "none";

function main(){
    for(i = 0; i < statusArr.length; i++){
        if (statusArr[i].textContent == "Status: 0"){
            statusArr[i].textContent = "Status: Not Started";
        }
        if (statusArr[i].textContent == "Status: 1"){
            statusArr[i].textContent = "Status: In Progress";
        }
        if (statusArr[i].textContent == "Status: 2"){
            statusArr[i].textContent = "Status: Done";
        }
    }
    shareBtn.addEventListener("click", ()=>{
        if(shareForm.style.display == "block"){
            shareForm.style.display = "none";
        }
        else{
            shareForm.style.display = "block";
        }
    })
    manageBtn.addEventListener("click", ()=>{
        manageDisp.style.display = "block";
        dim.style.display = "block";
    })
    dim.addEventListener("click", ()=>{
        manageDisp.style.display = "none";
    })
}

window.onload = main();