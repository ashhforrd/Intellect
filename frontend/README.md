# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some Oxlint rules.

## Styling

- Put one-off layout and appearance in Tailwind `className` attributes on the element being styled. Use React's `style` prop for values calculated at runtime.
- Extract repeated UI into components in [`src/components/`](src/components/), keeping their styles with the component.
- Keep theme tokens, base rules, shared CSS patterns, and styles for generated Markdown or React Flow markup in [`src/globals.css`](src/globals.css). Scope shared rules to their component classes.
- Avoid a separate registry of class strings or custom utility aliases for single-use CSS declarations.

Run `npm run lint` and `npm run build` from this directory after frontend changes. In Windows PowerShell, use `npm.cmd` if script execution policy blocks `npm.ps1`.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the Oxlint configuration

If you are developing a production application, we recommend enabling type-aware lint rules by installing `oxlint-tsgolint` and editing `.oxlintrc.json`:

```json
{
  "$schema": "./node_modules/oxlint/configuration_schema.json",
  "plugins": ["react", "typescript", "oxc"],
  "options": {
    "typeAware": true
  },
  "rules": {
    "react/rules-of-hooks": "error",
    "react/only-export-components": ["warn", { "allowConstantExport": true }]
  }
}
```

See the [Oxlint rules documentation](https://oxc.rs/docs/guide/usage/linter/rules) for the full list of rules and categories.
