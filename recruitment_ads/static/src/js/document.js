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
//     console.log(this.env);
       this._super.apply(this, arguments);
       console.log(this.env.model);
        if (options.viewType === "form") {
        if (this.env.model === 'hr.applicant'){
            this.sections = []
        }
        }

    },
});







});