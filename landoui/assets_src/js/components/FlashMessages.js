/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */

'use strict';

$.fn.flashMessages = function () {
    return this.each(function () {
        let $section = $(this);
        let $messages = $section.find('.FlashMessages-content');
        let visibleMessages = $messages.length;

        let closeSectionIfEmpty = function () {
            if (visibleMessages <= 0) {
                $section.hide();
            }
        };

        $messages.each(function () {
            let $message = $(this);
            let $closeBtn = $message.find('.FlashMessages-close');

            $closeBtn.on('click', e => {
                e.preventDefault();
                $message.hide();
                visibleMessages--;
                closeSectionIfEmpty();
            });
        })
    });
};
