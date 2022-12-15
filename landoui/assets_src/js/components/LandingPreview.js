/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */

'use strict';

$.fn.landingPreview = function() {
  return this.each(function() {
    let $landingPreview = $(this);
    let $form = $('.StackPage-form');
    let $close = $landingPreview.find('.StackPage-landingPreview-close');
    let $warnings = $landingPreview.find('.StackPage-landingPreview-warnings input[type=checkbox]');
    let $blocker = $landingPreview.find('.StackPage-landingPreview-blocker');
    let $landButton = $landingPreview.find('.StackPage-landingPreview-land');
    let $revisions = $landingPreview.find('.StackPage-landingPreview-revision');
    let $expandAllButton = $landingPreview.find('.StackPage-landingPreview-expandAll');
    let $collapseAllButton = $landingPreview.find('.StackPage-landingPreview-collapseAll');

    // Reach outside my component, because I'm a pragmatist.
    let $previewButton = $('.StackPage-preview-button');



    // Form currently resides in the footer in its own component, so we
    // need to listen to changes on flags outside of the form and update
    // form field accordingly. TODO: make this better.
    document.querySelectorAll('.flag-checkbox').forEach(item => {
        item.addEventListener('change', event => {
            let flags = [];
            document.querySelectorAll('.flag-checkbox:checked').forEach(flag => {
                flags.push(flag.value);
            });
            $form.find("[name=flags]").val(JSON.stringify(flags));
        });
    });


    let calculateLandButtonState = () => {
      if($blocker.length > 0) {
        $landButton.attr({'disabled': true});
        $landButton.text('Landing is blocked');
        return;
      }

      let checked = $warnings.filter(function() {
        return this.checked;
      });
      if(checked.length !== $warnings.length) {
        $landButton.attr({'disabled': true});
        $landButton.text('Acknowledge warnings to land');
      } else {
        $landButton.attr({'disabled': false});
        $landButton.text('Land to ' + $landButton.data('target-repo'));
      }
    };


    $form.on('submit', () => {
      $landButton.attr({'disabled': true});
      $landButton.text('Landing in progress...');
    });

    let expandCommitMessage = ($commitMessage, $seeMore, $toggleButton, lines) => {
      $commitMessage.css('max-height', 'none');
      $commitMessage.data('expanded', true);
      $toggleButton.text('Hide lines');
      $seeMore.css('display', 'none');
    };

    let collapseCommitMessage = ($commitMessage, $seeMore, $toggleButton, lines) => {
      $commitMessage.css('max-height', '');
      $commitMessage.data('expanded', false);
      $toggleButton.text('Show all ' + lines + ' lines');
      $seeMore.css('display', 'block');
    };

    let toggleCommitMessage = ($commitMessage, $seeMore, $toggleButton, lines) => {
      if($commitMessage.data('expanded')) {
        collapseCommitMessage($commitMessage, $seeMore, $toggleButton, lines);
      } else {
        expandCommitMessage($commitMessage, $seeMore, $toggleButton, lines);
      }
    };

    let swapDisplayEditPanels = ($displayMessagePanel, $editMessagePanel) => {
      if($editMessagePanel.data('expanded')) {
        $displayMessagePanel.show();
        $editMessagePanel.hide();
        $editMessagePanel.data('expanded', false);
      } else {
        $displayMessagePanel.hide();
        $editMessagePanel.show();
        $editMessagePanel.data('expanded', true);
      }
    };

    let submitSecApprovalForm = ($form, $error_list) => {
        const data = new FormData($form[0]);

        fetch('/request-sec-approval', {
          method: 'POST',
          headers: {'Accept': 'application/json'},
          body: data,
        })
          .then(response => {
            if (response.ok || response.status === 400 || response.status === 401) {
              // The submission succeeded or failed with a validation error.
              return response.json();
            } else {
              // The submission failed with a network or server error.
              return Promise.reject(
                new Error("Bad response for form submission: " + response.status)
              );
            }
          })
          .then(json => {
            const errors = json.errors;

            if (errors) {
              // We got a form submission validation error.
              console.info("sec-approval form submission failed");

              // Overwrite the list of form errors.
              $error_list.empty();
              // The data structure with form errors is:
              //  {
              //    field_1: [error_msg_1, error_msg_2, ...],
              //    field_2: [error_msg_1, error_msg_2, ...],
              //    ...
              //  }
              Object.keys(errors).forEach(field => {
                errors[field].forEach(error => {
                  $('<li>', {
                    text: error
                  }).appendTo($error_list);
                });
              });

              $error_list.show();

            } else {
              // Submission was OK, reload the page and show the "Success" dialog.
              console.info("sec-approval form submission succeeded");
              let url = new URL(document.URL);
              url.searchParams.set('show_approval_success', data.get('revision_id'));
              document.location.assign(url.toString());
            }
          })
          .catch(err => { console.error(err) });
    };


    let longMessages = 0;

    $revisions.each(function () {
      let $revision = $(this);

      // Message display
      let $displayMsgPanel = $revision.find('.StackPage-landingPreview-displayMessagePanel');
      let $toggleButton = $revision.find('.StackPage-landingPreview-expand');
      let $commitMessage = $revision.find('.StackPage-landingPreview-commitMessage');
      let $seeMore = $revision.find('.StackPage-landingPreview-seeMore');
      let lines = $commitMessage.text().split(/\r\n|\r|\n/).length;

      // Message editing
      let $editMessageBtn = $revision.find('.StackPage-landingPreview-editMessage');
      let $editMsgPanel = $revision.find('.StackPage-landingPreview-editMessagePanel');
      let $editMsgForm = $revision.find('form');
      let $editMsgFormErrorsList = $editMsgForm.find('.StackPage-landingPreview-editMessagePanel-formErrors')

      ///////////////////////////
      //
      // Message display routines
      //
      ///////////////////////////

      if (lines <= 5){
        $toggleButton.hide();
      } else {
        // Handle long commit messages.

        longMessages++;

        // Sets up the display of how many lines are hidden:
        // expandCommitMessage and collapseCommitMessage merely toggle this when clicked.
        $toggleButton.text('Show all ' + lines + ' lines');
        $seeMore.text('... (' + (lines - 5) + ' more lines)');

        $toggleButton.on('click', (e) => {
          e.preventDefault();
          toggleCommitMessage($commitMessage, $seeMore, $toggleButton, lines);
        });

        $expandAllButton.on('click', (e) => {
          e.preventDefault();
          expandCommitMessage($commitMessage, $seeMore, $toggleButton, lines);
        });

        $collapseAllButton.on('click', (e) => {
          e.preventDefault();
          collapseCommitMessage($commitMessage, $seeMore, $toggleButton, lines)
        });
      }

      ///////////////////////////
      //
      // Message editing routines
      //
      ///////////////////////////

      $editMessageBtn.on('click', (e) => {
        e.preventDefault();
        $editMessageBtn.attr({'disabled': true});
        swapDisplayEditPanels($displayMsgPanel, $editMsgPanel);
      });

      $editMsgForm.on('submit', (e) => {
        e.preventDefault();
        submitSecApprovalForm($editMsgForm, $editMsgFormErrorsList);
      });

      $editMsgForm.on('reset', (e) => {
        e.preventDefault();
        $editMessageBtn.attr({'disabled': false});
        swapDisplayEditPanels($displayMsgPanel, $editMsgPanel);
      });
    });

    if ($revisions.length === 1 || longMessages === 0) {
      $expandAllButton.css('display', 'none');
      $collapseAllButton.css('display', 'none');
    }

    $previewButton.on('click', (e) => {
      e.preventDefault();
      calculateLandButtonState();
      $landingPreview.css("display", "flex");
    });
    $close.on('click', (e) => {
      e.preventDefault();
      $landingPreview.css("display", "none");
    });
    $warnings.on('change', () => {
      calculateLandButtonState();
    });
  });
};
