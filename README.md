# Deno Magic Command

This fork simplifies the magic command; instead of `%%run_deno`, we change it to `%%d`.
And also translate all Japanese to English.

## Overview

This is a magic command to write and execute Deno (JavaScript/TypeScript) code in code cells in Jupyter (notebook/lab) or Google Colab.

## Usage

### Installation

In Jupyter environments, you need to install Deno in advance and add it to your PATH. For installation methods, please refer to [Deno's official website](https://deno.com/). If you're using Jupyter (extension) via VSCode, additionally install the Deno extension and set `Deno.enable` to true in the settings.

In the Google Colab environment, there's an installation function provided in the package, so you don't need to install it separately.

### Adding the Magic Command

Paste the following code into a code cell and execute it to register the magic command. You need to re-run it each time you restart the kernel or runtime.

```python
%pip install denomagics
import denomagics
```

# Install Deno (for Google Colab; calling this in other environments won't install Deno)

```python
denomagics.install_deno_colab()
# Register the magic command
denomagics.register_deno_magics()
```

### How to Use the Magic Command

At the beginning of a code cell, write the magic command as follows. When executed, the JavaScript/TypeScript code in the code cell will be run by Deno.

```javascript
%%d

console.log("Hello, world!");
```

or with old syntax

```javascript
%%run_deno

console.log("Hello, world!");
```

We also provide a magic command that transpiles the JavaScript/TypeScript code in the code cell using Deno and runs it inside an iframe.

Below is an example using p5.js, a library for browsers.

```javascript
%%run_deno_iframe 830 430
import "https://cdn.jsdelivr.net/npm/p5@1.9.4/lib/p5.js";

const sketch = (p: any) => {
  let x = 0;
  let y = 0;
  let speed = 2;
  let color: [number, number, number] = [0, 0, 0];

  p.setup = () => {
    p.createCanvas(800, 400);
    x = p.width / 2;
    y = p.height / 2;
  };

  p.draw = () => {
    p.background(220);
    p.fill(color);
    p.ellipse(x, y, 50, 50);
    if (p.keyIsDown(p.LEFT_ARROW) === true) {
      x -= speed;
    }

    if (p.keyIsDown(p.RIGHT_ARROW) === true) {
      x += speed;
    }

    if (p.keyIsDown(p.UP_ARROW) === true) {
      y -= speed;
    }

    if (p.keyIsDown(p.DOWN_ARROW) === true) {
      y += speed;
    }
  };

  p.mousePressed = () => {
    color = [p.random(255), p.random(255), p.random(255)];
  };
};

new p5(sketch);
```

### Magic Command

#### %%d

```jupyter
%%run_deno [userval]
```

Executes the JavaScript/TypeScript code in the code cell using Deno.

- **userval**: Specifies whether to use Jupyter user variables in Deno. The default is `False`.

When `userval` is set to `True`, you can access Jupyter's user variables through `globalThis.jupyter`, allowing variable exchange across cells.  
Internally, data is exchanged between Jupyter and Deno using a temporary JSON file, so objects that cannot be converted to JSON cannot be used.  
Behavior is undefined if such objects are used.

If the code is being executed within a Jupyter code cell, `globalThis.isJupyterCell` is defined. By checking whether this is not `undefined`, you can determine if the code is being executed from a Jupyter code cell.

If you want to terminate the execution in the middle of a code cell while using Jupyter user variables, use `jupyterExit()` instead of `Deno.exit`. If you exit with `Deno.exit`, Jupyter's user variables will not be updated.

#### %%run_deno_iframe

Transpiles the JavaScript/TypeScript in the code cell using Deno and runs it inside an iframe.

```jupyter
%%run_deno_iframe [width] [height] [srcs]
```

- **width**: Specifies the width of the iframe. The default is 500.
- **height**: Specifies the height of the iframe. The default is 500.
- **srcs**: Specifies the URLs of external JavaScript files. If specifying multiple URLs, separate them with spaces.

#### %%run_deno_bundle_iframe

Transpiles and bundles the JavaScript/TypeScript in the code cell, including the imported code, and runs it inside an iframe.

The arguments are the same as `%%denoiframe`.

### %%view_deno_iframe

Outputs the HTML generated after transpiling the JavaScript/TypeScript in the code cell using Deno.

The arguments are the same as `%%run_deno_iframe`.

#### %%view_deno_bundle_iframe

Outputs the HTML generated after transpiling and bundling the JavaScript/TypeScript in the code cell, including the imported code.

The arguments are the same as `%%run_deno_iframe`.
