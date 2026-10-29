var axios = require('axios');
var VueSelect = require('vue-select');
// var VueSpinner = require('vue-spinner');
// Vue.component('v-select', VueSelect.VueSelect);
// Vue.component('moon-loader', VueSpinner.MoonLoader);  
const modal = {
    data() {
        return {
            isLoading: false,
            form: {
                nome: this.$parent.props.parentForm.nome,
                sobrenome: this.$parent.props.parentForm.sobrenome,
                email_alternativo: this.$parent.props.parentForm.email_alternativo
            }
        }
    },
    methods: {
        save: function () {
            var that = this;
            this.isLoading = true;
            axios.post('/requests/', {
                method: 'update-personal-data',
                email: this.$parent.props.parentForm.email,
                name: this.form.nome,
                familyName: this.form.sobrenome,
                recoveryEmail: this.form.email_alternativo
            }, {
                headers: {
                    'X-CSRFToken': document.querySelector('input[name=csrfmiddlewaretoken]').value
                }
            }).then(function (success) {
                that.$parent.props.parentForm.nome = that.form.nome
                that.$parent.props.parentForm.sobrenome = that.form.sobrenome;
                that.$parent.props.parentForm.email_alternativo = that.form.email_alternativo;
                that.isLoading = false;
                that.$parent.close();
                that.$buefy.toast.open('Dados pessoais salvos!');
                that.$parent.props.changeNameAvatar();                
            }).catch(function (err) {
                that.isLoading = false;
                that.$parent.close();
                that.$buefy.toast.open('Não foi possível salvar os dados pessoais');
            });

        }
    },
    template: `
    <validation-observer ref="observer" v-slot="v">
        <div class="modal-card">
            <header class="modal-card-head">
                <p class="modal-card-title">Alterar dados pessoais</p>
            </header>
            <section class="modal-card-body">
                <div class="field is-horizontal">
                    <div class="field-label is-normal">
                        <label class="label" style="text-align:left">Nome</label>
                    </div> 
                    <div class="field-body">
                        <div class="field">
                            <div class="control">
                                <validation-provider ref="provider" :rules="{required:true}" v-slot="errors" immediate>
                                    <input :class="['input',errors.flags.untouched && form.nome ? '' : errors.flags.valid ? 'is-success' : 'is-danger']" type="text" v-model="form.nome">
                                </validation-provider>
                            </div>
                        </div>
                    </div>                       
                </div>
                <div class="field is-horizontal">
                    <div class="field-label is-normal">
                        <label class="label" style="text-align:left">Sobrenome</label>
                    </div> 
                    <div class="field-body">
                        <div class="field">
                            <div class="control">
                                <validation-provider ref="provider" :rules="{required:true}" v-slot="errors" immediate>
                                    <input :class="['input',errors.flags.untouched && form.sobrenome  ? '' : errors.flags.valid ? 'is-success' : 'is-danger']" type="text" v-model="form.sobrenome">
                                </validation-provider>
                            </div>
                        </div>
                    </div>                       
                </div>
                <div class="field is-horizontal">
                    <div class="field-label is-normal">
                        <label class="label" style="text-align:left">Email Alternativo</label>
                    </div> 
                    <div class="field-body">
                        <div class="field">
                            <div class="control">
                                <validation-provider ref="provider" :rules="{required:true,email:true}" v-slot="errors" immediate>
                                    <input :class="['input',errors.flags.untouched && form.email_alternativo ? '' : errors.flags.valid ? 'is-success' : 'is-danger']" type="email" v-model="form.email_alternativo">
                                </validation-provider>
                            </div>
                        </div>
                    </div>                       
                </div>             
            </section>
            <footer class="modal-card-foot">
                <button class="button" type="button" @click="$parent.close()">Fechar</button>                
                <button :class="['button is-primary',isLoading ? 'is-loading' : null]" @click="save()" :disabled="!v.valid || !v.dirty" >Salvar</button>
            </footer>
        </div>
        </validation-observer>        
        `
};

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
    template: `
        <div class="modal-card" style="width: auto">
            <header class="modal-card-head">
                <p class="modal-card-title">Alterar senha</p>
            </header>
        <section class="modal-card-body">
            <b-field label="Nova senha">
                <validation-provider ref="provider" :rules="{required:true}">
                    <b-input type="password" name="senha" v-model="password" password-reveal placeholder="Nova Senha de 8 dígitos"></b-input> 
                </validation-provider>               
            </b-field>
        </section>
        <footer class="modal-card-foot">
            <button class="button" type="button" @click="$parent.close()">Close</button>
            <button :class="['button is-primary',isLoading ? 'is-loading' : null]" :disabled="isLoading || (!password || password.length < 8)"  @click="confirm()">Confirmar</button>
        </footer>
        </div>    `
}


export default {
    name: 'redefine-view',
    props: {
        contas: null,
        fullnome: null
    },
    created() {
        this.accs = JSON.parse(this.contas);
        this.account = JSON.parse(this.contas)[0];
        this.getPhoto(this.account.email);
    },
    data: function () {
        return {
            accs: null,
            account: null,
            photoLoaded: false            
        }        
    },
    methods: {
        myChange(o){    
            if(!o || o.email.length == 0){
                return;
            }        
            if(document.querySelector('img[id="img-user-preview"]')){
                document.querySelector('img[id="img-user-preview"]').remove();                
            }
            this.photoLoaded = false;
            this.getPhoto(o.email)
        },
        cardModal(obj) {
            var that = this;

            this.$buefy.modal.open({
                parent: this,
                component: modal,
                hasModalCard: true,
                canCancel: false,
                trapFocus: true,
                props: {
                    parentForm: this.account,
                    changeNameAvatar: this.changeNameAvatar
                }
            })
        },
        changePassword() {
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
        },
        changeNameAvatar(img){
            if(!img){
                img = document.querySelector('img[id="img-user-preview"]');
            }
            img.src = `https://ui-avatars.com/api/?background=0D8ABC&color=fff&name=${this.account.nome ? (this.account.nome + '+' + this.account.sobrenome) : this.fullnome}`;
        },
        getPhoto(email) {
            var that = this;            
            var im = new Image();
            im.className = 'is-rounded';
            im.id = 'img-user-preview';            
            axios.get(`/requests/?email=${email}&method=get-photo`).then(function (response) {
                if (response.data) {
                    that.photoLoaded = true;
                    var image = response.data.photoData;
                    var zq = /_/g;
                    var hq = /-/g;
                    var ef = /\*/g;
                    image = image.replace(zq, "/").replace(hq,'+').replace(ef,'=');  
                    im.src = `data:image/jpeg;base64,${image}`;
                    if(document.querySelector('img[id="img-user-preview"]')){
                        document.querySelector('img[id="img-user-preview"]').remove();                
                    }
                    document.querySelector('p[id="user-preview"]').appendChild(im);
                }
            }).catch(function(err){
                that.photoLoaded = true;
                that.changeNameAvatar(im);
                if(document.querySelector('img[id="img-user-preview"]')){
                    document.querySelector('img[id="img-user-preview"]').remove();                
                }            
                document.querySelector('p[id="user-preview"]').appendChild(im);
            });
        }
    }
}