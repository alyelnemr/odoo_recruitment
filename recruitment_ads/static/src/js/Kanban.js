odoo.define('recruitment_ads.KanbanColumn', function (require){
"use strict";

var config = require('web.config');
var core = require('web.core');
var Dialog = require('web.Dialog');
var kanban_quick_create = require('web.kanban_quick_create');
var KanbanRecord = require('web.KanbanRecord');
var view_dialogs = require('web.view_dialogs');
var Widget = require('web.Widget');
var KanbanColumn = require('web.KanbanColumn');
var session = require('web.session');
var _t = core._t;
var QWeb = core.qweb;
var RecordQuickCreate = kanban_quick_create.RecordQuickCreate;
var rpc = require('web.rpc');
var target_column;
var source_column;
var manager;
KanbanColumn.include({
    current_user_group: function (id){
        return this._rpc({
                model: 'hr.applicant',
                method: 'get_current_user_group',
                args: [[id]],
            }).then(function (result) {
                if (result.length > 0) {
                    window.manager = result;
                    return result;
//
                }
            });
      },
    start: function () {
        this._super.apply(this, arguments);
        var flag ;
        var  responsible ;
        var  x= this.current_user_group();
        var self = this;

        if (!config.device.isMobile) {
            // deactivate sortable in mobile mode.  It does not work anyway,
            // and it breaks horizontal scrolling in kanban views.  Someday, we
            // should find a way to use the touch events to make sortable work.
             this.$el.sortable({
                over: function () {
                debugger;
                    flag = 'over';
                    self.$el.addClass('o_kanban_hover');
                    target_column = self.title;
                },
                out: function () {
                debugger;
                    flag = 'out';
                    source_column = self.title;
                    self.$el.removeClass('o_kanban_hover');
                },
                update: function (event, ui) {
                    var record = ui.item.data('record');
                    if (record.modelName === 'hr.applicant' && record.recordData.activity_ids){
                        if(record.recordData.activity_ids.res_ids != false){
                         event.preventDefault();
                         if(flag === 'over'){
                            alert('Please insert Activity Result in order to be transferred to another stage');}
                        }
                        else{
                            var checkmanager = window.manager;
                            if (record.recordData.user_id !== false) {
                                if(record.recordData.user_id.data.id !== session.uid){
                                    responsible = 'false';
                                }
                            }else {
                                responsible = 'false';
                            }

                            if(record.modelName === 'hr.applicant' && responsible === 'false' && checkmanager !== 'manager'){
                                 event.preventDefault();
                                 if(flag === 'over'){
                                    return alert('This Application is owned by another Recruiter');
                                 }
                            } else {
                                var index = self.records.indexOf(record);
                                record.$el.removeAttr('style');  // jqueryui sortable add display:block inline
                                if (index >= 0) {
                                    if ($.contains(self.$el[0], record.$el[0])) {
                                        // resequencing records
                                        self.trigger_up('kanban_column_resequence', {ids: self._getIDs()});
                                    }else if (record.modelName==='hr.applicant' && target_column==='Approval Cycle' && record.recordData.approval_cycles_number===0){
                                        event.preventDefault();
                                        if(flag === 'over'){
                                            alert('You can not add application to approval cycle stage until create Approval cycle on application.');
                                        }
                                    }else if (record.modelName==='hr.applicant' && source_column==='Approval Cycle' && record.recordData.approved_approval_cycles_number===0){
                                        event.preventDefault();
                                        if(flag === 'over'){
                                            alert('You can not move application to other stage until the approval cycle is approved.');
                                        }
                                    }
                                } else {

                                    if (record.modelName==='hr.applicant' && target_column==='Approval Cycle' && record.recordData.approval_cycles_number===0){
                                        event.preventDefault();
                                        if(flag === 'over'){
                                            alert('You can not add application to approval cycle stage until create Approval cycle on application.');
                                        }
                                    }else if (record.modelName==='hr.applicant' && source_column==='Approval Cycle' && record.recordData.approved_approval_cycles_number===0){
                                        event.preventDefault();
                                        if(flag === 'over'){
                                            alert('You can not move application to other stage until the approval cycle is approved.');
                                        }
                                    }
                                    else{

                                        // adding record to this column
                                        ui.item.addClass('o_updating');
                                        self.trigger_up('kanban_column_add_record', {record: record, ids: self._getIDs()});
                                    }
                                }
                            }
                        }
                    } else {
                        var record = ui.item.data('record');
                        var index = self.records.indexOf(record);
                        record.$el.removeAttr('style');  // jqueryui sortable add display:block inline
                        if (index >= 0) {
                            if ($.contains(self.$el[0], record.$el[0])) {
                                // resequencing records
                                self.trigger_up('kanban_column_resequence', {ids: self._getIDs()});
                            }else if (record.modelName==='hr.applicant' && target_column==='Approval Cycle' && record.recordData.approval_cycles_number===0){
                                event.preventDefault();
                                if(flag === 'over'){
                                    alert('You can not add application to approval cycle stage until create Approval cycle on application.');
                                }
                            }else if (record.modelName==='hr.applicant' && source_column==='Approval Cycle' && record.recordData.approved_approval_cycles_number===0){
                                        event.preventDefault();
                                        if(flag === 'over'){
                                            alert('You can not move application to other stage until the approval cycle is approved.');
                                        }
                                    }
                        } else {

                             if (record.modelName==='hr.applicant' && target_column==='Approval Cycle' && record.recordData.approval_cycles_number===0){
                                event.preventDefault();
                                if(flag === 'over'){
                                    alert('You can not add application to approval cycle stage until create Approval cycle on application.');
                                }
                            }else if (record.modelName==='hr.applicant' && source_column==='Approval Cycle' && record.recordData.approved_approval_cycles_number===0){
                                event.preventDefault();
                                if(flag === 'over'){
                                    alert('You can not move application to other stage until the approval cycle is approved.');
                                }
                            }else{

                                // adding record to this column
                                ui.item.addClass('o_updating');
                                self.trigger_up('kanban_column_add_record', {record: record, ids: self._getIDs()});
                            }
                        }
                    }
                }
            });
        }
//        this.$el.click(function (event) {
//            if (self.folded) {
//                self._onToggleFold(event);
//            }
//        });
//        if (this.barOptions) {
//            this.$el.addClass('o_kanban_has_progressbar');
//            this.progressBar = new KanbanColumnProgressBar(this, this.barOptions, this.data);
//            defs.push(this.progressBar.appendTo(this.$header));
//        }

//        var title = this.folded ? this.title + ' (' + this.data.count + ')' : this.title;
//        this.$header.find('.o_column_title').text(title);

//        this.$el.toggleClass('o_column_folded', this.folded && !config.device.isMobile);
//        var tooltip = this.data.count + _t(' records');
//        tooltip = '<p>' + tooltip + '</p>' + this.tooltipInfo;
//        this.$header.find('.o_kanban_header_title').tooltip({html: true}).attr('data-original-title', tooltip);
//        if (!this.remaining) {
//            this.$('.o_kanban_load_more').remove();
//        } else {
//            this.$('.o_kanban_load_more').html(QWeb.render('KanbanView.LoadMore', {widget: this}));
//        }

//        return $.when.apply($, defs);
    },




});
});