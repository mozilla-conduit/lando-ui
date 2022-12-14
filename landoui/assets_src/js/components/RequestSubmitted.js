/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */

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
