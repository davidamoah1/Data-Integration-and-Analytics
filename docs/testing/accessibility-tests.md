# Accessibility Tests

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Planned  
> **Owner**: QA Lead

---

## Purpose

Accessibility testing checklist and approach.

## Scope

WCAG 2.1 AA compliance testing.

## Audience

QA engineers and frontend developers.

---

> **⚠️ Planned**: Automated accessibility tests are not yet implemented.

## 1. Testing Approach

### Automated

| Tool | Purpose |
|------|---------|
| @axe-core/playwright | E2e accessibility scanning |
| Lighthouse | Accessibility audit |
| eslint-plugin-jsx-a11y | Static analysis |

### Manual

| Test | How |
|------|-----|
| Keyboard navigation | Tab through all pages |
| Screen reader | NVDA (Windows), VoiceOver (Mac) |
| Color contrast | WebAIM contrast checker |
| Zoom | 200% zoom test |

## 2. WCAG 2.1 AA Checklist

- [ ] All interactive elements keyboard accessible
- [ ] Visible focus indicators
- [ ] No keyboard traps
- [ ] Skip to content link
- [ ] Proper heading hierarchy (h1 → h2 → h3)
- [ ] All images have alt text
- [ ] Form fields have labels
- [ ] Error messages are associated with fields
- [ ] Color contrast meets 4.5:1 (normal text)
- [ ] Color contrast meets 3:1 (large text)
- [ ] No information conveyed by color alone
- [ ] Page works at 200% zoom
- [ ] Page works with text resized
- [ ] `prefers-reduced-motion` respected

## 3. Priority Pages

| Page | Priority | Rationale |
|------|----------|-----------|
| Login | High | Entry point |
| Dashboard | High | Main page |
| Settings | High | User configuration |
| Admin | Medium | Admin functions |
| Signup | High | Registration |

## Related Documents

- [../frontend/accessibility.md](../frontend/accessibility.md) — Accessibility implementation
- [strategy.md](strategy.md) — Testing strategy
