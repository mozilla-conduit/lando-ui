/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */

'use strict';

const RELATIVE_UNITS = [
  { unit: 'year',   seconds: 31536000 },
  { unit: 'month',  seconds: 2592000 },
  { unit: 'week',   seconds: 604800 },
  { unit: 'day',    seconds: 86400 },
  { unit: 'hour',   seconds: 3600 },
  { unit: 'minute', seconds: 60 },
  { unit: 'second', seconds: 1 },
];

const relativeFormatter = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });

function humanizeTimeDelta(date, now = new Date()) {
  const deltaSeconds = Math.round((date - now) / 1000);
  const match = RELATIVE_UNITS.find((entry) => Math.abs(deltaSeconds) >= entry.seconds);
  return match
    ? relativeFormatter.format(Math.round(deltaSeconds / match.seconds), match.unit)
    : relativeFormatter.format(deltaSeconds, 'second');
}

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
    // We can't use string interpolation as the minifier eats the
    // empty space between the timestamp and the humanized time delta.
    }) + ' (' + humanizeTimeDelta(date) + ')');
  });
};
