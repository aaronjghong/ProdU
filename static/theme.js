// Detects if the theme change button has been presssed
// If pressed, submit the theme change form

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