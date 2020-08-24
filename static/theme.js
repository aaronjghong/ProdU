let themeBtn = document.getElementById("theme-button");
let themeForm = document.getElementById("themechange")

console.log("window")
themeBtn.addEventListener("click", ()=>{
    console.log("clicked")
    setTimeout(()=>{
        console.log("time");
        themeForm.submit();
    },1000)
})