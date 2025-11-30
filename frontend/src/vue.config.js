const { defineConfig } = require("@vue/cli-service");
module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    proxy: {
      "/": {
        target: "http://127.0.0.1:4523/m1/7301386-7030215-default",
        changeOrigin: true,
      },
    },
  },
});
