# Accessibility

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: UX Designer

---

## Purpose

Document accessibility standards and current implementation.

## Scope

WCAG compliance, keyboard navigation, screen reader support.

## Audience

Frontend developers and UX designers.

---

## 1. Standards

Target: **WCAG 2.1 AA** compliance.

## 2. Current Implementation

| Feature | Status | Notes |
|---------|--------|-------|
| Semantic HTML | ✅ | Proper heading hierarchy, landmarks |
| Keyboard navigation | ✅ | All interactive elements keyboard accessible |
| Focus indicators | ✅ | Tailwind focus rings |
| Alt text | ⚠️ | Images need alt text audit |
| ARIA labels | ⚠️ | Some components lack ARIA attributes |
| Color contrast | ✅ | Tailwind theme meets AA contrast |
| Screen reader | ⚠️ | Not formally tested |
| Skip to content | ❌ | Not implemented |
| Reduced motion | ❌ | Not implemented |

## 3. Areas for Improvement

1. Add skip-to-content link
2. Add `aria-label` to icon-only buttons
3. Add `role` attributes to dynamic content
4. Implement `prefers-reduced-motion` media query
5. Conduct screen reader testing (NVDA, VoiceOver)
6. Add ARIA live regions for dynamic updates
7. Audit all images for alt text
8. Test with keyboard-only navigation

## 4. Testing

> **⚠️ Planned**: Automated accessibility testing with axe-core.

Recommended tools:
- `@axe-core/playwright` for e2e accessibility tests
- Lighthouse accessibility audit
- Manual screen reader testing

## Related Documents

- [design-system.md](design-system.md) — Design system
- [component-library.md](component-library.md) — Component library
- [../testing/accessibility-tests.md](../testing/accessibility-tests.md) — Accessibility testing
