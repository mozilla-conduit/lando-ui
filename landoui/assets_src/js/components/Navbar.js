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
    if (!$modal.length) {
      return;
    }
    let $modalToggleBtn = $navbar.find('.Navbar-userSettingsBtn').first();
    let $modalSubmitBtn = $navbar.find('.Navbar-modalSubmit').first();
    let $modalCancelBtn = $navbar.find('.Navbar-modalCancel');
    let $settingsForm = $modal.find('.userSettingsForm').first();
    let $settingsFormErrors = $modal.find('.userSettingsForm-Errors');
    let $errorPageShowModal = $('.ErrorPage-showAPIToken');

    // Phabricator API Token settings
    // The token's value is stored in the httponly cookie
    let $phabAPITokenInput = $modal.find('#phab_api_token').first();
    let $phabAPITokenReset = $modal.find('#reset_phab_api_token').first();
    let isSetPhabAPIToken = $settingsForm.data('phabricator_api_token');

    modalSubmitBtnOn();
    setAPITokenPlaceholder();

    $modalToggleBtn.on('click', () => {
      $modal.toggleClass('is-active');
    });

    if ($errorPageShowModal) {
      $errorPageShowModal.on('click', e => {
        e.preventDefault();
        $modal.addClass('is-active');
      });
    }

    $settingsForm.on('submit', function(e) {
      e.preventDefault();
      e.stopImmediatePropagation();
      // We don't have any other setting than the API Token
      if (!$phabAPITokenInput.val() && !$phabAPITokenReset.prop('checked')) {
        displaySettingsError('phab_api_token_errors', 'Invalid Token Value');
        return;
      }
      modalSubmitBtnOff();
      $.ajax({
        url: '/settings',
        type: 'post',
        data: $(this).serialize(),
        dataType: 'json',
        success: data => {
          modalSubmitBtnOn();
          if (!data.success) {
            return handlePhabAPITokenErrors(data.errors);
          }
          isSetPhabAPIToken = data.phab_api_token_set;
          restartPhabAPIToken();
          $modal.removeClass('is-active');
          console.log('Your settings have been saved.');
          window.location.reload(true);
        },
        error: () => {
          modalSubmitBtnOn();
          resetSettingsFormErrors();
          displaySettingsError('form_errors', 'Connection error');
        }
      });
    });

    $modalCancelBtn.each(function() {
      $(this).on('click', () => {
        restartPhabAPIToken();
        resetSettingsFormErrors();
        $modal.removeClass('is-active');
      });
    });

    $phabAPITokenReset.on('click', () => {
      setAPITokenPlaceholder();
    });

    function resetSettingsFormErrors() {
      $settingsFormErrors.empty();
    }

    function displaySettingsError(errorSet, message) {
      $modal
        .find('#' + errorSet)
        .first()
        .append('<li class="help is-danger">' + message + '</li>');
    }

    function setAPITokenPlaceholder() {
      if ($phabAPITokenReset.prop('checked')) {
        $phabAPITokenInput.prop('placeholder', 'Save changes to delete the API token');
        $phabAPITokenInput.val('');
        $phabAPITokenInput.prop('disabled', true);
        return;
      }
      $phabAPITokenInput.prop('disabled', false);
      if (!isSetPhabAPIToken) {
        $phabAPITokenInput.prop('placeholder', 'not set');
      } else {
        $phabAPITokenInput.prop('placeholder', 'api-############################');
      }
    }

    function restartPhabAPIToken() {
      $phabAPITokenInput.val('');
      $phabAPITokenReset.prop('checked', false);
      $phabAPITokenInput.prop('disabled', false);
      setAPITokenPlaceholder();
    }

    function handlePhabAPITokenErrors(errors) {
      resetSettingsFormErrors();
      Object.keys(errors).forEach(error => {
        if (error in ['phab_api_token', 'reset_phab_api_token']) {
          errors[error].each(message => {
            displaySettingsError('phab_api_token_errors', message);
          });
          return;
        }
        errors[error].forEach(message => {
          displaySettingsError(error + '_errors', message);
        });
      });
    }

    function settingsFormSubmit() {
      $settingsForm.submit();
    }

    function modalSubmitBtnOn() {
      $modalSubmitBtn.removeClass('is-loading');
      $modalSubmitBtn.on('click', settingsFormSubmit);
    }

    function modalSubmitBtnOff() {
      $modalSubmitBtn.addClass('is-loading');
      $modalSubmitBtn.off('click');
    }
  });
};
