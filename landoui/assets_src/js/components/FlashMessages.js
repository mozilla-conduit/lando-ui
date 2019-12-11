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
