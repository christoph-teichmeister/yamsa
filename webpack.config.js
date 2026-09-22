const path = require("path");
const webpack = require("webpack");
const BundleTracker = require("webpack-bundle-tracker");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");

// Outside apps/ entirely, not just outside apps/static: Tailwind's @source directives watch
// their common ancestor across every app's templates dir, which is apps/ itself. An output
// directory anywhere under apps/ then counts as a content change on every build (clean: true
// rewrites it every time) and reopens the next one - a self-triggering watch loop with no
// source edit involved. Served at the same /static/bundles/ URL via a second STATICFILES_DIRS
// entry (apps/config/settings.py), so nothing downstream of the URL changes.
const bundlesPath = path.resolve(__dirname, "webpack_bundles/bundles");
const staticJsPath = path.resolve(__dirname, "apps/static/js");
// Build-only sources, deliberately outside apps/static: collectstatic runs every .css it
// finds there through the manifest storage, which cannot resolve Tailwind's @import.
const staticSrcPath = path.resolve(__dirname, "apps/static_src");

module.exports = {
  mode: "production",
  entry: {
    d3: path.resolve(staticJsPath, "vendor/d3-entry.js"),
    navigation: path.resolve(staticJsPath, "navigation.js"),
    offline: path.resolve(staticJsPath, "offline.js"),
    "suggested-guests": path.resolve(staticJsPath, "suggested-guests.js"),
    "transaction-create": path.resolve(staticJsPath, "transaction-create.js"),
    sheet: path.resolve(staticJsPath, "sheet.js"),
    dialog: path.resolve(staticJsPath, "dialog.js"),
    "password-visibility": path.resolve(staticJsPath, "password-visibility.js"),
    "hide-on-scroll": path.resolve(staticJsPath, "hide-on-scroll.js"),
    tailwind: path.resolve(staticSrcPath, "tailwind.js"),
    htmx: path.resolve(staticJsPath, "htmx.js"),
  },
  output: {
    // Content-hashed: a rebuild that changes a bundle's content gets a new URL, so a stale
    // browser cache can only ever serve a URL matching what it cached, instead of a fixed
    // name silently serving whatever the last deploy overwrote it with.
    filename: "[name].[contenthash:8].bundle.js",
    path: bundlesPath,
    publicPath: "/static/bundles/",
    clean: true,
  },
  module: {
    rules: [
      {
        test: /\.css$/i,
        use: [
          MiniCssExtractPlugin.loader,
          {
            loader: "css-loader",
            options: {
              sourceMap: false,
            },
          },
          "postcss-loader",
        ],
      },
    ],
  },
  plugins: [
    // The bare module gives webpack a namespace object whose only export is `default`, so
    // idiomorph-ext's `htmx.defineExtension(...)` would call a method that is not there and take
    // the whole htmx entry down with it. Name the export explicitly.
    new webpack.ProvidePlugin({
      htmx: ["htmx.org", "default"],
    }),
    new MiniCssExtractPlugin({
      filename: "[name].[contenthash:8].bundle.css",
    }),
    new BundleTracker({
      path: bundlesPath,
      filename: "webpack-stats.json",
    }),
  ],
  performance: {
    hints: false,
  },
};
