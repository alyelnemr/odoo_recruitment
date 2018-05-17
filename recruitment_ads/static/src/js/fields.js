odoo.define('recruitment_ads.fields', function (require) {
"use strict";

var RelationalFields = require('web.relational_fields');
var registry = require('web.field_registry');
var FormFieldMany2ManyTags = RelationalFields.FormFieldMany2ManyTags;

var FormFieldMany2ManyShortTags = FormFieldMany2ManyTags.extend({
    tag_template:"FieldMany2ManyShortTag",
    fieldsToFetch: {
        short_display: {type: 'char'},
        display_name: {type: 'char'},
    },

    events: _.extend({}, FormFieldMany2ManyTags.prototype.events, {
        'mouseover .badge': '_onBadgeHover',
    }),

    _onBadgeHover: function (event) {
        var $Badge = $(event.target);
        $Badge.popover({
            html: false,
            trigger: 'hover',
            content: $Badge.data('name'),
            placement: 'right',
        }).popover('show');
    },

    });
registry.add('many2many_short_tags', FormFieldMany2ManyShortTags);
});