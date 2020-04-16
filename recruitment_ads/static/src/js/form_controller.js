odoo.define('recruitment_ads.FormController', function (require) {
"use strict";

var BasicController = require('web.BasicController');
var dialogs = require('web.view_dialogs');
var core = require('web.core');
var Dialog = require('web.Dialog');
var Sidebar = require('web.Sidebar');
var _t = core._t;
var qweb = core.qweb;
var FormController = require('web.FormController');
var Session = require('web.session');
FormController.include({

    _onEdit: function () {
        var data = this.renderer.state.data;
        this.getSession().user_has_group('hr_recruitment.group_hr_recruitment_manager').then(function(has_group) {
            if(has_group) {
             window.manager =  true;
            }
         });
        if (data.user_id != false && data.user_id.data.id !== Session.uid && window.manager !== true){
             alert('This Application is Owned by another Recruiter , you are not allowed to take any on.');
        }else{this._super.apply(this, arguments);}
}
});
});