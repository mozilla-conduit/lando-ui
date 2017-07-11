'use strict';

$.fn.landoNavbar = function() {
  return this.each(function() {
    let $navbar = $(this);

    // Initialize the responsive menu.
    let $menu = $navbar.find('#Navbar-menu').first();
    let $mobileMenuBtn = $navbar.find('.navbar-burger').first();
    $mobileMenuBtn.on('click', () => {
      $menu.toggleClass('is-active');
      $mobileMenuBtn.toggleClass('is-active');
    });

    // Initialize the settings modal.
    let $modal = $navbar.find('.Navbar-modal').first();
    let $modalToggleBtn = $navbar.find('.Navbar-userSettingsBtn').first();
    let $modalSubmitBtn = $navbar.find('.Navbar-modalSubmit').first();
    let $modalCancelBtn = $navbar.find('.Navbar-modalCancel');

    $modalToggleBtn.on('click', () => {
      $modal.toggleClass('is-active');
    });

    $modalSubmitBtn.on('click', () => {
      // TODO implement user settings
      $modal.removeClass('is-active');
      console.log('Your settings have been saved.');
    });

    $modalCancelBtn.each(function() {
      $(this).on('click', () => {
        $modal.removeClass('is-active');
      });
    });
  });
};
