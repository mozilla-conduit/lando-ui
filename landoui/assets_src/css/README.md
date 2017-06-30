# Lando UI Design Guide

This is an extremely brief guide to get a new developer familiar with the way
the project is styled. It is not meant to be a rulebook or the law, feel free to
change the project as necessary and update this guide if you feel there is a
better way to do something.


# SCSS

All styles in the Lando project should preferably be in the SCSS syntax.
SCSS is 100% compatible with normal CSS so you may not even tell the difference.
It has been included in the project mainly so that we can customize Bulma
and so that we can take advantage of nested styles and variables. Feel free to
use the more advanced features if you so choose.


# Bulma

Lando UI uses the [Bulma CSS Framework](http://bulma.io/)
as a way to provide some excellent defaults and style helpers (e.g. grids,
modals, forms, etc).


# SUIT CSS, Naming, Components

While Lando UI is meant to be a very simple application, who knows how it will
grow or who will work on it. To keep a modular design styles should follow [SUIT
CSS](https://github.com/suitcss/suit/blob/master/doc/naming-conventions.md)
naming conventions. It is not the best out there, but, it is simple and it works.
Here is an example, we have a widget and we want to style it:

### *Not* Preferred Method:
```html
<div>
  <div class="left-title large"><h1>Hi!</h1></div>
  <div class="main-content">
    <p class="controls active">...</p>
    ...
  </div>
  <div class="right-title"><button>Click me</button></div>
</div>
```

You can infer the css.

### Preferred Method:
```html
<div class="Widget">
  <div class="Widget-left Widget-left--large"><h1>Hi!</h1></div>
  <div class="Widget-main">
    <p class="Widget-controls is-active">...</p>
    ...
  </div>
  <div class="Widget-right"><button>Click me</button></div>
</div>
```

```scss
/* Inside the Widget.scss file */
.Widget { ... }
.Widget-left { float: left; }
.Widget-left--large { font-size: 3em; }
.Widget-main { ... }
.Widget-controls { display: none; }
.Widget-controls.is-active { display: block; }
.Widget-right { ... }
```

The downside of this approach is that html elements may have very long class
attributes (e.g. "Widget-left Widget-left--large Widget-left--blue"), the upside
is that that is fairly rare and doing things this way will make finding that
pesky class that is overriding your styles extremely easy (or avoid the problem
altogether).

With that in mind, all pages and partials (e.g. basically anything with a file
in the flask templates folder) should be a scoped in a css component.
"Pages" are special components that belong to a whole page which corresponds to
one of the templates that is not in the partials folder, these should ideally be
suffixed with "Page" e.g. "RevisionPage".

SUIT CSS should all be camelCase, with components starting with an uppercase
letter.

If a css class is not prefixed with a component name, an "is-" (denoting a SUIT
CSS state), or a "u-" (denoting a SUIT CSS utility class). Then it is assumed to
be a css class from the Bulma framework or another global class.

If possible prefer classes like .MyPage over id's like #MyPage for defining
styles. That way we won't run into weird specificity issues.


# Colors and Fonts

For simplicity Lando UI follows the [Firefox Photon Color Pallete](http://design.firefox.com/photon/visual/color.html) to the letter.
The only addition is our main color of orange (to be finalized, please give opinion).
Currently it is:
```
F76600 - Darker Orange
FF7700 - Main Orange (same as Lando logo)
FFA000 - Lighter Orange
FFB330 - Lightest Orange
```

Our primary font is also based on the Firefox Photon Design:
It is [Fira Sans](https://github.com/mozilla/Fira) made by Mozilla :D. It is
vendored in via our cdn at https://code.cdn.mozilla.net/fonts/fira.css. If it
doesn't load, then it will just use the browser default so no biggie.

Our customization of Bulma has been configured to default to these colors
and the Fira font.


# Logo

In the `static/images` folder you will find many logos to use. They have been
resized at 1024px, 512px, 256px, 128px, and some at 64px.

The logo with the text's aspect ratio is 2.65625, it comes with both black and
white text. See the `static/src/log` folder for the src files.
Israel, imadueme@mozilla.com, created them :D


# Icons

Font awesome 4.7.0 is included, so feel free to use any of those fonts listed
[here](http://fontawesome.io/icons/). Make sure those docs are for 4.7 not 5.
