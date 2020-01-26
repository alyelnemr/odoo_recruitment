odoo.define('recruitment_ads.Activity', function (require) {
"use strict";

var AbstractField = require('web.AbstractField');
var concurrency = require('web.concurrency');
var core = require('web.core');
var field_registry = require('web.field_registry');
var time = require('web.time');
var utils = require('mail.utils');

var QWeb = core.qweb;
var _t = core._t;
var MailActivity = require('mail.Activity');
var Session = require('web.session');
var Dialog = require('web.Dialog');


MailActivity.include({
    _onScheduleInterview: function () {
        self = this;
        var get_calendar_view = Session.rpc('/web/dataset/call_kw/ir.ui.view/get_view_id', {
            "model": "ir.ui.view",
            "method": "get_view_id",
            "args": ['recruitment_ads.view_calendar_event_interview_calender'],
            "kwargs": {}
            });
        var get_form_view =  Session.rpc('/web/dataset/call_kw/ir.ui.view/get_view_id', {
            "model": "ir.ui.view",
            "method": "get_view_id",
            "args": ['recruitment_ads.view_calendar_event_interview_form'],
            "kwargs": {}
            });
        $.when(get_calendar_view,get_form_view).then(function(calendar_view_id,form_view_id){
            var name = self.record.data.partner_name+"'s interview";
            if (self.record.data.job_id){
                name = self.record.data.job_id.data.display_name + " - " + name;
            }
            var action = {
                    type: 'ir.actions.act_window',
                    name: 'Schedule Interview',
                    res_model: 'calendar.event',
                    view_mode: 'calendar,form',
                    view_type: 'form',
                    view_id: false || form_view_id,
                    views: [[false || calendar_view_id, 'calendar'],[false || form_view_id ,'form']],
                    target: 'current',
                    domain: [['type','=','interview']],
                    context: {
                        default_name: name,
                        default_res_id: self.record.res_id,
                        default_res_model: self.record.model,
                        default_type: 'interview',
                    },
                };
            return self.do_action(action);
        });

    },
    _onEditActivity: function (event, options) {
        var self = this;
        var _super = this._super.bind(this);
        var activity_id = $(event.currentTarget).data('activity-id');
        var activity = _.find(this.activities, function (act) { return act.id === activity_id; });
        if (activity && activity.activity_category === 'interview' && activity.calendar_event_id) {
            var get_form_view =  Session.rpc('/web/dataset/call_kw/ir.ui.view/get_view_id', {
                "model": "ir.ui.view",
                "method": "get_view_id",
                "args": ['recruitment_ads.view_calendar_event_interview_form'],
                "kwargs": {}
            });

            $.when(get_form_view).then(function(form_view_id){
                    return _super(event, _.extend({
                    res_model: 'calendar.event',
                    res_id: activity.calendar_event_id[0],
                    view_id: form_view_id || false,
                    views: [[form_view_id || false, 'form']],
                }));

            });

        }
        else{
            return self._super(event, options);
        }
    },

    _onUnlinkActivity: function (event, options) {
        event.preventDefault();
        var self = this;
        var activity_id = $(event.currentTarget).data('activity-id');
        var activity = _.find(this.activities, function (act) { return act.id === activity_id; });
        if (activity && activity.activity_category === 'interview' && activity.calendar_event_id) {
            Dialog.confirm(
                self,
                _t("The activity is linked to a interview. Deleting it will remove the interview as well. Do you want to proceed ?"), {
                    confirm_callback: function () {
                        return self._rpc({
                            model: 'mail.activity',
                            method: 'unlink_w_meeting',
                            args: [[activity_id]],
                        })
                        .then(self._reload.bind(self, {activity: true}));
                    },
                }
            );
        }
        else {
            return self._super(event, options);
        }
    },

    _markActivityDDDone: function (id, feedback,call_result_id ) {
        return this._rpc({
                model: 'mail.activity',
                method: 'action_call_result',
                args: [[id]],
                kwargs: {feedback:feedback,call_result_id: call_result_id},
            });
      },


    _markInterviewDone: function (id, feedback,interview_result) {
        return this._rpc({
                model: 'mail.activity',
                method: 'action_interview_result',
                args: [[id]],
                kwargs: {feedback:feedback,interview_result: interview_result},
            });
      },

    _onMarkActivityDone: function (event) {
        event.preventDefault();
        var self = this;
        var $popover_el = $(event.currentTarget);
        var activity_id = $popover_el.data('activity-id');
        var activity = _.find(this.activities, function (act) { return act.id === activity_id; });
        var previous_activity_type_id = $popover_el.data('previous-activity-type-id');
        if (!$popover_el.data('bs.popover')) {
            $popover_el.popover({
                title : _t('Feedback'),
                html: 'true',
                trigger:'click',
                content : function() {
                    var $popover = $(QWeb.render("mail.activity_feedback_form", {'previous_activity_type_id': previous_activity_type_id,'activity_category':activity && activity.activity_category}));
                    $popover.on('click', '.o_activity_popover_done_next', function () {
                        var feedback = _.escape($popover.find('#activity_feedback').val());
                        var call_result_id = _.escape($popover.find('#activity_call_result').val());
                        var interview_result = _.escape($popover.find('#activity_interview_result').val());
                        var previous_activity_type_id = $popover_el.data('previous-activity-type-id');
                        if (activity && activity.activity_category === 'interview') {
                            if (interview_result === "") {
                                Dialog.alert(
                                    self,
                                    _t("Please select Interview result!"), {
                                        confirm_callback: function () {
                                            self._reload.bind(self, {activity: true});
                                        },
                                    }
                                );
                            }
                            else if (interview_result === "Rejected" && feedback === ""){
                                Dialog.alert(
                                    self,
                                    _t("Please fill the rejection reason in feedback!"), {
                                        confirm_callback: function () {
                                            self._reload.bind(self, {activity: true});
                                        },
                                    }
                                );
                            }
                            else{
                                self._markInterviewDone(activity_id,feedback,interview_result)
                                    .then(self.scheduleActivity.bind(self, previous_activity_type_id));
                            }
                        }
                        else if (previous_activity_type_id == 2){
                            if (call_result_id === "") {
                                Dialog.alert(
                                    self,
                                    _t("Please select Call result!"), {
                                        confirm_callback: function () {
                                            self._reload.bind(self, {activity: true});
                                        },
                                    }
                                );
                            }
                            else if (call_result_id ==="Invited") {
                                self._markActivityDDDone(activity_id, feedback,call_result_id )
                                    .then(self._onScheduleInterview(self));

                            }
                            else{
                                self._markActivityDDDone(activity_id, feedback,call_result_id )
                                    .then(self.scheduleActivity.bind(self, previous_activity_type_id));
                            }
                        }
                        else{
                            self._markActivityDone(activity_id, feedback )
                                .then(self.scheduleActivity.bind(self, previous_activity_type_id));
                        }
                    });
                    $popover.on('click', '.o_activity_popover_done', function () {

                        var feedback = _.escape($popover.find('#activity_feedback').val());

//                        if (previous_activity_type_id != 2 ){
//                              self._markActivityDone(activity_id, feedback)
//                            .then(self._reload.bind(self, {activity: true, thread: true}));
//
//                        }
                        if (previous_activity_type_id == 2){
                            var call_result_id = _.escape($popover.find('#activity_call_result').val());
                               if (call_result_id === "") {
                                    Dialog.alert(
                                        self,
                                        _t("Please select Call result!"), {
                                            confirm_callback: function () {
                                                self._reload.bind(self, {activity: true});
                                            },
                                        }
                                    );
                               }
                               else{
                                    self._markActivityDDDone(activity_id,feedback,call_result_id)
                                    .then(self._reload.bind(self, {activity: true, thread: true}));
                               }
                        }
                        else if(activity && activity.activity_category === 'interview') {
                            var interview_result = _.escape($popover.find('#activity_interview_result').val());
                            if (interview_result === "") {
                                Dialog.alert(
                                    self,
                                    _t("Please select Interview result!"), {
                                        confirm_callback: function () {
                                            self._reload.bind(self, {activity: true});
                                        },
                                    }
                                );
                            }
                            else if (interview_result === "Rejected" && feedback === ""){
                                Dialog.alert(
                                    self,
                                    _t("Please fill the rejection reason in feedback!"), {
                                        confirm_callback: function () {
                                            self._reload.bind(self, {activity: true});
                                        },
                                    }
                                );
                            }
                            else{
                                self._markInterviewDone(activity_id,feedback,interview_result)
                                .then(self._reload.bind(self, {activity: true, thread: true}));
                            }
                        }
                        else{
                            self._markActivityDone(activity_id, feedback)
                            .then(self._reload.bind(self, {activity: true, thread: true}));
                        }
                    });
                    $popover.on('click', '.o_activity_popover_discard', function () {
                        $popover_el.popover('hide');
                    });
                    return $popover;
                },
            }).on("show.bs.popover", function (e) {
                var $popover = $(this).data("bs.popover").tip();
                $popover.addClass('o_mail_activity_feedback').attr('tabindex', 0);
                $(".o_mail_activity_feedback.popover").not(e.target).popover("hide");
            }).on("shown.bs.popover", function () {
                var $popover = $(this).data("bs.popover").tip();
                $popover.find('#activity_call_result').focus();
                $popover.off('focusout');
                $popover.focusout(function (e) {
                    // outside click of popover hide the popover
                    // e.relatedTarget is the element receiving the focus
                    if(!$popover.is(e.relatedTarget) && !$popover.find(e.relatedTarget).length) {
                        $popover.popover('hide');
                    }
                });
            }).popover('show');
        }
    },

    });
});

