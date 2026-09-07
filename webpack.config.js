const path = require("path");
const webpack = require("webpack");
const BundleTracker = require("webpack-bundle-tracker");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");

const bundlesPath = path.resolve(__dirname, "apps/static/bundles");
const staticJsPath = path.resolve(__dirname, "apps/static/js");
// Build-only sources, deliberately outside apps/static: collectstatic runs every .css it
// finds there through the manifest storage, which cannot resolve Tailwind's @import.
const staticSrcPath = path.resolve(__dirname, "apps/static_src");

module.exports = {
  mode: "production",
  entry: {
    d3: path.resolve(staticJsPath, "vendor/d3-entry.js"),
    navigation: path.resolve(staticJsPath, "navigation.js"),
    "suggested-guests": path.resolve(staticJsPath, "suggested-guests.js"),
    "category-suggestion": path.resolve(staticJsPath, "category-suggestion.js"),
    sheet: path.resolve(staticJsPath, "sheet.js"),
    dialog: path.resolve(staticJsPath, "dialog.js"),
    "password-visibility": path.resolve(staticJsPath, "password-visibility.js"),
    tailwind: path.resolve(staticSrcPath, "tailwind.js"),
    htmx: path.resolve(staticJsPath, "htmx.js"),
  },
  output: {
    filename: "[name].bundle.js",
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
      filename: "[name].bundle.css",
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
