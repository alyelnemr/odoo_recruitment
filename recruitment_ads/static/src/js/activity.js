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


MailActivity.include({

    _markActivityDDDone: function (id, call_result_id ) {
        return this._rpc({
                model: 'mail.activity',
                method: 'action_call_result',
                args: [[id]],
                kwargs: {call_result_id: call_result_id},
            });
      },



    _onMarkActivityDone: function (event) {
        debugger;
        event.preventDefault();
        var self = this;
        var $popover_el = $(event.currentTarget);
        var activity_id = $popover_el.data('activity-id');
        var previous_activity_type_id = $popover_el.data('previous-activity-type-id');
        if (!$popover_el.data('bs.popover')) {
            $popover_el.popover({
                title : _t('Feedback'),
                html: 'true',
                trigger:'click',
                content : function() {
                    var $popover = $(QWeb.render("mail.activity_feedback_form", {'previous_activity_type_id': previous_activity_type_id}));
                    $popover.on('click', '.o_activity_popover_done_next', function () {
                        var feedback = _.escape($popover.find('#activity_feedback').val());
                        var call_result_id = _.escape($popover.find('#activity_call_result').val());
                        var previous_activity_type_id = $popover_el.data('previous-activity-type-id');
                        self._markActivityDone(activity_id, feedback )
                            .then(self.scheduleActivity.bind(self, previous_activity_type_id));
                        self._markActivityDDDone(activity_id, call_result_id )
                            .then(self.scheduleActivity.bind(self, previous_activity_type_id));
                    });
                    $popover.on('click', '.o_activity_popover_done', function () {

                        var feedback = _.escape($popover.find('#activity_feedback').val());
                        var call_result_id = _.escape($popover.find('#activity_call_result').val());

//                        if (previous_activity_type_id != 2 ){
//                              self._markActivityDone(activity_id, feedback)
//                            .then(self._reload.bind(self, {activity: true, thread: true}));
//
//                        }
                        if (call_result_id ){
                             self._markActivityDone(activity_id, feedback)
                            .then(self._reload.bind(self, {activity: true, thread: true}));
                        }

                        if (previous_activity_type_id == 2){
                            self._markActivityDDDone(activity_id,call_result_id)
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

