# Lando Test Plan

## Prerequisites

You will need to have the following. They can be reused for every test run.

### Phabricator Familiarity

1. Familiarize yourself with the "Getting Started", "Signing Up", "Creating a
Revision", and "Updating a Revision" sections of the [Phabricator Test Plan][].
This knowledge will help with the Phabricator portions of this Test Plan.


### Two Phabricator Accounts

1. See the "Signing Up" section of the [Phabricator Test Plan][] for how to
create a Phabricator account.
2. Account one should be what you will use to run `arc diff` on your terminal.
3. Account two simply needs to exist so that it can accept or deny reviews requested
by account one. If you have a colleague that can do this for you, feel free to ask them.


### Auth0 Accounts

1. You will need to be able to login through Mozilla Single Sign On (Auth0) with
LDAP credentials that have at least L1 permissions. See the [Mozilla Commit Access Policy][]
for more information.

2. You will also need to be able to login with another account that does NOT have
L1 permissions. Having 2 LDAP accounts may prove tricky, so it may be helpful to
have a colleague that can help test. Or talk to the LDAP team to see if they can
help out.


## Setup

You will need to do this setup initially once when you start this test plan.

### Create a revision.

1. Create a new bug on https://bugzilla-dev.allizom.org/.
2. Run `hg clone https://autolandhg.devsvcdev.mozaws.net/ phabqa`
    - If you have already cloned the repo, run `hg pull` instead.
3. Make some realistic changes in the repo.
    - Change a several lines in a few files.
    - Add a new file(s). Its content can be some sample code from [MDN][].
    - Mix it up at your discretion.
4. `hg add` (if needed) and `hg commit` the changes.
5. Run `arc diff` to create a new revision.
6. Give the revision:
    - A realistic title.
    - A realistic summary.
    - A reviewer (preferably one whose account you can control).
    - The bug number from the bug created above.
7. Visit the revision at https://phabricator-dev.allizom.org/ and confirm
everything looks appropriate according to the "Create a Revision" section of
the [Phabricator Test Plan][].

## Test: Authentication - Not Logged In

**Test Plan**
1. View the revision you created at https://lando.devsvcdev.mozaws.net/revisions/<REVISION_ID>.
    - Change <REVISION_ID> in this URL to the D-prefixed revision number (e.g. D123).

**Result**
1. ![Not Logged In](/screenshots/not-logged-in.png)
    - In the top right corner, confirm that there is a blue button that says
    "Login with Auth0".
    - Near the bottom of the page there is no Land button and a warning message
    is shown informing the user that they aren't logged in.

## Test: Authentication - Logging In

**Test Plan**
1. Click the "Login with Auth0" button.
2. Login with the LDAP account that has L1 permissions.

**Result**
1. You should be taken through the standard Mozilla Single Sign On Login process.
2. Once logged in you should be redirected back to the revision page.
3. ![Logged In](/screenshots/logged-in.png)
    - In the top right corner, your name and picture are present instead of the
    "Login with Auth0" button.
        - You may have to log out if you have run this test plan before.
    - Near the bottom of the page confirm that the Land button is present.

## Test: Authentication - Logging Out

**Test Plan**
1. Click "Logout" in the top right corner.

**Result**
1. Confirm that you successfully logged out and reach the "Signed Out" page.


## Test: Display a Revision - Single Diff

**Test Plan**
1. Double check that you are logged in with the account that has L1 permissions.
2. View the revision you created at https://lando.devsvcdev.mozaws.net/revisions/<REVISION_ID>.
    - Change <REVISION_ID> in this URL to the D-prefixed revision number (e.g. D123).

**Result**
1. ![Revision on Lando](/screenshots/display-revision-normal.png)
    - The page should resemble the above.
2. Confirm that the following pieces of the revision shown are correct:
    - **Revision number and title** (e.g. "D78: Test Revision" in this screenshot).
    - **Timeline**: Not yet landed.
    - **Details**:
        - Diff: Same as the diff number shown on Phabricator as seen here:
            - ![Same diff num](/screenshots/display-revision-same-diff-number.png)
        - Author: Should match the hg commit author name and email as seen by `hg log`.
        - Date: Should match the date you created the commit as seen by `hg log`.
        - Review Status: Should be 'Review Pending' until the reviewer has accepted
          or rejected the revision.
    - **Commit Message**:
        - First Line: Should follow this pattern:
        "\<Bug number\> - \<Revision Title\> r=\<reviewers\>"
        - Toggle Full Commit Message: When clicked should show:
            - The first line
            - The revision summary
            - The revision URL
    - **Land button**: Should be green and display the correct revision number.


## Test: Display a Revision - Multiple Diffs

**Test Plan**
1. In your terminal make some additional file changes.
2. Run `hg commit --amend` and `arc diff` to update the
same revision.

**Result**
1. Confirm that there are now two diffs in the revision's history on Phabricator:
    - ![Multiple diffs](/screenshots/multiple-diffs.png)
2. Take note of the Diff **IDs** (e.g. 115 and 118 in this screenshot).
3. View the revision at https://lando.devsvcdev.mozaws.net/revisions/<REVISION_ID>/<DIFF1>.
    - Change <REVISION_ID> in this URL to the D-prefixed revision number (e.g. D123).
    - Replace <DIFF1> with the first diff number. In the above screenshot, 115.
4. Confirm that the page is loaded in the context of the old diff.
    - ![Multiple diffs old](/screenshots/multiple-diffs-viewing-old.png)
    - The diff number is the old (lowest) one.
    - There is a warning near the bottom that informs the user they are going
      to land an old diff.
    - The land button is disabled.
    - The land button is enabled if you check the checkbox in the warning.
    - The page URL has the old diff id in it (just as it was entered in).
7. Visit https://lando.devsvcdev.mozaws.net/revisions/<REVISION_ID>/<DIFF2>.
    - Replace <DIFF2> with the second diff number. In the above screenshot, 118.
8. Confirm that the the page is loaded in the context of the newest diff.
    - The diff number is the new (highest) one.
    - The land button is enabled.
    - The page URL has the new diff id in it (just as it was entered in).

## Test: Display a Revision - URL loads the most recent diff by default.

**Test Plan**
1. Visit https://lando.devsvcdev.mozaws.net/revisions/<REVISION_ID>/<DIFF2>.
    - Replace <DIFF2> with the second diff number of the revision. E.g., in the
    in the screenshot in "Display a Revision - Multiple Diffs"/Result/1: 118.
2. Then visit https://lando.devsvcdev.mozaws.net/revisions/<REVISION_ID>
    - Do not add any diff in this url.

**Result**
1. Confirm that in both cases the page loads in the context of the latest diff:
    - There should be no warning and the land button should be enabled.
    - Both pages should be equal.
    - Once loaded both pages should have <DIFF2> in the URL.

## Test: Display a Revision - Reviewer accepted older diff

**Test Plan**
1. If you have not already, make sure that your reviewer account has accepted
the revision.
2. In your terminal update the same file you edited to create the revision.
3. `hg commit` those changes.
4. Run `arc diff`.
5. This should post an updated revision to Phabricator.
6. View the revision on Lando - **make sure to remove the old diff id in the URL
so that Lando loads the latest one**. Or you can just click the "View on Lando"
link on Phabricator in the right sidebar.

**Result**
1. ![Accepted Older](/screenshots/accepted-older.png)
    - The reviewer should be marked as having accepted an older version.

## Test: Display a Revision - Project Reviewer

**Test Plan**
1. Visit the revision on Phabricator and in the right sidebar click Edit.
2. In the reviewers box add the `landoqa` project by typing its name. Save the
revision.
3. Your reviewer account should be in the `landoqa` group. If not go to
https://phabricator-dev.allizom.org/project/members/89/ and join the project
on your reviewer account.
4. On your reviewer account visit the revision and at the bottom of the page
choose the Accept action. There will be a little checkbox to accept it as the
landoqa group as shown:
![Accept as Project](/screenshots/accepted-as-project.png)


**Result**
1. On Lando the project is correctly displayed as a reviewer.


## Test: Landing Blockers - Open dependant parent revision.

**Test Plan**
1. Visit the revision you created on phabricator.
2. In the right sidebar click "Edit Parent Revisions".
3. Select a revision that has a status other than "Closed" or "Abandoned". For
example, select a revision that "Needs Review".
4. Click "Save Parent Revisions".

**Result**
1. Visit the revision on Lando.
2. ![Open parents](/screenshots/open-revision.png)
    - Confirm that there is a red "blocking" warning that informs the user that
    there is an open revision and that the land button is not present.

## Test: Landing Blockers - Author Planned Changes

**Test Plan**
1. Visit the revision you created on phabricator.
2. At the bottom of the page in the "Add Actions" dropdown, select "Plan Changes"
and hit Submit.

**Result**
1. Visit the revision on Lando.
2. ![Planned Changes](/screenshots/planned-changes.png)
    - Confirm that there is a red "blocking" warning that informs the user that
    the author of the revision is planning changes.

## Test: Landing Blockers - Lacking permissions.

**Test Plan**
1. View the revision you created on Lando.
2. Login with the LDAP account that does NOT have L1 permissions.

**Result**
1. ![No SCM Level](/screenshots/no-scm-level.png)
    - Confirm that there is a red "blocking" warning that informs the user that
    they do not have L1 permissions.

## Test: Landing Blockers - Invalid Repository

**Test Plan**
1. On Phabricator Edit the Revision.
2. Remove 'test-repo' as the repository. The repository field should be empty.
3. Save the revision.

**Result**
1. View the revision again on Lando.
2. There should be a red blocking message at the bottom saying that no repository
is associated with the revision and so landing is disabled.

## Test: Landing Blockers - Invalid Repository

**Test Plan**
1. On Phabricator Edit the Revision.
2. Remove 'test-repo' as the repository and add 'lando-api'.
3. Save the revision.

**Result**
1. View the revision again on Lando.
2. Since lando-api is not a supported repository that Lando can land to, there
should be a red blocking message at the bottom saying that landing to that
repository is unsupported.
3. After this step make sure to add 'test-repo' as the repository again to
continue with this test plan.

## Test: Landing - Successfully Land a Revision

**Test Plan**
1. Log into Lando with the LDAP account that has L1 permissions.
2. On Phabricator, have the revision's reviewer accept the revision.
3. Visit the revision on lando and Click the Land button.
    - Make sure you do not specify a DIFF_ID so that the page will load
    with the second (most recent) diff.

**Result**
1. There should be no warnings on the page.
    - Make sure you view the revision in the context of the most recent diff.
    - See the "Revision URL loads the most recent diff by default" test for
    help on how.
2. ![Landing Queued](/screenshots/landing-queued.png)
    - Confirm that there is a timeline entry saying that landing is queued.
        - The diff ID is the most recent diff.
        - The diff ID links to the Phabricator revision and shows the correct diff.
        - Time is correct.
            - Known bug: The time is off by 4 hours.
            https://bugzilla.mozilla.org/show_bug.cgi?id=1442003
        - The requester author email matches the email of the LDAP account you
        used to login via Mozilla SSO.
    - If the timing of our backend transplant service is really fast you may
      see the page transition directly to the successful screenshot below.
3. Refresh the page every 2 or so seconds until the landing succeeds.
4. ![Landing Successful](/screenshots/landing-successful.png)
    - Confirm that there is a timeline entry indicating landing is successful.
        - The diff ID is the most recent diff.
        - The diff ID links to the Phabricator revision and shows the correct diff.
        - Time is correct.
            - Known bug: The time is off by 4 hours.
            https://bugzilla.mozilla.org/show_bug.cgi?id=1442003
        - The requester author email matches the email of the LDAP account you
        used to login via Mozilla SSO.
5. Visit https://autolandhg.devsvcdev.mozaws.net/.
    - Confirm that the commit was landed successfully.
    - Confirm that the commit id SHA matches the "Result" in the successful
    landing timeline entry on Lando.


## Test: Landing - Re-Land a Revision

**Test Plan**
1. This test follows the test immediately above (Successfully Land a Revision).
There is no action required.
2. Do not click the Re-Land button.

**Result**
1. Confirm that there is a warning on the page indicating that the revision
has been landed.
2. Confirm that checking the warning enables the Re-land button.

## Test: Landing Errors - Diff will not apply cleanly.

**Test Plan**
1. In the hg repo add a new file with 3 lines of text: `vi my-bad-file`.
2. `hg add` and `hg commit` the new file.
3. Modify the file and change something on line 2. `hg commit` the changes.
4. Run `arc diff .^`. This will create a new revision with only the changes
that modified the file. The intent is to create a bad revision which is impossible
to land (since the changes in the first commit that added the file are missing).
5. Accept the revision with your reviewer account.
6. Visit the revision on Lando.
7. Land the revision.
8. Refresh the page every 2 seconds or so until the page updates.

**Result**
1. ![Landing Failed](/screenshots/landing-failed.png)
    - There should be an error message in the timeline indicating that the
    landing failed.




[Phabricator Test Plan]: https://wiki.mozilla.org/Phabricator/TestPlan
[Mozilla Commit Access Policy]: https://www.mozilla.org/en-US/about/governance/policies/commit/access-policy/
[MDN]: https://developer.mozilla.org/en-US/
