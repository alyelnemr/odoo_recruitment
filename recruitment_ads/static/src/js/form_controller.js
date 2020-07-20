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
        if(this.modelName === 'hr.applicant'){
            var data = this.renderer.state.data;
            this.getSession().user_has_group('hr_recruitment.group_hr_recruitment_manager').then(function(has_group) {
                if(has_group) {
                 window.manager =  true;
                }
             });
            if (data.user_id != false && data.user_id.data.id !== Session.uid && window.manager !== true){
                 alert('This Application is Owned by another Recruiter , you are not allowed to take any on.');
            }else{this._super.apply(this, arguments);}}
        else{this._super.apply(this, arguments);}
},
	_onSave: function (ev) {

	    var self = this;
        var record = self.model.get(self.handle, {raw: true});
        if (record.model ==='hr.applicant'){
            if (typeof(record.data.id) == 'undefined'){
                // New Applicant
                self.saveRecord(self.handle, {
    //                stayInEdit: true,
    //                reload: false,
    //                savePoint: self.shouldSaveLocally,
    //                viewType: 'form',
                 }).then(function (changedFields) {
                    // record might have been changed by the save (e.g. if this was a new record, it has an
                    // id now), so don't re-use the copy obtained before the save
                    var record = self.model.get(self.handle);
                    self._rpc({
                        model: self.modelName,
                        method: 'check_application_duplication',
                        args: [[record.data.id]],
                    }).then(function (res) {
                        if (res){
                            return self.do_action({
                            name: ("This Contact would be duplicated."),
                            type: 'ir.actions.act_window',
                            res_model: 'base.partner.merge.automatic.wizard',
                            view_mode: 'form',
                            view_type: 'form',
                            views: [[false, 'form'],[false, 'list'],[false, 'kanban']],
                            target: 'new',
                            context:  {
                                'state': 'selection',
                                'active_model': self.modelName,
//                                'dst_partner_id': record.data.partner_id.data.id,
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
                                'new_contact': true,
                                'edit_contact': false,
                                'form_dialog': false,
                                'create_applicant': record.data.id,
                                'edit_applicant': false,
                            },
                        });
                        }else{
                            return changedFields
                        }
                    });
                });
            }
            else{
                self.saveRecord(self.handle, {
    //                stayInEdit: true,
    //                reload: false,
    //                savePoint: self.shouldSaveLocally,
    //                viewType: 'form',
                 }).then(function (changedFields) {
                    var record = self.model.get(self.handle);
                    self._rpc({
                        model: self.modelName,
                        method: 'check_application_duplication',
                        args: [[record.data.id]],
                    }).then(function (res) {
                         if (res){
                            return self.do_action({
                                name: ("This Contact would be duplicated."),
                                type: 'ir.actions.act_window',
                                res_model: 'base.partner.merge.automatic.wizard',
                                view_mode: 'form',
                                view_type: 'form',
                                views: [[false, 'form'],[false, 'list'],[false, 'kanban']],
                                target: 'new',
                                context:  {
                                    'state': 'selection',
                                    'active_model':self.modelName,
    //                                'dst_partner_id': record.data.partner_id,
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
                                    'new_contact': false,
                                    'form_dialog': false,
                                    'edit_contact': false,
                                    'create_applicant': false,
                                    'edit_applicant': record.data.id,
                                },
                            })
                         }else{
                            return changedFields
                        }
                    });
                });
            }
        }
        else if (record.model ==='res.partner'){

            if (typeof(record.data.id) == 'undefined'){
                // New Partner
                self.saveRecord(self.handle, {
    //                stayInEdit: true,
    //                reload: false,
    //                savePoint: self.shouldSaveLocally,
    //                viewType: 'form',
                 }).then(function (changedFields) {
                    // record might have been changed by the save (e.g. if this was a new record, it has an
                    // id now), so don't re-use the copy obtained before the save
                    var record = self.model.get(self.handle);
                    self._rpc({
                        model: self.modelName,
                        method: 'check_contact_duplication',
                        args: [[record.data.id]],
        //                    kwargs: { vals: record.data }
                    }).then(function (res) {
                        if (res){
                            return self.do_action({
                            name: ("This Contact would be duplicated."),
                            type: 'ir.actions.act_window',
                            res_model: 'base.partner.merge.automatic.wizard',
                            view_mode: 'form',
                            view_type: 'form',
                            views: [[false, 'form'],[false, 'list'],[false, 'kanban']],
                            target: 'new',
                            context:  {
                                'state': 'selection',
                                'active_model': self.modelName,
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
                                'new_contact': true,
                                'edit_contact': false,
                                'form_dialog': false,
                            },
                        });
                        }else{
                            return changedFields
                        }
                    });
                });
            }
            else{
                // Edit Contact
                self.saveRecord(self.handle, {
//                    stayInEdit: true,
//                    reload: false,
//                    savePoint: self.shouldSaveLocally,
//                    viewType: 'form',
                }).then(function (changedFields) {
                    // record might have been changed by the save (e.g. if this was a new record, it has an
                    // id now), so don't re-use the copy obtained before the save
                    var record = self.model.get(self.handle);
                    self._rpc({
                        model: self.modelName,
                        method: 'check_contact_duplication',
                        args: [[record.data.id]],
        //                    kwargs: { vals: record.data }
                    }).then(function (res) {
                        if(res){
                            return self.do_action({
                            name: ("This Contact would be duplicated."),
                            type: 'ir.actions.act_window',
                            res_model: 'base.partner.merge.automatic.wizard',
                            view_mode: 'form',
                            view_type: 'form',
                            views: [[false, 'form'],[false, 'list'],[false, 'kanban']],
                            target: 'new',
                            context:  {
                                'state': 'selection',
                                'active_model': self.modelName,
//                                'dst_partner_id': record.data.id,
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
                                'new_contact': false,
                                'form_dialog': false,
                                'edit_contact': record.data.id,
                            },
                            });
                        }else{
                            return changedFields
                        }

                    });
                });
            }
        }
        else if (record.model ==='hr.set.daily.target'){
            if (record.data.line_ids.length === 0) {
                this.do_warn(_t("Error"), _t("Please Set Daily Target first before saving"));
                return
            }
            else if (!self.model.isDirty(record.id)){
                self.do_warn(_t("Error"), _t("Recruiter Daily Target must be added"));
                return
            }
            else{
                return self._super.apply(self, arguments);
            }
        }
        else if (record.model ==='hr.set.monthly.target'){
            if (record.data.line_ids.length === 0) {
                this.do_warn(_t("Error"), _t("Please Set Monthly Target first before saving"));
                return
            }
            else if (!self.model.isDirty(record.id)){
                self.do_warn(_t("Error"), _t("Recruiter Monthly Target must be added"));
                return
            }
            else{
                return self._super.apply(self, arguments);
            }
        }
        else{
            return self._super.apply(self, arguments);
//             ev.stopPropagation(); // Prevent x2m lines to be auto-saved
//             this.saveRecord();
        }
    }

});
});
