export default {
    name: 'signup-view',
    data(){
        return {
            nome_usuario: null,
            email_alternativo: null,
            nome: null,
            sobrenome: null,
            telProps: {
                name: 'telefone_recuperacao',
                defaultCountry: 'BR',
                inputClasses: 'input',
                placeholder: 'Forneça um telefone de recuperação',
                inputOptions: {
                    showDialCode:true
                },
                validCharactersOnly: true
            }
        }
    },
    methods: {
        checkForm(e){
            return true;
        },
    }
}