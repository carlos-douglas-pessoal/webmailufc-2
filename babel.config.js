const { kebabCase } = require("lodash");

module.exports = {
    sourceMaps: "inline",
    presets: [ "@babel/preset-env" ],
    "plugins": [
        [
            "transform-import-css",
            {
              "generateScopedName": "[local]"
            }
        ],
        [
            "babel-plugin-transform-imports",
            {
              "maz-ui": {
                "transform": (importName, matches) => `maz-ui/lib/${require('lodash').kebabCase((importName))}`,
                "preventFullImport": true
              },
              "buefy": {
                "transform": "buefy/dist/components/${member}",
                "preventFullImport": true
              },
              "vue_": {
                  "transform": ""
              }
            }
        ],
        [
            "module-resolver",{
                "alias":{
                    "myvue": "vue/dist/vue.common.js",
                    "select2": "select2/dist/js/select2.js",
                    "jquery": "select2/src/js/jquery.select2.js"
                }
            }
        ]
    ]
}

// [
//     "babel-plugin-import",
//     {
//       "libraryName": "maz-ui",
//       "styleLibraryName": "~node_modules/maz-ui/lib/css",
//       "ext": ".css"
//     },
//     "input-phone"
//   ],
//   [
//     "babel-plugin-import",
//     {
//       "libraryName": "buefy",
//       "libraryDirectory": "dist/components"
//     },
//     "buefy"
//   ]