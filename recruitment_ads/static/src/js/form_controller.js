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
        console.log(this);
        if(this.modelName === 'hr.applicant'){
            var data = this.renderer.state.data;
            this.getSession().user_has_group('hr_recruitment.group_hr_recruitment_manager').then(function(has_group) {
                if(has_group) {
                 window.manager =  true;
                }
             });
            if (data.user_id != false && data.user_id.data.id !== Session.uid && window.manager !== true){
                 alert('This Application is Owned by another Recruiter , you are not allowed to take any action on.');
            }else{this._super.apply(this, arguments);}}
        else{this._super.apply(this, arguments);}
},
	 _onSave: function (ev) {
        var self = this;
        var record = this.model.get(this.handle, {raw: true});
        if (record.model ==='hr.applicant'){
            this._rpc({
                model: 'hr.applicant',
                method: 'check_application_duplication',
                args: [[record.data.id]],
            }).then(function (res) {
             if (res){
             return self.do_action({
                    name: ("Merge Selected Contacts"),
                    type: 'ir.actions.act_window',
                    res_model: 'base.partner.merge.automatic.wizard',
                    view_mode: 'form',
                    view_type: 'form',
                    views: [[false, 'form'],[false, 'list'],[false, 'kanban']],
                    target: 'new',
                    context:  {'state': 'selection',
                        'active_model':'hr.applicant',
                        'dst_partner_id': record.data.partner_id,
                        'partner_ids': res,
                        'group_by_is_company': false,
                        'maximum_group': 0,
                        'group_by_parent_id': false,
                        'exclude_contact': false,
                        'group_by_email': false,
                        'exclude_journal_item': false,
                        'display_name': '',
                        'number_group': 0,
                        'group_by_vat': false,
                        },
                })
             }
            })
        }

        if (record.model ==='res.partner'){
            console.log(record.data)
            debugger;
            this._rpc({
                model: 'res.partner',
                method: 'check_contact_duplication',
                args: [[record.data.id]],
            }).then(function (res) {
             if (res){
             return self.do_action({
                    name: ("Merge Selected Contacts"),
                    type: 'ir.actions.act_window',
                    res_model: 'base.partner.merge.automatic.wizard',
                    view_mode: 'form',
                    view_type: 'form',
                    views: [[false, 'form'],[false, 'list'],[false, 'kanban']],
                    target: 'new',
                    context:  {'state': 'selection',
                        'active_model':'hr.applicant',
                        'dst_partner_id': record.data.id,
                        'partner_ids': res,
                        'group_by_is_company': false,
                        'maximum_group': 0,
                        'group_by_parent_id': false,
                        'exclude_contact': false,
                        'group_by_email': false,
                        'exclude_journal_item': false,
                        'display_name': '',
                        'number_group': 0,
                        'group_by_vat': false,
                        },
                })
             }
            })
        }

        return this._super.apply(this, arguments);
        ev.stopPropagation(); // Prevent x2m lines to be auto-saved
//        this.saveRecord();
    }
});
});
