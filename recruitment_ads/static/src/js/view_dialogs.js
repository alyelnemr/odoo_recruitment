odoo.define('recruitment_ads.view_dialogs', function (require) {
"use strict";


var core = require('web.core');
var data = require('web.data');
var Dialog = require('web.Dialog');
var dom = require('web.dom');
var ListController = require('web.ListController');
var ListView = require('web.ListView');
var pyeval = require('web.pyeval');
var SearchView = require('web.SearchView');
var view_registry = require('web.view_registry');
var view_dialogs = require('web.view_dialogs');
var _t = core._t;
view_dialogs.FormViewDialog.include({
 init: function (parent, options) {
        var self = this;

        this.res_id = options.res_id || null;
        this.on_saved = options.on_saved || (function () {});
        this.context = options.context;
        this.model = options.model;
        this.parentID = options.parentID;
        this.recordID = options.recordID;
        this.shouldSaveLocally = options.shouldSaveLocally;

        var multi_select = !_.isNumber(options.res_id) && !options.disable_multiple_selection;
        var readonly = _.isNumber(options.res_id) && options.readonly;

        if (!options || !options.buttons) {
            options = options || {};
            options.buttons = [{
                text: (readonly ? _t("Close") : _t("Discard")),
                classes: "btn-default o_form_button_cancel",
                close: true,
                click: function () {
                    if (!readonly) {
                        self.form_view.model.discardChanges(self.form_view.handle, {
                            rollback: self.shouldSaveLocally,
                        });
                    }
                },
            }];

            if (!readonly) {
                options.buttons.unshift({
                    text: _t("Save") + ((multi_select)? " " + _t(" & Close") : ""),
                    classes: "btn-primary",
                    click: function () {
                        var record = self.form_view.model.get(self.form_view.handle, {raw: true});
                        if (record.model ==='res.partner'){
                            if (typeof(record.data.id) == 'undefined'){
                                this._save().then(function(){
                                    var record = self.form_view.model.get(self.form_view.handle);
                                    $.when(self._rpc({
                                        model: self.form_view.modelName,
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
                                            context:  {
                                                'state': 'selection',
                                                'active_model': self.form_view.modelName,
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
                                                'form_dialog': true,
                                            },
                                        });
                                        self.close()
                                        }else{
                                            self.close()
                                        }
                                    })).then(self.close.bind(self));
                                }.bind(this))
                            }
                            else{
                                // Edit Contact
                                this._save().then(function(){
                                    // record might have been changed by the save (e.g. if this was a new record, it has an
                                    // id now), so don't re-use the copy obtained before the save
                                    var old_data = self.form_view.initialState.data
                                    var record = self.form_view.model.get(self.form_view.handle);
                                    self._rpc({
                                        model: self.form_view.modelName,
                                        method: 'check_contact_duplication',
                                        args: [[record.data.id]],
                                    }).then(function (res) {
                                        if(res){
                                            $.when(self.do_action({
                                            name: ("Merge Selected Contacts"),
                                            type: 'ir.actions.act_window',
                                            res_model: 'base.partner.merge.automatic.wizard',
                                            view_mode: 'form',
                                            view_type: 'form',
                                            views: [[false, 'form'],[false, 'list'],[false, 'kanban']],
                                            target: 'new',
                                            context:  {
                                                'state': 'selection',
                                                'active_model': self.form_view.modelName,
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
                                                'form_dialog': true,
                                                'edit_contact': record.data.id,
                                                'old_data_contact': old_data,
                                            },
                                            })).then(self.close.bind(self));
                                        }else{
                                            self._save().then(self.close.bind(self));
                                        }

                                    });
                                });
                            }
                        }else{
                            this._save().then(self.close.bind(self));
                        }
                    }
                });

                if (multi_select) {
                    options.buttons.splice(1, 0, {
                        text: _t("Save & New"),
                        classes: "btn-primary",
                        click: function () {
                            this._save().then(self.form_view.createRecord.bind(self.form_view, self.parentID));
                        },
                    });
                }
            }
        }
        this._super(parent, options);
    },
//    _save: function ()  {
//        var self = this;
//        var record = self.form_view.model.get(self.form_view.handle, {raw: true});
//        if (record.model ==='res.partner'){
//            if (typeof(record.data.id) == 'undefined'){
//                return this.form_view.saveRecord(this.form_view.handle, {
//                        stayInEdit: true,
//                        reload: false,
//                        savePoint: this.shouldSaveLocally,
//                        viewType: 'form',
//                    }).then(function (changedFields) {
//                        // record might have been changed by the save (e.g. if this was a new record, it has an
//                        // id now), so don't re-use the copy obtained before the save
//                        var record = self.form_view.model.get(self.form_view.handle);
//                        self.on_saved(record, !!changedFields.length);
//                        self._rpc({
//                            model: self.form_view.modelName,
//                            method: 'check_contact_duplication',
//                            args: [[record.data.id]],
//                        }).then(function (res) {
//                            if (res){
//                                return self.do_action({
//                                name: ("Merge Selected Contacts"),
//                                type: 'ir.actions.act_window',
//                                res_model: 'base.partner.merge.automatic.wizard',
//                                view_mode: 'form',
//                                view_type: 'form',
//                                views: [[false, 'form'],[false, 'list'],[false, 'kanban']],
//                                target: 'new',
//                                context:  {
//                                    'state': 'selection',
//                                    'active_model': self.form_view.modelName,
//                                    'dst_partner_id': record.data.id,
//                                    'partner_ids': res,
//                                    'group_by_is_company': false,
//                                    'maximum_group': 0,
//                                    'group_by_parent_id': false,
//                                    'exclude_contact': false,
//                                    'group_by_email': false,
//                                    'exclude_journal_item': false,
//                                    'display_name': '',
//                                    'number_group': 0,
//                                    'group_by_vat': false,
//                                    'new_contact': true,
//                                    'edit_contact': false,
//                                    'form_dialog': true,
//                                },
//                            });
//                            }else{
//                                return this.form_view.saveRecord(this.form_view.handle, {
//                                    stayInEdit: true,
//                                    reload: false,
//                                    savePoint: this.shouldSaveLocally,
//                                    viewType: 'form',
//                                }).then(function (changedFields) {
//                                    // record might have been changed by the save (e.g. if this was a new record, it has an
//                                    // id now), so don't re-use the copy obtained before the save
//                                    var record = self.form_view.model.get(self.form_view.handle);
//                                    self.on_saved(record, !!changedFields.length);
//                                });
//                            }
//                        });
//                })
//
//            }
//            else{
//                // Edit Contact
//                return this.form_view.saveRecord(this.form_view.handle, {
//                        stayInEdit: true,
//                        reload: false,
//                        savePoint: this.shouldSaveLocally,
//                        viewType: 'form',
//                    }).then(function (changedFields) {
//                        // record might have been changed by the save (e.g. if this was a new record, it has an
//                        // id now), so don't re-use the copy obtained before the save
//                        var record = self.form_view.model.get(self.form_view.handle);
//                        self.on_saved(record, !!changedFields.length);
//                        var old_data = self.form_view.initialState.data
//                        self._rpc({
//                            model: self.form_view.modelName,
//                            method: 'check_contact_duplication',
//                            args: [[record.data.id]],
//                        }).then(function (res) {
//                            if(res){
//                                console.log(res)
//                                return self.do_action({
//                                name: ("Merge Selected Contacts"),
//                                type: 'ir.actions.act_window',
//                                res_model: 'base.partner.merge.automatic.wizard',
//                                view_mode: 'form',
//                                view_type: 'form',
//                                views: [[false, 'form'],[false, 'list'],[false, 'kanban']],
//                                target: 'new',
//                                context:  {
//                                    'state': 'selection',
//                                    'active_model': self.form_view.modelName,
//    //                                'dst_partner_id': record.data.id,
//                                    'partner_ids': res,
//                                    'group_by_is_company': false,
//                                    'maximum_group': 0,
//                                    'group_by_parent_id': false,
//                                    'exclude_contact': false,
//                                    'group_by_email': false,
//                                    'exclude_journal_item': false,
//                                    'display_name': '',
//                                    'number_group': 0,
//                                    'group_by_vat': false,
//                                    'new_contact': false,
//                                    'form_dialog': true,
//                                    'edit_contact': record.data.id,
//                                    'old_data_contact': old_data,
//                                },
//                                });
//                            }else{
//                                return this.form_view.saveRecord(this.form_view.handle, {
//                                    stayInEdit: true,
//                                    reload: false,
//                                    savePoint: this.shouldSaveLocally,
//                                    viewType: 'form',
//                                }).then(function (changedFields) {
//                                    // record might have been changed by the save (e.g. if this was a new record, it has an
//                                    // id now), so don't re-use the copy obtained before the save
//                                    var record = self.form_view.model.get(self.form_view.handle);
//                                    self.on_saved(record, !!changedFields.length);
//                                });
//                            }
//
//                    });
//                });
//            }
//        }else{
//            return this.form_view.saveRecord(this.form_view.handle, {
//                stayInEdit: true,
//                reload: false,
//                savePoint: this.shouldSaveLocally,
//                viewType: 'form',
//            }).then(function (changedFields) {
//                // record might have been changed by the save (e.g. if this was a new record, it has an
//                // id now), so don't re-use the copy obtained before the save
//                var record = self.form_view.model.get(self.form_view.handle);
//                self.on_saved(record, !!changedFields.length);
//            });
//        }
//    },
});
});
