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
var manager ;

//To Fix A bug in it
var CalendarController = require('web.CalendarController');
var QuickCreate = require('web.CalendarQuickCreate');
var dialogs = require('web.view_dialogs');
var _t = core._t;

var QWeb = core.qweb;
CalendarController.include({
    _onOpenCreate : function (event) {
        var self = this;
        if (this.model.get().scale === "month") {
            event.data.allDay = true;
        }
        var data = this.model.calendarEventToRecord(event.data);

        var context = _.extend({}, this.context, event.options && event.options.context);
        context.default_name = data.name || null;
        context['default_' + this.mapping.date_start] = data[this.mapping.date_start] || null;
        if (this.mapping.date_stop) {
            context['default_' + this.mapping.date_stop] = data[this.mapping.date_stop] || null;
        }
        if (this.mapping.date_delay) {
            context['default_' + this.mapping.date_delay] = data[this.mapping.date_delay] || null;
        }
        if (this.mapping.all_day) {
            context['default_' + this.mapping.all_day] = data[this.mapping.all_day] || null;
        }

        for (var k in context) {
            if (context[k] && context[k]._isAMomentObject) {
                context[k] = context[k].clone().utc().format('YYYY-MM-DD HH:mm:ss');
            }
        }

        var options = _.extend({}, this.options, event.options, {context: context});

        if (this.quick != null) {
            this.quick.destroy();
            this.quick = null;
        }

        if(!options.disableQuickCreate && !event.data.disableQuickCreate && this.quickAddPop) {
            this.quick = new QuickCreate(this, true, options, data, event.data);
            this.quick.open();
            this.quick.focus();
            return;
        }

        var title = _t("Create");
        if (this.renderer.arch.attrs.string) {
            title += ': ' + this.renderer.arch.attrs.string;
        }
        if (this.eventOpenPopup) {
            new dialogs.FormViewDialog(self, {
                res_model: this.modelName,
                context: context,
                title: title,
                view_id : parseInt(this.formViewId) || false, //Bug Fixed view id should be spe
                disable_multiple_selection: true,
                on_saved: function () {
                    if (event.data.on_save) {
                        event.data.on_save();
                    }
                    self.reload();
                },
            }).open();
        } else {
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: this.modelName,
                views: [[parseInt(this.formViewId) || false, 'form']], // Bug Fixed view id should be integer not string
                target: 'current',
                context: context,
            });
        }
    },
});
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
        this.getSession().user_has_group('hr_recruitment.group_hr_recruitment_manager').then(function(has_group) {
            if(has_group) {
             window.manager =  true;
            }
         });

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
        this.getSession().user_has_group('hr_recruitment.group_hr_recruitment_manager').then(function(has_group) {
            if(has_group) {
             window.manager =  true;
            }
         });
        if (this.record.data.user_id != false && this.record.data.user_id.data.id !== Session.uid && window.manager !== true){
            console.log(window.manager);
           alert('This Application is Owned by another Recruiter , you are not allowed to take any on.');
        }else{

            if (this.record.data.partner_phone && this.record.data.partner_mobile && this.record.data.email_from){
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
            }else{
                console.log('elseeee')
                alert('Please insert Applicant Mobile /Email /Phone in order to schedule activity .');

            }}
    },
    _onScheduleActivity: function () {
        this.getSession().user_has_group('hr_recruitment.group_hr_recruitment_manager').then(function(has_group) {
            if(has_group) {
             window.manager =  true;
            }
         });

        if (this.record.data.user_id != false && this.record.data.user_id.data.id !== Session.uid && window.manager !== true){
            console.log(window.manager);
           alert('This Application is Owned by another Recruiter , you are not allowed to take any on.');
        }else{

        if (this.record.data.job_id){
            if (this.record.data.allow_call){
                this.fields.activity.scheduleActivity(false);
            }else{
                if (this.record.data.partner_phone && this.record.data.partner_mobile && this.record.data.email_from){
                    this.fields.activity.scheduleActivity(false);
                }else{
                    console.log('elseeee')
                    alert('Please insert Applicant Mobile /Email /Phone in order to schedule activity .');
                }
            }
        }else{
            if (this.record.data.partner_phone && this.record.data.partner_mobile && this.record.data.email_from){
                this.fields.activity.scheduleActivity(false);
            }else{
                console.log('elseeee')
                alert('Please insert Applicant Mobile /Email /Phone in order to schedule activity .');
            }
        }
        }
    },
    _onOpenComposerMessage: function () {
      this.getSession().user_has_group('hr_recruitment.group_hr_recruitment_manager').then(function(has_group) {
            if(has_group){window.manager =  true; }
         });
        if (this.record.data.user_id != false && this.record.data.user_id.data.id !== Session.uid && window.manager !== true){
           alert('This Application is Owned by another Recruiter , you are not allowed to take any on.');
        }else{this._super.apply(this, arguments);}
    },

    _onOpenComposerNote: function () {
        this.getSession().user_has_group('hr_recruitment.group_hr_recruitment_manager').then(function(has_group) {
            if(has_group){window.manager =  true; }
         });
        if (this.record.data.user_id != false && this.record.data.user_id.data.id !== Session.uid && window.manager !== true){
           alert('This Application is Owned by another Recruiter , you are not allowed to take any on.');
        }else{this._super.apply(this, arguments);}
    },

    });
 });

