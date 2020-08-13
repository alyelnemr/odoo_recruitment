odoo.define('recruitment_ads.KanbanController', function (require) {
"use strict";

var BasicController = require('web.BasicController');
var Context = require('web.Context');
var core = require('web.core');
var view_dialogs = require('web.view_dialogs');

var _t = core._t;
var qweb = core.qweb;

var KanbanController = require('web.KanbanController');
KanbanController.include({
    _onAddRecordToColumn: function (event) {
        var self = this;
        var record = event.data.record;
        var column = event.target;
        this.alive(this.model.moveRecord(record.db_id, column.db_id, this.handle))
            .then(function (column_db_ids) {
                if (column.modelName==='hr.setup.approval.cycle.users'){
                    if (column.title === 'Users'){
                        return self._resequenceRecords(column.db_id, event.data.ids)
                            .then(function () {
                                _.each(column_db_ids, function (db_id) {
                                    var data = self.model.get(db_id);
                                    self.renderer.updateColumn(db_id, data);
                                });
                            });
                    }
                    else{
                        _.each(column_db_ids, function (db_id) {
                            var data = self.model.get(db_id);
                            data.data.sort((a, b) => (a.data.id > b.data.id) ? 1 : (a.data.id === b.data.id) ? 1 : -1);
                            self.renderer.updateColumn(db_id, data);
                            self._updateEnv();

                        });
                    }
                }else{
                    return self._resequenceRecords(column.db_id, event.data.ids)
                                .then(function () {
                                    _.each(column_db_ids, function (db_id) {
                                        var data = self.model.get(db_id);
                                        self.renderer.updateColumn(db_id, data);
                                    });
                                });
                }
            }).fail(this.reload.bind(this));
    },
    _onColumnResequence: function (event) {
        if (event.target.modelName==='hr.setup.approval.cycle.users'){
            if (event.target.title === 'Users'){
                this._resequenceRecords(event.target.db_id, event.data.ids);
            }else{
                var db_id = event.target.db_id;
                var data = this.model.get(db_id);
                data.data.sort((a, b) => (a.data.id > b.data.id) ? 1 : (a.data.id === b.data.id) ? 1 : -1);
                this.renderer.updateColumn(db_id, data);
                this._updateEnv();
            }
        }else{
            this._resequenceRecords(event.target.db_id, event.data.ids);
        }

    },

});
});
