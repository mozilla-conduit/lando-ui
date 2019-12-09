'use strict';

$.fn.flashMessages = function() {
  return this.each(function() {
    let $modal = $(this);
    let $closeBtn = $modal.find('.FlashMessages-close');

    $closeBtn.on('click', e => {
      e.preventDefault();
      $modal.hide();
    });
  });
};
