const { configure } = require('quasar/wrappers');

module.exports = configure(function (ctx) {
  return {
    eslint: {
      fix: true,
      warnings: true,
      errors: true
    },

    boot: [],

    css: ['app.scss'],

    extras: [
      'roboto-font',
      'material-icons',
      'material-icons-outlined',
    ],

    build: {
      vitePlugins: [],

      env: {
        API_URL: ''  // Empty string means same origin
      },

      extendViteConf(viteConf) {
        viteConf.server = {
          ...viteConf.server,
          proxy: {
            '/api': {
              target: 'http://localhost:8000',
              changeOrigin: true
            }
          }
        };
      }
    },

    devServer: {
      open: true
    },

    framework: {
      config: {},
      plugins: [
        'Notify'
      ]
    },

    animations: [],

    ssr: {
      pwa: true
    },

    pwa: {
      extendPwaConf(pwaConf) {
        pwaConf.workbox = {
          ...pwaConf.workbox,
          navigateFallback: '/index.html',
          navigateFallbackDenylist: [/sw\.js$/, /workbox-.+\.js$/]
        };

        // Ensure manifest is injected
        pwaConf.injectPwaMetaTags = true
        pwaConf.manifestFilename = 'manifest.json'
      }
    },

    cordova: {},


    capacitor: {},


    bin: {
      linuxAndroidStudio: ''
    }
  };
});
