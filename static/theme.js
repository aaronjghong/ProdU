let themeBtn = document.getElementById("theme-button");

console.log("window")
themeBtn.addEventListener("click", ()=>{
    console.log("clicked")
    setTimeout(()=>{
        console.log("time")
        location.reload();
    },10)
})