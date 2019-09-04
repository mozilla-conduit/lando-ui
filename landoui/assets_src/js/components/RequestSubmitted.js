'use strict';

$.fn.secRequestSubmitted = function() {
  return this.each(function() {
    let $modal = $(this);
    let $closeBtn = $modal.find('.StackPage-secRequestSubmitted-close');

    $closeBtn.on('click', e => {
      e.preventDefault();
      $modal.removeClass('is-active');
    });

    $(document).ready(() => {
      let url = new URL(document.URL);
      if (url.searchParams.has('show_approval_success')) {
        $modal.addClass('is-active');
      }
    });
  });
};
