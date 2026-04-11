const path = require("path");
const webpack = require("webpack");
const BundleTracker = require("webpack-bundle-tracker");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");

const bundlesPath = path.resolve(__dirname, "apps/static/bundles");
const staticJsPath = path.resolve(__dirname, "apps/static/js");

module.exports = {
  mode: "production",
  entry: {
    d3: path.resolve(staticJsPath, "vendor/d3-entry.js"),
    navigation: path.resolve(staticJsPath, "navigation.js"),
    "suggested-guests": path.resolve(staticJsPath, "suggested-guests.js"),
    styles: path.resolve(staticJsPath, "styles.js"),
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
        ],
      },
      {
        test: /\.(woff2?|eot|ttf|otf|svg)(\?.*)?$/i,
        type: "asset/resource",
        generator: {
          filename: "fonts/[name][ext]",
        },
      },
    ],
  },
  plugins: [
    new webpack.ProvidePlugin({
      htmx: "htmx.org",
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
