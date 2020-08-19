let statusnodelist = document.querySelectorAll(".statustext");
let statusArr = Array.prototype.slice.call(statusnodelist);
let shareForm = document.getElementById("shareable");
let shareSubmit = document.getElementById("addshare");
let shareBtn = document.getElementById("share");

shareForm.style.display = "none";

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
}

window.onload = main();