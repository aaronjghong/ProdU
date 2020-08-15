let alert = document.querySelector(".alert");
let body = document.body;

function main(){

    // Makes the alert fade away if it is an element in the DOM
    if (alert === null){
        return;
    }
    let op = 1;
    let i = 0
    let timer = setInterval(function(){
        
        // Timer for how long the alert should stay on screen at full opacity
        i++
        if (i >= 90){
            clearInterval(timer);
            i = 0;
            let timer2 = setInterval(function(){

                // Timer to decrease the opacity once the first timer had gone
                if (op <= 0.1){
                    clearInterval(timer2);
                    op = 0;
                    body.removeChild(alert)
                }
                alert.style.opacity = op;
                alert.style.filter = 'alpha(opacity=' + op * 100 + ")";
                op -= op * 0.1
            }, 25)
        }
    }, 100)
}

window.onload = main();