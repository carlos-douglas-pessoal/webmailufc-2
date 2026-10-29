// VueSpinner
import {
    MoonLoader
} from 'vue-spinner/dist/vue-spinner.min.js'
import axios from 'axios';
import {
    required,
    minLength,
    between
} from 'vuelidate/lib/validators';

const changePasswordModal = {
    data() {
        return {
            isLoading: false,
            password: null
        }
    },
    methods: {
        confirm() {
            var that = this;
            this.isLoading = true;
            axios.post('/requests/', {
                method: 'update-password',
                password: this.password,
                email: this.$parent.props.email
            }, {
                headers: {
                    'X-CSRFToken': document.querySelector('input[name=csrfmiddlewaretoken]').value
                }
            }).then(function (response) {
                that.isLoading = false;
                that.password = null;
                that.$parent.close();
                that.$buefy.toast.open('A senha foi alterada!');
            }).catch(function (err) {
                that.isLoading = false;
                that.$parent.close();
                that.password = null;
                that.$buefy.toast.open('Não foi possível alterar a senha');
            })
        }
    },
    template: /*html*/`
        <div class="modal-card" style="width: auto">
            <header class="modal-card-head">
                <p class="modal-card-title">Alterar senha</p>
            </header>
        <section class="modal-card-body">
            <b-field label="Nova senha">
                <ValidationProvider ref="provider" :rules="{required:true}">
                    <b-input type="password" name="senha" v-model="password" password-reveal placeholder="Nova Senha de 8 dígitos"></b-input>                    
                </ValidationProvider>
            </b-field>
        </section>
        <footer class="modal-card-foot">
            <button class="button" type="button" @click="$parent.close()">Close</button>
            <button :class="['button is-primary',isLoading ? 'is-loading' : null]" :disabled="isLoading || (!password || password.length < 8)"  @click="confirm()">Confirmar</button>
        </footer>
        </div>`
}

const modal = {
    props: ['parentForm', 'emailRegex','phoneOptionsTranslation'],
    data: function () {
        return {
            isLoading: false,
            nome_: this.parentForm.nome,
            sobrenome_: this.parentForm.sobrenome,
            email_alternativo_: this.parentForm.email_alternativo,
            telefone_: this.parentForm.telefone,
            telephone: null,
            lang: {
                language: 'br'
            }
        }
    },
    created() {

    },
    methods: {
        save: function () {
            var that = this;
            this.isLoading = true;
            axios.post('/requests/', {
                method: 'update-personal-data',
                email: this.parentForm.email,
                name: this.nome_,
                familyName: this.sobrenome_,
                recoveryEmail: this.email_alternativo_,
                telephone: {
                    number: this.telephone.e164 || this.telephone.phoneNumber,
                    ise164: this.telephone.e164 != null,
                    countryCode: this.telephone.countryCallingCode
                }
            }, {
                headers: {
                    'X-CSRFToken': document.querySelector('input[name=csrfmiddlewaretoken]').value
                }
            }).then(function (success) {
                if (success.status == 200){
                    that.$parent.props.parentForm.nome = that.nome_
                    that.$parent.props.parentForm.sobrenome = that.sobrenome_;
                    that.$parent.props.parentForm.email_alternativo = that.email_alternativo_;
                    that.$parent.props.parentForm.telefone = that.telephone.e164 || (that.telephone.countryCallingCode + that.telephone.phoneNumber)
                    that.isLoading = false;
                    that.$parent.close();
                    that.$buefy.toast.open('Dados pessoais salvos!');
                    that.$parent.props.changeNameAvatar();
                }else{
                    throw "";
                }                
            }).catch(function (err) { false;
                that.$parent.close();
                that.$buefy.toast.open('Não foi possível salvar os dados pessoais');
            });

        }
    },
    template: /*html*/ `
        <div class="modal-card" style="overflow: visible !important">
            <header class="modal-card-head">
                <p class="modal-card-title">Alterar dados pessoais</p>
            </header>
            <ValidationObserver ref="formularioDadosPessoais" v-slot="{ invalid, handleSubmit }">         
            <section class="modal-card-body" style="overflow: visible !important">
                <ValidationProvider name="Nome" rules="required" v-slot="validation" immediate>
                    <div class="field">
                        <label class="label">Nome</label>
                        <div class="control">
                            <input :class="['input', (!validation.changed && !validation.passed) || !validation.dirty  ? '' : (!validation.valid) ? 'is-danger' : 'is-success' ]" type="text" placeholder="Seu nome" v-model="nome_">
                            <p class="help is-danger" v-if="validation.errors.length > 0">{{validation.errors[0]}}</p>
                        </div>
                    </div>
                </ValidationProvider>
                <ValidationProvider name="Sobrenome" rules="required" v-slot="validation" immediate>
                    <div class="field">
                        <label class="label">Sobrenome</label>
                        <div class="control">
                            <input :class="['input', (!validation.changed && !validation.passed) || !validation.dirty  ? '' : (!validation.valid) ? 'is-danger' : 'is-success' ]" type="text" placeholder="Seu sobrenome" v-model="sobrenome_">
                            <p class="help is-danger" v-if="validation.errors.length > 0">{{validation.errors[0]}}</p>
                        </div>
                    </div>
                </ValidationProvider>
                <ValidationProvider name="E-mail alternativo" rules="required|email" v-slot="validation" immediate>
                    <div class="field">
                        <label class="label">E-mail Alternativo</label>
                        <div class="control">
                            <input :class="['input', (!validation.changed && !validation.passed) || !validation.dirty  ? '' : (!validation.valid) ? 'is-danger' : 'is-success' ]" type="email" placeholder="Seu email de recuperação de conta" v-model="email_alternativo_">
                            <p class="help is-danger" v-if="validation.errors.length > 0">{{validation.errors[0]}}</p>
                        </div>
                    </div>
                </ValidationProvider>
                <div class="field">
                    <label class="label">Telefone de recuperação da conta</label>
                    <div class="control">
                    <MazPhoneNumberInput v-model="telefone_" @update="telephone = $event" :translations="phoneOptionsTranslation" />
                        <p class="help is-danger" v-if="telephone && !telephone.e164">Telefone não está no formato correto!</p>
                    </div>
                </div>                          
            </section>
            <footer class="modal-card-foot">
                <button class="button" type="button" @click="$parent.close()">Fechar</button>                
                <button :class="['button is-primary',isLoading ? 'is-loading' : null]" @click.prevent.self="handleSubmit(save)" :disabled="invalid">Atualizar</button>
            </footer>
            </ValidationObserver>            
        </div>
        `
};

const redefineViewMixin = {
    data: function () {
        return {
            account: null,
            accounts: [],
            senha: null,
            userPhoto:null
        }
    },
    validations: {
        name: {
            required,
            minLength: minLength(4)
        },
        age: {
            between: between(20, 30)
        }
    },
    methods: {
        whenChange(o) {
            if (!o || o.email.length == 0) {
                return;
            }
            if (document.querySelector('img[id="img-user-preview"]')) {
                document.querySelector('img[id="img-user-preview"]').remove();
            }

            this.$refs.dados_.photoLoaded = false;
            this.$refs.dados_.getPhoto(o.email)
        },
        cardModal() {
            var that = this;
            this.$buefy.modal.open({
                parent: that,
                component: modal,
                hasModalCard: true,
                canCancel: false,
                trapFocus: true,
                props: {
                    emailRegex:  this.emailRegex,
                    phoneOptionsTranslation: this.phoneOptionsTranslation,
                    parentForm: this.account,
                    changeNameAvatar: this.$refs.dados_.changeNameAvatar
                }
            });
        },
        changePassword(){
            this.$buefy.modal.open({
                parent: this,
                component: changePasswordModal,
                hasModalCard: true,
                canCancel: false,
                trapFocus: true,
                props: {
                    email: this.account.email
                }
            })
        }
    },
    created(){
        setTimeout(()=>{
            var element = document.querySelector(".upload-draggable.is-primary");
            if (!element){ return }
            element.style.borderRadius = '290486px';
            element.style.padding = '0.1em';
            console.log(element)
        },50);
    }
}


var dadosComponent = {
    props: ['contas', 'nome', 'cpf'],
    data: function () {
        return {
            photoLoaded: false,
        }
    },
    template: /*html*/ `
        <div class="columns is-vcentered is-centered">
            <div class="column is-3 is-hidden-mobile" style="display:flex;justify-content:center">
                <p id="user-preview" class="content image is-64x64">
                    <moon-loader :loading="!photoLoaded" style="line-height:0"></moon-loader>
                </p>
            </div>
            <div class="column is-mobiled-aligned-center">
                <h5 class="title is-6" style="margin-bottom:0px">
                    {{ ($parent.account.nome && $parent.account.sobrenome) ? $parent.account.nome + ' ' + $parent.account.sobrenome : nome }}
                </h5>
                <h6 class="has-text-grey-dark">{{ cpf }}</h6>
                <h6 v-if="$parent.accounts.length == 1" class="label has-text-grey-dark">{{ $parent.account.email }}</h6>
            </div>
        </div>       
    `,
    components: {
        MoonLoader
    },
    created() {
        this.$parent.accounts = JSON.parse(this.contas);
        this.$parent.account = this.$parent.accounts[0];
        this.getPhoto(this.$parent.account.email);
    },
    methods: {        
        userChangedPhoto(value){
            var that = this;
            var fr = new FileReader();
            fr.onload = function(){
                axios.post('/requests/', {
                    method: 'update-photo',
                    photo: fr.result,
                    email: that.$parent.account.email
                }, {
                    headers: {
                        'X-CSRFToken': document.querySelector('input[name=csrfmiddlewaretoken]').value
                    }
                }).then(function (response) {
                    that.isLoading = false;
                    that.$buefy.toast.open('Sua foto no gmail foi alterada!');
                }).catch(function (err) {
                    that.isLoading = false;
                    that.$buefy.toast.open('Não foi possível alterar sua foto');
                })

                // var im = new Image();
                // im.src = fr.result;
                // im.className = 'is-rounded';
                // im.id = 'img-user-preview';
                // im.style.width = '96px';
                // im.style.height = '96px';
                // if (document.querySelector('img[id="img-user-preview"]')) {
                //     document.querySelector('img[id="img-user-preview"]').remove();
                // }
                // document.querySelector('p[id="user-preview"]').appendChild(im);
            };
            fr.readAsDataURL(value)
        },
        changeNameAvatar(img) {
            if (!img) {
                img = document.querySelector('img[id="img-user-preview"]');
            }
            img.src = `https://ui-avatars.com/api/?background=0D8ABC&color=fff&name=${this.$parent.account.nome ? (this.$parent.account.nome + '+' + this.$parent.account.sobrenome) : this.nome}`;
        },
        getPhoto(email) {
            var that = this;
            var im = new Image();
            im.className = 'is-rounded';
            im.id = 'img-user-preview';
            axios.get(`/requests/?email=${email}&method=get-photo`).then(function (response) {
                if (response.data && Object.keys(response.data).length > 0) {
                    that.photoLoaded = true;
                    var image = response.data.photoData;
                    var zq = /_/g;
                    var hq = /-/g;
                    var ef = /\*/g;
                    image = image.replace(zq, "/").replace(hq, '+').replace(ef, '=');
                    im.src = `data:image/jpeg;base64,${image}`;
                    if (document.querySelector('img[id="img-user-preview"]')) {
                        document.querySelector('img[id="img-user-preview"]').remove();
                    }
                    document.querySelector('p[id="user-preview"]').appendChild(im);
                } else {
                    throw "";
                }
            }).catch(function (err) {
                that.photoLoaded = true;
                that.changeNameAvatar(im);
                if (document.querySelector('img[id="img-user-preview"]')) {
                    document.querySelector('img[id="img-user-preview"]').remove();
                }
                document.querySelector('p[id="user-preview"]').appendChild(im);
            });
        }
    }
};



module.exports = {
    'dadosComponent': dadosComponent,
    'redefineViewMixin': redefineViewMixin
}