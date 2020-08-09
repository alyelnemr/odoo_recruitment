odoo.define('recruitment_ads.KanbanRenderer', function (require) {
"use strict";


var BasicRenderer = require('web.BasicRenderer');
var core = require('web.core');
var KanbanColumn = require('web.KanbanColumn');
var KanbanRecord = require('web.KanbanRecord');
var quick_create = require('web.kanban_quick_create');
var QWeb = require('web.QWeb');
var session = require('web.session');
var utils = require('web.utils');

var ColumnQuickCreate = quick_create.ColumnQuickCreate;

var qweb = core.qweb;

var KanbanRenderer = require('web.KanbanRenderer');
KanbanController.include({

    _renderGrouped: function (fragment) {
        var self = this;

        // Render columns
        _.each(this.state.data, function (group) {
        if (group.model==='hr.setup.approval.cycle.users'){
                if (group.value === 'Approval Group'){
                    group.data.sort((a, b) => (a.data.id > b.data.id) ? 1 : (a.data.id === b.data.id) ? 1 : -1);
                }
            }
            var column = new KanbanColumn(self, group, self.columnOptions, self.recordOptions);
            if (!group.value) {
                column.prependTo(fragment); // display the 'Undefined' group first
                self.widgets.unshift(column);
            } else {
                column.appendTo(fragment);
                self.widgets.push(column);
            }

        });

        // remove previous sorting
        if(this.$el.sortable('instance') !== undefined) {
            this.$el.sortable('destroy');
        }
        if (this.groupedByM2O) {
            // Enable column sorting
            this.$el.sortable({
                axis: 'x',
                items: '> .o_kanban_group',
                handle: '.o_kanban_header_title',
                cursor: 'move',
                revert: 150,
                delay: 100,
                tolerance: 'pointer',
                forcePlaceholderSize: true,
                stop: function () {
                    var ids = [];
                    self.$('.o_kanban_group').each(function (index, u) {
                        // Ignore 'Undefined' column
                        if (_.isNumber($(u).data('id'))) {
                            ids.push($(u).data('id'));
                        }
                    });
                    self.trigger_up('resequence_columns', {ids: ids});
                },
            });

            // Enable column quickcreate
            if (this.createColumnEnabled) {
                this.quickCreate = new ColumnQuickCreate(this);
                this.quickCreate.appendTo(fragment);
            }
        }

    },

});
});
