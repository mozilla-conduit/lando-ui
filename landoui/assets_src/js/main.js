'use strict';

$(document).ready(function() {
  // Initialize components
  $('.Navbar').landoNavbar();

  // Initialize plugins
  $('time[data-timestamp]').formatTime();
});
