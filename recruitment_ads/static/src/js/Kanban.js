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

KanbanColumn.include({
    start: function () {
        this._super.apply(this, arguments);
        var self = this;
        var defs = [this._super.apply(this, arguments)];
        this.$header = this.$('.o_kanban_header');

        for (var i = 0; i < this.data_records.length; i++) {
            this._addRecord(this.data_records[i]);
        }
        this.$header.find('.o_kanban_header_title').tooltip();
        if (!config.device.isMobile) {
            // deactivate sortable in mobile mode.  It does not work anyway,
            // and it breaks horizontal scrolling in kanban views.  Someday, we
            // should find a way to use the touch events to make sortable work.
             this.$el.sortable({
                connectWith: '.o_kanban_group',
                containment: this.draggable ? '.o_kanban_view' : 'parent',
                revert: 0,
                delay: 0,
                items: '> .o_kanban_record:not(.o_updating)',
                helper: 'clone',
                cursor: 'move',
                over: function () {
                    console.log(self);
                    self.$el.addClass('o_kanban_hover');
                },
                out: function () {
                    self.$el.removeClass('o_kanban_hover');
                },
                update: function (event, ui) {
                debugger;
                    var record = ui.item.data('record');
                    if(record.modelName === 'hr.applicant' && record.recordData.user_id.data.id !== session.uid){
                         event.preventDefault();
                        return alert('sorry you cant');
                    }else{
                        var index = self.records.indexOf(record);
                        record.$el.removeAttr('style');  // jqueryui sortable add display:block inline
                        if (index >= 0) {
                            if ($.contains(self.$el[0], record.$el[0])) {
                                // resequencing records
                                self.trigger_up('kanban_column_resequence', {ids: self._getIDs()});
                            }
                        } else {
                            // adding record to this column
                            ui.item.addClass('o_updating');
                            self.trigger_up('kanban_column_add_record', {record: record, ids: self._getIDs()});
                        }
                      }
                }
            });
        }
        this.$el.click(function (event) {
            if (self.folded) {
                self._onToggleFold(event);
            }
        });
        if (this.barOptions) {
            this.$el.addClass('o_kanban_has_progressbar');
            this.progressBar = new KanbanColumnProgressBar(this, this.barOptions, this.data);
            defs.push(this.progressBar.appendTo(this.$header));
        }

        var title = this.folded ? this.title + ' (' + this.data.count + ')' : this.title;
        this.$header.find('.o_column_title').text(title);

        this.$el.toggleClass('o_column_folded', this.folded && !config.device.isMobile);
        var tooltip = this.data.count + _t(' records');
        tooltip = '<p>' + tooltip + '</p>' + this.tooltipInfo;
        this.$header.find('.o_kanban_header_title').tooltip({html: true}).attr('data-original-title', tooltip);
        if (!this.remaining) {
            this.$('.o_kanban_load_more').remove();
        } else {
            this.$('.o_kanban_load_more').html(QWeb.render('KanbanView.LoadMore', {widget: this}));
        }

        return $.when.apply($, defs);
    },




});
});