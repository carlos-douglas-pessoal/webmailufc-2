
//Vue
import myVue  from 'myvue';
window.Vue = myVue;
import 'vue-phone-number-input/dist/vue-phone-number-input.css';
// Buefy
import { Input, Button, Field, Loading, Modal, Toast, Icon, Notification, Upload } from 'buefy';
import '../css/styles.css';
import '../css/site.css';
// import 'buefy/dist/buefy.css';
// vue-select
import vSelect, { VueSelect } from 'vue-select'



import { ValidationProvider, ValidationObserver, extend } from 'vee-validate';
import { required, email, regex } from 'vee-validate/dist/rules.umd';

import { dadosComponent, redefineViewMixin } from './redefine.mixin';
import { signupViewMixin } from './signup.mixin';

// phone number input
import { MazPhoneNumberInput } from 'maz-ui';
import "maz-ui/lib/css/base.css";
import 'maz-ui/lib/css/maz-phone-number-input.css';


myVue.directive('init', {
    bind: function (el, binding, vnode) {
        vnode.context[binding.arg] = binding.value;
    }
});

extend('email',{
    ...email,
    message: 'E-mail inválido'
});
extend('required',{
    ...required,
    message: 'Este campo é obrigatório!'
});
extend('regex',{
    ...regex,
    message: message => `${message} não está no formato válido!`
});
extend('emailregex',{
    validate: (value) => {
        debugger
        console.log(email(value))
    }
})

myVue.use(Input);
myVue.use(Button);
myVue.use(Field);
myVue.use(Loading);
myVue.use(Modal);
myVue.use(Toast);
myVue.use(Icon);
myVue.use(Notification);
myVue.use(Upload);

myVue.component('v-select',vSelect);
myVue.component('dados',dadosComponent);
myVue.component(MazPhoneNumberInput.name,MazPhoneNumberInput);
myVue.component('ValidationProvider', ValidationProvider);
myVue.component('ValidationObserver', ValidationObserver);

new myVue({
    el: '#app',
    delimiters: ["<%", "%>"],
    mixins: [redefineViewMixin, signupViewMixin],
    data(){
        return {
            emailRegex: /^([a-z]{7,}|[a-z]{3,}(\.[a-z]{3,}|\.?[a-z]{2,}[0-9]{2}([a-z]{2,})?|[0-9]{2}([a-z]{3,})|[0-9]{4}([a-z]{2,})|\.?[a-z]{2,}[0-9]{4}([a-z]{2,})?|\.?[0-9]{4}))$/,
            phoneOptionsTranslation: {
                countrySelectorLabel: 'País',
                countrySelectorError: 'Escolha inválida',
                phoneNumberLabel: 'Telefone de recuperação',
                example: 'Exemplo :'
            },
            isloading: false
        }
    },
    methods: {
        back() {
            window.history.back()
        },
        showLoading() {
            const loadingComponent = this.$buefy.loading.open({
                container: null
            });
            setTimeout(()=> {
                loadingComponent.close();
                alert('O servidor demorou a responder')
            },120000);
        }
    },
    created() {
        window.addEventListener('beforeunload', this.showLoading);
    }
})