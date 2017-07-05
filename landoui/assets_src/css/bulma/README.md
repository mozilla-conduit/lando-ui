### Bulma (Version: 0.4.2)

See [https://github.com/jgthms/bulma](https://github.com/jgthms/bulma).
This is a vendored subset of bulma used for compiling our custom version of it
using the customization variables it provides. Its License has been included in
REDISTRIBUTED_LICENSES in the root of the lando-ui project.

### How to upgrade

1. Clone the original Bulma project in an external directory outside of the project.
2. Copy the `bulma.sass` file and the `sass` folder into this folder, replacing
any existing file.
3. One customization made directly in the Bulma sass files is in `sass/elements/
tag.sass` lines 24 - 27 for the outline style. You should re add that or consider
removing its usages.
4. Update the version number at the top of this README.md file to match the version
which you cloned.

### How to customize
Follow the instructions at http://bulma.io/documentation/overview/customize/ or
simply set the initial-variables that bulma provides in the `assets_src/css/lando.scss` file.
