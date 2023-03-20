/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */

'use strict';

$.fn.treestatus = function() {
    return this.each(function() {
        // Register an on-click handler for each log update edit button.
        $('.log-update-edit').on("click", function () {
            // Toggle the elements from hidden/visible.
            var closest_form = $(this).closest('.log-update-form');
            closest_form.find('.log-update-hidden').toggle();
            closest_form.find('.log-update-visible').toggle();
        });

        // Register an on-click handler for each recent changes edit button.
        $('.recent-changes-edit').on("click", function () {
            // Toggle the elements from hidden/visible.
            var closest_form = $(this).closest('.recent-changes-form');
            closest_form.find('.recent-changes-update-hidden').toggle();
            closest_form.find('.recent-changes-update-visible').toggle();
        });

        // Toggle selected on all trees.
        $('.select-all-trees').on("click", function () {
            $('.tree-select-checkbox').prop('checked', true);
        });
    });
};
