/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */

'use strict';

$.fn.formatTime = function() {
  return this.each(function() {
    let time = $(this).data('timestamp');
    let date = new Date(time);

    $(this).text(date.toLocaleString('en', {
      weekday: 'short',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      timeZoneName: 'short',
      hour: 'numeric',
      minute: 'numeric'
    }));
  });
};
