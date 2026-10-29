(function(){
    setTimeout(function(){
        var num = document.querySelector('.form-row.field-cpf').querySelector('.readonly').innerHTML.toString().padStart(11,'0');
        document.querySelector('.form-row.field-cpf').querySelector('.readonly').innerHTML = `${num.substring(0,3)}.${num.substring(3,6)}.${num.substring(6,9)}-${num.substring(9,11)}`;        
    },1);    
})()