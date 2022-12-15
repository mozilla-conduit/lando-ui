/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */

'use strict';

$(document).ready(function() {
  let $timeline = $('.StackPage-timeline');
  let $landingPreview = $('.StackPage-landingPreview');
  let $stack = $('.StackPage-stack');
  let $secRequestSubmitted = $('.StackPage-secRequestSubmitted');
  let $flashMessages = $('.FlashMessages');
  let $queue = $('.QueuePage');

  // Initialize components
  $('.Navbar').landoNavbar();
  $timeline.timeline();
  $landingPreview.landingPreview();
  $stack.stack();
  $secRequestSubmitted.secRequestSubmitted();
  $flashMessages.flashMessages();
  $queue.queue();
});
