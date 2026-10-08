import js from '@eslint/js'
import prettier from 'eslint-config-prettier'
import pluginVue from 'eslint-plugin-vue'
import globals from 'globals'
import tseslint from 'typescript-eslint'

export default tseslint.config(
  {
    ignores: ['.nuxt/**', '.output/**', 'node_modules/**', 'coverage/**'],
  },
  js.configs.recommended,
  {
    files: ['**/*.ts', '**/*.mts'],
    extends: [tseslint.configs.recommended],
    rules: {
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
      ],
    },
  },
  ...pluginVue.configs['flat/essential'],
  {
    files: ['**/*.vue'],
    languageOptions: {
      parserOptions: { parser: tseslint.parser },
    },
    plugins: { '@typescript-eslint': tseslint.plugin },
    rules: {
      // Nuxt auto-imports; TypeScript reports undefined identifiers instead.
      'no-undef': 'off',
      'no-unused-vars': 'off',
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
      ],
    },
  },
  {
    languageOptions: {
      globals: { ...globals.browser, ...globals.node },
    },
  },
  {
    files: ['**/*.ts', '**/*.mts'],
    rules: {
      // Nuxt auto-imports; TypeScript reports undefined identifiers instead.
      'no-undef': 'off',
    },
  },
  {
    files: ['app/pages/**/*.vue'],
    rules: {
      // Nuxt page filenames (index.vue, [id].vue) are routes, not components.
      'vue/multi-word-component-names': 'off',
    },
  },
  prettier,
)
