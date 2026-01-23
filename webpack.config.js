const path = require("path");
const BundleTracker = require("webpack-bundle-tracker");

const bundlesPath = path.resolve(__dirname, "apps/static/bundles");
const staticJsPath = path.resolve(__dirname, "apps/static/js");

module.exports = {
  mode: "production",
  entry: {
    d3: path.resolve(staticJsPath, "vendor/d3-entry.js"),
    navigation: path.resolve(staticJsPath, "navigation.js"),
    "suggested-guests": path.resolve(staticJsPath, "suggested-guests.js"),
  },
  output: {
    filename: "[name].bundle.js",
    path: bundlesPath,
    publicPath: "/static/bundles/",
    clean: true,
  },
  plugins: [
    new BundleTracker({
      filename: path.resolve(bundlesPath, "webpack-stats.json"),
    }),
  ],
  performance: {
    hints: false,
  },
};
