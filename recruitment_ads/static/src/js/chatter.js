odoo.define('recruitment_ads.Chatter', function (require) {
"use strict";

var Activity = require('mail.Activity');
var chat_mixin = require('mail.chat_mixin');
var ChatterComposer = require('mail.ChatterComposer');
var Followers = require('mail.Followers');
var ThreadField = require('mail.ThreadField');
var utils = require('mail.utils');

var concurrency = require('web.concurrency');
var config = require('web.config');
var core = require('web.core');
var Widget = require('web.Widget');
var Chatter = require('mail.Chatter');
var Session = require('web.session');

var QWeb = core.qweb;

Chatter.include({
    events: {
        'click .o_chatter_button_new_message': '_onOpenComposerMessage',
        'click .o_chatter_button_log_note': '_onOpenComposerNote',
        'click .o_chatter_button_schedule_activity': '_onScheduleActivity',
        'click .o_chatter_button_schedule_interview': '_onScheduleInterview',
    },
    start: function () {
        //override to add interview button
        var res = this._super.apply(this, arguments);

        this.$topbar = this.$('.o_chatter_topbar');

        // render and append the buttons
        this.$topbar.append(QWeb.render('mail.Chatter.Buttons', {
            schedule_interview_btn: this.context.default_model === 'hr.applicant',
        }));

        // start and append the widgets
        var fieldDefs = _.invoke(this.fields, 'appendTo', $('<div>'));
        var def = this.dp.add($.when.apply($, fieldDefs));
        this._render(def).then(this._updateMentionSuggestions.bind(this));

        return res;
    },
    _onScheduleInterview: function () {
        self = this;
        Session.rpc('/web/dataset/call_kw/ir.ui.view/get_view_id', {
                "model": "ir.ui.view",
                "method": "get_view_id",
                "args": ['recruitment_ads.view_calendar_event_interview_calender'],
                "kwargs": {}
            }).then(function(view_id){
                var action = {
                    type: 'ir.actions.act_window',
                    name: 'Schedule Interview',
                    res_model: 'calendar.event',
                    view_mode: 'calendar,tree,form',
                    view_type: 'form',
                    views: [[false || view_id, 'calendar']],
                    target: 'current',
                    domain: [['type','=','interview']],
                    context: {
                        default_name: self.record_name,
                        default_res_id: self.record.res_id,
                        default_res_model: self.record.model,
                        default_type: 'interview',
                    },
                };
                return self.do_action(action);
            });

    },

    });
});
