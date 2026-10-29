const SignUpViewMixin = {
    data(){
        return {
            nome_usuario: null,
            email_alternativo: null,
            nome: null,
            sobrenome: null,
            telefone: null
        }
    },
    methods: {
        checkForm: function(){
            document.getElementById('form_').submit();
            return true;
        }
    },
    components: {

    },
    created(){

    }
}

module.exports = {
    'signupViewMixin': SignUpViewMixin
};