import coreWebVitals from 'eslint-config-next/core-web-vitals';

const eslintConfig = [
  ...coreWebVitals,
  {
    ignores: [
      'node_modules/**',
      '.next/**',
      'public/**',
      'next-env.d.ts',
    ],
  },
  {
    // New React Compiler-era rules shipped with the upgraded eslint-plugin-react-hooks
    // (bundled via eslint-config-next 16). These flag ~40 pre-existing patterns across
    // the codebase; adopting them is a separate refactor, out of scope for this
    // dependency-security upgrade (Next 14->16, ESLint 8->9, React 18->19).
    rules: {
      'react-hooks/set-state-in-effect': 'off',
      'react-hooks/immutability': 'off',
      'react-hooks/static-components': 'off',
    },
  },
];

export default eslintConfig;
