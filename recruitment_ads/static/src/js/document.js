odoo.define('recruitment_ads.document.document', function (require){
"use strict";

var core = require('web.core');
var Dialog = require('web.Dialog');
var framework = require('web.framework');
var Sidebar = require('web.Sidebar');
var field_utils = require('web.field_utils');
var Document = require('document.document');

var _t = core._t;
//Document.include({
Sidebar.include({
     init : function (parent, options) {
       this._super.apply(this, arguments);
        var value_without_attach_button = this.sections;
        if (options.viewType === "form") {
        if (this.env.model === 'hr.applicant'){
//            this.sections.splice(1, 0, { 'name' : 'files', 'label' : _t('Attachment(s)'), });
            for(var i in this.sections){
                if(this.sections[i]['label']=="Attachment(s)"){
                   this.sections.splice(i,1);
                    break;
            }
        }
        }
        }

    },
});







});